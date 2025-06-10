from flask import request
from flask_restx import Namespace, Resource, fields
import jwt
import datetime
from functools import wraps
from models.user import User
from bson import ObjectId
from dotenv import load_dotenv
import re
import os
import logging

load_dotenv()

auth_ns = Namespace('auth', description='인증 관련 API')
# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = "your-secret-key"
ACCESS_TOKEN_EXPIRES = int(os.getenv("ACCESS_TOKEN_EXPIRES", 3600))
REFRESH_TOKEN_EXPIRES = int(os.getenv("REFRESH_TOKEN_EXPIRES", 1209600))

user_service = User()
blacklist = set()

def create_tokens(user_id):
    access_token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=ACCESS_TOKEN_EXPIRES)
    }, SECRET_KEY, algorithm='HS256')

    refresh_token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=REFRESH_TOKEN_EXPIRES)
    }, SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        if not token:
            return {'code': 401, 'message': 'Token is missing'}, 401

        if token in blacklist:
            return {'code': 401, 'message': 'Token has been revoked'}, 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.current_user_id = data.get('user_id') # JWT -> user_id 제공을 위해 추가

            # `user_id`를 ObjectId로 변환
            try:
                user_id = ObjectId(data['user_id'])
            except Exception:
                return {'code': 401, 'message': 'Invalid user ID in token'}, 401

            current_user = user_service.collection.find_one({'_id': user_id})
            if not current_user:
                return {'code': 401, 'message': 'User not found'}, 401
            
        except jwt.ExpiredSignatureError:
            return {'code': 401, 'message': 'Token has expired'}, 401
        except jwt.InvalidTokenError:
            return {'code': 401, 'message': 'Token is invalid'}, 401
        except Exception:
            return {'code': 401, 'message': 'Token is invalid or expired'}, 401

        return f(*args, **kwargs)
    return decorated


signup_model = auth_ns.model('Signup', {
    'username': fields.String(required=True, description='이메일'),
    'password': fields.String(required=True, description='비밀번호'),
    'nickname': fields.String(required=True, description='닉네임'),
})

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='이메일'),
    'password': fields.String(required=True, description='비밀번호'),
})

check_model = auth_ns.model('Check', {
    'value': fields.String(required=True, description='확인할 값 (닉네임 or 이메일)')
})

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.expect(signup_model)
    @auth_ns.doc(security=[])
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')
        nickname = data.get('nickname')

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', username):
            return {'code': 400, 'message': '유효하지 않은 이메일 형식입니다.'}, 400

        if user_service.find_by_username(username):
            return {'code': 400, 'message': '이미 존재하는 이메일입니다.'}, 400
        if user_service.find_by_nickname(nickname):
            return {'code': 400, 'message': '이미 존재하는 닉네임입니다.'}, 400

        user_id = user_service.create_user(username, password, nickname)
        if not user_id:
            return {'code': 400, 'message': '회원가입 실패'}, 400

        return {'code': 201, 'message': '회원가입 성공', 'data': {'user_id': user_id}}, 201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.expect(login_model)
    @auth_ns.doc(security=[])
    def post(self):
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = user_service.verify_user(username, password)
        if not user:
            return {'code': 401, 'message': '아이디 또는 비밀번호가 올바르지 않습니다.'}, 401

        access_token, refresh_token = create_tokens(str(user['_id']))

        return {
            'code': 200,
            'message': '로그인 성공',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 3600,
                'refresh_expires_in': 1209600,
                'user_id': str(user['_id']),
                'nickname': user['nickname']
            }
        }, 200

@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc(security='Bearer Auth')
    @token_required
    def post(self):
        auth_header = request.headers.get('Authorization')
        
        logging.debug(f'Authorization header: {auth_header!r}')

        if not auth_header:
            return {'code': 401, 'message': 'Authorization header missing'}, 401
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return {'code': 401, 'message': 'Invalid Authorization header'}, 401
        token = parts[1]

        blacklist.add(token)  # 토큰을 블랙리스트에 추가

        return {'code': 200, 'message': '로그아웃 성공'}, 200

@auth_ns.route('/nickname-check')
class NicknameCheck(Resource):
    @auth_ns.expect(check_model)
    @auth_ns.doc(security=[])
    def post(self):
        data = request.json
        nickname = data.get('value')
        if user_service.find_by_nickname(nickname):
            return {'code': 409, 'message': '이미 사용 중인 닉네임입니다.'}, 409
        return {'code': 200, 'message': '사용 가능한 닉네임입니다.'}, 200

@auth_ns.route('/email-check')
class EmailCheck(Resource):
    @auth_ns.expect(check_model)
    @auth_ns.doc(security=[])
    def post(self):
        data = request.json
        email = data.get('value')
        if user_service.find_by_username(email):
            return {'code': 409, 'message': '이미 사용 중인 이메일입니다.'}, 409
        return {'code': 200, 'message': '사용 가능한 이메일입니다.'}, 200

@auth_ns.route('/<string:user_id>')
class UserInfo(Resource):
    def get(self, user_id):
        try:
            user = user_service.collection.find_one({'_id': ObjectId(user_id)})
        except Exception:
            return {'code': 400, 'message': '유효하지 않은 user_id'}, 400
        if not user:
            return {'code': 404, 'message': '유저를 찾을 수 없습니다.'}, 404
        return {
            'code': 200,
            'message': '유저 정보 조회 성공',
            'data': {
                'nickname': user.get('nickname', ''),
                'email': user.get('username', '')
            }
        }, 200
