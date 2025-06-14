from flask                    import request, g, url_for, current_app
from flask_restx              import Namespace, Resource, fields, reqparse
from werkzeug.datastructures import FileStorage

from app            import mongo
from models.photo   import Photo
from routes.auth    import token_required, error_response

photo_ns  = Namespace('photos', description='사진 업로드/메타 관리 API')
photo_svc = Photo(mongo)

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file',     location='files', type=FileStorage, required=True, help='이미지 파일')
upload_parser.add_argument('album_id', location='form',  type=str,       required=True, help='앨범 ID')

photo_resp = photo_ns.model('PhotoResp', {
    'id':           fields.String(example='60b0...'),
    'filename':     fields.String(example='pic.jpg'),
    'url':          fields.String(example='http://host/uploads/pic.jpg'),
    'album_id':     fields.String(example='60af...'),
    'uploaded_at':  fields.DateTime(example='2025-06-10T12:30:00Z')
})

@photo_ns.route('/')
class PhotoList(Resource):
    @photo_ns.doc(security='Bearer Auth', description='앨범별 사진 메타 조회 (쿼리: album_id)')
    @photo_ns.response(200,'조회 성공', fields.List(fields.Nested(photo_resp)))
    @photo_ns.response(400,'잘못된 요청', error_response)
    @token_required
    def get(self):
        album_id = request.args.get('album_id','')
        if not album_id:
            return {'code':400,'message':'album_id 쿼리 필요'},400
        return photo_svc.list_by_album(album_id),200

    @photo_ns.doc(security='Bearer Auth', description='사진 업로드', parser=upload_parser)
    @photo_ns.response(201,'업로드 성공', photo_resp)
    @photo_ns.response(400,'잘못된 요청', error_response)
    @token_required
    def post(self):
        args = upload_parser.parse_args()
        return photo_svc.upload(args['file'], args['album_id']),201

@photo_ns.route('/<string:photo_id>')
class PhotoDetail(Resource):
    @photo_ns.doc(security='Bearer Auth', description='단일 사진 메타 조회')
    @photo_ns.response(200,'조회 성공', photo_resp)
    @photo_ns.response(404,'사진 없음', error_response)
    @token_required
    def get(self, photo_id):
        p = photo_svc.get(photo_id)
        if not p:
            return {'code':404,'message':'사진을 찾을 수 없습니다.'},404
        return p,200

    @photo_ns.doc(security='Bearer Auth', description='단일 사진 삭제')
    @photo_ns.response(204,'삭제 성공')
    @photo_ns.response(404,'사진 없음', error_response)
    @token_required
    def delete(self, photo_id):
        if not photo_svc.delete(photo_id):
            return {'code':404,'message':'사진을 찾을 수 없습니다.'},404
        return '',204