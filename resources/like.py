from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required #요청 받기
from flask_restful import Resource
from mysql_connection import get_connection
from mysql.connector import Error


# 좋아요, 관련 
class likeResource(Resource):
    # 추가 
    @jwt_required()
    def post(self,like_id):
        user_id = get_jwt_identity()
        print(like_id)

        try:
            connection = get_connection()
            query = '''insert into likes
                        (userId, postingId)
                        values
                        (%s,%s);'''
            
            record = (user_id,like_id)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(Error)
            cursor.close()
            connection.close()
            return{"ERROR" : str(e)},500
        
        return{"Result " : "Success" },200
        
    @jwt_required()
    def delete(self,like_id):
        user_id = get_jwt_identity()
        print(like_id)

        try:
            connection = get_connection()
            query = '''delete from likes
                       where userId = %s and postingId = %s;'''
            
            record = (user_id,like_id)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(Error)
            cursor.close()
            connection.close()
            return{"ERROR" : str(e)},500
        
        return{"Result " : "Success" },200
    