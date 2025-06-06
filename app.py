from flask import Flask
from pymongo import MongoClient
from flask_restx import Api
from routes import auth
from routes import photo
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

mongo_uri = os.getenv('MONGODB_URI')
client = MongoClient(mongo_uri)
db = client['albumate']

authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "JWT 토큰을 'Bearer {token}' 형식으로 입력하세요."
    }
}

app.config['RESTX_MASK_SWAGGER'] = False # 필드 마스크 비활성화

api = Api(
    app,
    version='0.1',
    title='Photo App API',
    description='사진 공유 앱의 API 서버',
    terms_url='/',
    doc='/swagger/',
    authorizations=authorizations,
    security='Bearer Auth',
    mask=False          # 필드 마스크 비활성화
)

api.add_namespace(auth.auth_ns, path='/api/users')
# api.add_namespace(album.album_ns, path='/api/albums')
api.add_namespace(photo.photo_ns, path='/api/photos')

@app.route('/')
def home():
    return "환영합니다! API 문서는 /swagger/에서 확인하세요."

if __name__ == '__main__':
    app.run(debug=True)
