from flask import Flask
from pymongo import MongoClient
from flask_restx import Api
from routes import auth
from routes import photo
from routes import album
from dotenv import load_dotenv
import os
from flask import render_template, send_from_directory

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

api.add_namespace(auth.auth_ns, path='/api/auth')
api.add_namespace(album.album_ns, path='/api/albums')
api.add_namespace(photo.photo_ns, path='/api/photos')

# @app.route('/')
# def home():
#     return "환영합니다! API 문서는 /swagger/에서 확인하세요."

@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/album/<album_id>")
def album_detail_page(album_id):
    return render_template("album.html", album_id=album_id)


@app.route("/photo/<photo_id>")
def photo_detail_page(photo_id):
    return render_template("photo.html", photo_id=photo_id)

@app.route("/invitations")
def invitations_page():
    return render_template("invitations.html")

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads'))
    return send_from_directory(uploads_dir, filename)

if __name__ == '__main__':
    app.run(debug=True)
