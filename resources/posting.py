from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_restful import Resource
from config import Config
from mysql_connection import get_connection
from mysql.connector import Error
import boto3
from datetime import datetime
from resources.rekognition import ObjectDetectionResource

class PostingResource(Resource):
    @jwt_required()
    def post(self):
        
        # 1. 클라이언트로부터 데이터를 받아온다.
        file = request.files.get('photo')
        context = request.form.get('content')
        user_id = get_jwt_identity()

        # 2. 사진을 s3에 저장한다.
        if file is None :
            return {'error' : '파일을 업로드 하세요'}, 400


        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':','_') + '.jpg'
    
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
        

        label_list = ObjectDetectionResource.detect_labels(self,new_file_name, Config.S3_BUCKET)
        print(label_list)
        label_list = ','.join(label_list)


        # 3. DB에 저장한다.

        try:
            connection = get_connection()
            query = ''' insert into posting
                        (userId,imgUrl,content,tagging)
                        values
                        (%s,%s, %s,%s); '''


            imgUrl = Config.S3_LOCATION + file.filename
    
            record = ( user_id, imgUrl , context,label_list )

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
    

class PostingListResource(Resource):
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
                        set content = %s,tagging = %s
                        where id = %s and userId = %s;'''
            
            record = (data['content'], data['tagging'],
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
