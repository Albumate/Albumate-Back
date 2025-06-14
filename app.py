import os
import datetime

from flask import Flask
from flask_pymongo import PyMongo
from flask_restx import Api
from flask_cors import CORS

# 전역 mongo 인스턴스
mongo = PyMongo()


def create_app():
    app = Flask(__name__)

    # 환경변수 또는 기본값
    app.config['MONGO_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/albumate')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super-secret-key')
    app.config['ACCESS_TOKEN_EXPIRES'] = int(os.getenv('ACCESS_TOKEN_EXPIRES', 3600))
    app.config['REFRESH_TOKEN_EXPIRES'] = int(os.getenv('REFRESH_TOKEN_EXPIRES', 1209600))

    # PyMongo 초기화
    mongo.init_app(app)

    # Swagger JWT 설정
    authorizations = {
        'Bearer Auth': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': "JWT를 'Bearer {token}' 형식으로 입력하세요"
        }
    }
    api = Api(
        app,
        version='0.1',
        title='Photo App API',
        description='사진 공유 앱 API 서버',
        doc='/swagger/',
        authorizations=authorizations,
        security='Bearer Auth'
    )
    CORS(app, resources={r"/api/*": {"origins": ["http://125.129.14.194:8000"]}})

    # 여기에만 routes import (circular import 방지)
    from routes.auth import auth_ns
    from routes.album import album_ns
    from routes.photo import photo_ns

    api.add_namespace(auth_ns, path='/api/auth')
    api.add_namespace(album_ns, path='/api/albums')
    api.add_namespace(photo_ns, path='/api/photos')

    @app.route('/')
    def home():
        return "환영합니다! API 문서는 /swagger/ 에서 확인하세요."

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)