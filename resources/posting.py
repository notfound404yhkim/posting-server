from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error
import boto3
from datetime import datetime


class PostingListResource(Resource):


    def detect_labels(self, photo, bucket):

        client = boto3.client('rekognition',
                              'ap-northeast-2',
                              aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                              aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY)

        response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},
        MaxLabels=5,
        # Uncomment to use image properties and filtration settings
        #Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
        #Settings={"GeneralLabels": {"LabelInclusionFilters":["Cat"]},
        # "ImageProperties": {"MaxDominantColors":10}} 
        )

        print('Detected labels for ' + photo)
        print()

        label_list = [] 
        for label in response['Labels']:
            print("Label: " + label['Name']) 
            print("Confidence: " + str(label['Confidence']))
            if label['Confidence'] >= 90: #Confidence 가 90 이상인것만 출력하도록 .
                label_list.append(label['Name'])
            

        return label_list



    @jwt_required()
    def post(self):
        
        # 1. 클라이언트로부터 데이터를 받아온다.
        file = request.files.get('image')
        context = request.form.get('content')
        user_id = get_jwt_identity()

        # 2. 사진을 s3에 저장한다.
        if file is None :
            return {'error' : '파일을 업로드 하세요'}, 400


        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':','_') + str(user_id) + '.jpg'
    
        file.filename = new_file_name

        s3 = boto3.client('s3',
                     aws_access_key_id = Config.AWS_ACCESS_KEY_ID,
                     aws_secret_access_key = Config.AWS_SECRET_ACCESS_KEY)
        try : 
            s3.upload_fileobj(file, 
                              Config.S3_BUCKET,
                              file.filename, 
                              ExtraArgs = {'ACL' : 'public-read', 
                                           'ContentType' : 'image/jpeg'})
            

        except Exception as e :
            print(e)
            return{'error':str(e)}, 500
        

        # rekogintion 서비스를 이용하여
        # object detection 하여, 태그 이름을 가져온다.
        

        tag_list = self.detect_labels(new_file_name, Config.S3_BUCKET)
        print(tag_list)
        
        for i in tag_list:
            try:
                connection = get_connection()
                query = ''' insert into tag_name
                            (name)
                            values
                            (%s); '''

                imgUrl = Config.S3_LOCATION + file.filename
                record = ( i, )

                cursor = connection.cursor()
                cursor.execute(query,record)

                connection.commit()

                cursor.close()
                connection.close()
    
            except Error as e:
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)},500
            

        # DB의 posting 테이블에 데이터를 넣어야함.
        # tag_name 테이블 과 tag 테이블에도 데이터를 넣어줘야 한다 


        # 3. DB에 저장한다.

        try:
            connection = get_connection()
            query = ''' insert into posting
                        (userId,imgUrl,content)
                        values
                        (%s,%s, %s); '''


            imgUrl = Config.S3_LOCATION + file.filename
    
            record = ( user_id, imgUrl , context )

            cursor = connection.cursor()
            cursor.execute(query,record)

            connection.commit()

            cursor.close()
            connection.close()
    
        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)},500

        return {'result' : 'success',
                'imgUrl' : imgUrl },200
    
    @jwt_required()
    def get(self):
        
        user_id = get_jwt_identity()
        print(1)

        # 쿼리 스트링 가져오기 (쿼리 파라미터)
        # get에서는 쿼리 파라미터를 이용해 데이터를 가져옴
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        
        print(offset)
        print(limit)
      
        try:
            connection = get_connection()
            query = '''select *
                        from posting
                        where userId = %s
                        order by createdAt
                        limit '''+ str(offset) +''', '''+ str(limit) +'''    ;'''
            
            record = (user_id ,)

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query,record)
          
            result_list = cursor.fetchall()  

            print(result_list)

            # date time 은 파이썬에서 사용하는 데이터 타입이므로
            # JSON 형식이 아니다. 따라서,
            # JSOON은 문자열이나 숫자만 가능하므로
            # datetime을 문자열로 바꿔주어야 한다. 

            cursor.close()
            connection.close()


        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return{"Error" : str(e)},500
        
        i = 0
        for row in result_list:
            result_list[i]['createdAt'] = row['createdAt'].isoformat()
            result_list[i]['updateAt'] = row['updateAt'].isoformat()
            i = i+1

        return {"result " : "success",
            "items" : result_list,
            "count " : len(result_list)},200
    

class PostingResource(Resource):
    @jwt_required()
    def delete(self,posting_id):
        user_id = get_jwt_identity()
        try:
            connection = get_connection()
            query = ''' delete from posting
                        where id =%s and userId =%s;'''
            
            record = (posting_id, user_id)
            
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return{"Error" : str(e)},500

        return{"Result" : "success"},200 
    
    @jwt_required()
    def put(self,posting_id):
        data = request.get_json()
        user_id = get_jwt_identity()
        print(user_id)
        print(posting_id)
        
        try:
            connection = get_connection()
            query = ''' update posting
                        set content = %s,
                        where id = %s and userId = %s;'''
            
            record = (data['content'],
                      posting_id,user_id)
            
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return{"Error" : str(e)},500

        return{"Result" : "success"},200 
