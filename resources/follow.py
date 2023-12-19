from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required #요청 받기
from flask_restful import Resource
from mysql_connection import get_connection
from mysql.connector import Error


# 팔로워 팔로위 관련
class FollowResource(Resource):
    # 친구추가 
    @jwt_required()
    def post(self,followee_id):
        user_id = get_jwt_identity()
        print(followee_id)

        try:
            connection = get_connection()
            query = '''insert into follow
                        (followerId,followeeId)
                        values
                        (%s,%s);'''
            
            record = (user_id,followee_id)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return{"ERROR" : str(e)},500
        
        return{"Result " : "Success" },200
    
    @jwt_required()
    def delete(self,followee_id):
        user_id = get_jwt_identity()
        print(followee_id)

        try:
            connection = get_connection()
            query = '''delete from follow
                       where followerId =%s and followeeId =%s;'''
            
            record = (user_id,followee_id)
            cursor = connection.cursor()
            cursor.execute(query,record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return{"ERROR" : str(e)},500
        
        return{"Result " : "Success" },200
    




    


