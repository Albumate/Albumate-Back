import datetime
import jwt
from functools       import wraps

from flask            import request, current_app, g
from flask_restx      import Namespace, Resource, fields

from app              import mongo
from models.user      import User

auth_ns = Namespace('auth', description='인증 관련 API')
user_svc = User(mongo)

# --- Swagger 모델 정의 ---
signup_model = auth_ns.model('Signup', {
    'username': fields.String(required=True, example='abc@abc.com'),
    'password': fields.String(required=True, example='password12'),
    'nickname': fields.String(required=True, example='st4rlit'),
})
signup_success = auth_ns.model('SignupSuccess', {
    'code':    fields.Integer(example=201),
    'message': fields.String(example='회원가입 성공'),
    'data':    fields.Nested(auth_ns.model('SignupData', {
        'user_id': fields.String(example='60af884f4f1c4e3f2c8b4567'),
    }))
})
login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, example='abc@abc.com'),
    'password': fields.String(required=True, example='password12'),
})
login_success = auth_ns.model('LoginSuccess', {
    'code':    fields.Integer(example=200),
    'message': fields.String(example='로그인 성공'),
    'data':    fields.Nested(auth_ns.model('LoginData', {
        'access_token':  fields.String(example='eyJ0eXAi...'),
        'refresh_token': fields.String(example='dGhpcyBp...'),
        'expires_in':    fields.Integer(example=3600),
        'user_id':       fields.String(example='60af884f4f1c4e3f2c8b4567'),
        'nickname':      fields.String(example='st4rlit'),
    }))
})
token_model = auth_ns.model('Refresh', {
    'refresh_token': fields.String(required=True)
})
user_resp = auth_ns.model('UserResp', {
    'user_id':  fields.String(example='60af884f4f1c4e3f2c8b4567'),
    'username': fields.String(example='abc@abc.com'),
    'nickname': fields.String(example='st4rlit'),
})
error_response = auth_ns.model('ErrorResponse', {
    'code':    fields.Integer(example=401),
    'message': fields.String(example='인증 실패')
})

def create_tokens(user_id: str):
    secret = current_app.config['SECRET_KEY']
    now    = datetime.datetime.utcnow()
    at = jwt.encode(
        {'user_id': user_id, 'exp': now + datetime.timedelta(seconds=current_app.config['ACCESS_TOKEN_EXPIRES'])},
        secret, algorithm='HS256'
    )
    rt = jwt.encode(
        {'user_id': user_id, 'exp': now + datetime.timedelta(seconds=current_app.config['REFRESH_TOKEN_EXPIRES'])},
        secret, algorithm='HS256'
    )
    return at, rt

def token_required(f):
    @wraps(f)
    def deco(*args, **kwargs):
        parts = request.headers.get('Authorization','').split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return {'code':401,'message':'Token missing'},401
        try:
            data = jwt.decode(parts[1], current_app.config['SECRET_KEY'], algorithms=['HS256'])
            g.user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return {'code':401,'message':'Token expired'},401
        except:
            return {'code':401,'message':'Invalid token'},401
        return f(*args, **kwargs)
    return deco

@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc(description='새 사용자 등록')
    @auth_ns.expect(signup_model, validate=True)
    @auth_ns.response(201,'회원가입 성공', signup_success)
    @auth_ns.response(400,'잘못된 요청', error_response)
    def post(self):
        data = request.json
        if user_svc.find_by_username(data['username']):
            return {'code':400,'message':'이미 존재하는 이메일'},400
        if user_svc.find_by_nickname(data['nickname']):
            return {'code':400,'message':'이미 존재하는 닉네임'},400
        uid = user_svc.create_user(data['username'], data['password'], data['nickname'])
        return {'code':201,'message':'회원가입 성공','data':{'user_id':uid}},201

@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc(description='로그인 (JWT 발급)')
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.response(200,'로그인 성공', login_success)
    @auth_ns.response(401,'인증 실패', error_response)
    def post(self):
        data = request.json
        user = user_svc.verify_user(data['username'], data['password'])
        if not user:
            return {'code':401,'message':'아이디 또는 비밀번호 불일치'},401
        at, rt = create_tokens(str(user['_id']))
        return {
            'code':200,'message':'로그인 성공',
            'data': {
                'access_token':  at,
                'refresh_token': rt,
                'expires_in':    current_app.config['ACCESS_TOKEN_EXPIRES'],
                'user_id':       str(user['_id']),
                'nickname':      user['nickname']
            }
        },200

@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc(security='Bearer Auth', description='로그아웃')
    @auth_ns.response(200,'로그아웃 성공')
    @auth_ns.response(401,'인증 실패', error_response)
    @token_required
    def post(self):
        return {'code':200,'message':'로그아웃 성공'},200

@auth_ns.route('/refresh')
class Refresh(Resource):
    @auth_ns.doc(description='리프레시 토큰으로 액세스 토큰 재발급')
    @auth_ns.expect(token_model, validate=True)
    @auth_ns.response(200,'토큰 재발급 성공', login_success)
    @auth_ns.response(401,'리프레시 실패', error_response)
    def post(self):
        rt = request.json.get('refresh_token','')
        try:
            data = jwt.decode(rt, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            uid = data['user_id']
        except:
            return {'code':401,'message':'Invalid refresh token'},401
        at, new_rt = create_tokens(uid)
        return {
            'code':200,'message':'토큰 재발급 성공',
            'data': {
                'access_token':  at,
                'refresh_token': new_rt,
                'expires_in':    current_app.config['ACCESS_TOKEN_EXPIRES'],
                'user_id':       uid
            }
        },200

@auth_ns.route('/<string:user_id>')
class GetUser(Resource):
    @auth_ns.doc(security='Bearer Auth', description='유저 정보 조회')
    @auth_ns.response(200,'조회 성공', user_resp)
    @auth_ns.response(404,'없음', error_response)
    @token_required
    def get(self, user_id):
        u = user_svc.find_by_id(user_id)
        if not u:
            return {'code':404,'message':'유저를 찾을 수 없습니다.'},404
        return u,200

@auth_ns.route('/email-check')
class EmailCheck(Resource):
    @auth_ns.doc(description='이메일 중복 체크')
    @auth_ns.expect(auth_ns.model('CheckEmail', {'value': fields.String(required=True)}), validate=True)
    @auth_ns.response(200,'사용 가능')
    @auth_ns.response(409,'중복', error_response)
    def post(self):
        v = request.json['value']
        if user_svc.find_by_username(v):
            return {'code':409,'message':'이미 사용 중인 이메일'},409
        return {'code':200,'message':'사용 가능'},200

@auth_ns.route('/nickname-check')
class NickCheck(Resource):
    @auth_ns.doc(description='닉네임 중복 체크')
    @auth_ns.expect(auth_ns.model('CheckNick', {'value': fields.String(required=True)}), validate=True)
    @auth_ns.response(200,'사용 가능')
    @auth_ns.response(409,'중복', error_response)
    def post(self):
        v = request.json['value']
        if user_svc.find_by_nickname(v):
            return {'code':409,'message':'이미 사용 중인 닉네임'},409
        return {'code':200,'message':'사용 가능'},200