# flask 프레임워크를 이용한 ,  Restful API 서버 개발

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_restful import Api
from config import Config
from resources.follow import FollowResource
from resources.like import LikeResource
from resources.posting import PostingListResource, PostingResource


#  로그 아웃 관련된 임포트문. 
from resources.user import UserLoginResource, UserLogoutResource, UserRegisterResource, jwt_blocklist


app = Flask(__name__)

api = Api(app)

# 환경변수 셋팅

app.config.from_object(Config)
# JWT 매니저를 초기화
jwt = JWTManager(app) 

# 로그 아웃 된 토큰으로 요청하는 경우,
# 실행되지 않도록 처리하는 코드.
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header,jwt_payload):
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

# API를 구분해서 실행시키는 것은,
# HTTP METHOD 와 URL의 조합 이다.

# 경로(path)와 리소스(API 코드) 를 연결한다. 

api.add_resource( UserRegisterResource ,'/user/register')
api.add_resource( UserLoginResource,'/user/login')
api.add_resource( UserLogoutResource ,'/user/logout')

api.add_resource( PostingListResource,'/posting') #포스팅 작성 , 팔로워한 포스팅 보기 
api.add_resource( PostingResource ,'/posting/<int:posting_id>') # 포스팅 삭제 , 수정 ,상세보기

api.add_resource( FollowResource , '/follow/<int:followee_id>') #친구 추가, 삭제 
api.add_resource( LikeResource , '/like/<int:posting_id>') # 좋아요 ,좋아요 취소 

if __name__ == '__main__':
    app.run()




