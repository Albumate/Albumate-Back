import os
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from .auth import token_required
from models.photo import Photo as PhotoModel

photo_ns = Namespace('photos', description='사진 업로드/다운로드 관련 API')

upload_parser = photo_ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='업로드할 이미지 파일')
upload_parser.add_argument('album_id', location='form', type=str, required=True, help='어느 앨범에 속할지 앨범 ID')

photo_model = photo_ns.model('Photo', {
    'photo_id': fields.String(readonly=True, description='사진 고유 ID'),
    'album_id': fields.String(description='앨범 ID'),
    'user_id': fields.String(description='업로드한 유저 ID'),
    'url': fields.String(description='외부에서 접근 가능한 사진 URL'),
    'original_filename': fields.String(description='원본 파일명'),
    'created_at': fields.DateTime(description='업로드 시각(UTC)'),
})

photo_service = PhotoModel()

@photo_ns.route('/')
class PhotoList(Resource):
    @photo_ns.doc(security='Bearer Auth')
    @token_required
    @photo_ns.expect(upload_parser)
    @photo_ns.marshal_with(photo_model, code=201)
    def post(self):
        """
        사진 업로드
        - multipart/form-data로
          - file         : (File) 업로드할 이미지
          - album_id     : (str) 해당 앨범 ID
        - 헤더: Authorization: Bearer {access_token}
        """
        args = upload_parser.parse_args()
        uploaded_file = args.get('file')
        album_id = args.get('album_id')
        user_id = request.current_user_id  # 토큰 데코레이터로부터 가져온 유저 ID

        if uploaded_file is None:
            photo_ns.abort(400, '파일을 첨부해주세요.')

        original_filename = uploaded_file.filename
        filename = secure_filename(original_filename)

        base_dir = os.path.dirname(__file__)
        upload_folder = os.path.abspath(os.path.join(base_dir, '../uploads'))
        os.makedirs(upload_folder, exist_ok=True)

        save_path = os.path.join(upload_folder, filename)
        uploaded_file.save(save_path)

        photo_id = photo_service.create(album_id=album_id,
                                        user_id=user_id,
                                        filename=filename,
                                        original_filename=original_filename)

        base_url = request.host_url.rstrip('/')
        file_url = f"{base_url}/uploads/{filename}"

        return {
            'photo_id': photo_id,
            'album_id': album_id,
            'user_id': user_id,
            'url': file_url,
            'original_filename': original_filename,
            'created_at': photo_service.find_by_id(photo_id)['created_at'].isoformat() + 'Z'
        }, 201

    @photo_ns.doc(security='Bearer Auth')
    @token_required
    @photo_ns.param('album_id', '조회할 앨범 ID (쿼리스트링)')
    @photo_ns.marshal_list_with(photo_model, code=200)
    def get(self):
        """
        특정 앨범에 속한 사진 메타데이터 리스트 조회.
        - 쿼리스트링: ?album_id=<앨범ID>
        - 헤더: Authorization: Bearer {access_token}
        """
        album_id = request.args.get('album_id')
        if not album_id:
            photo_ns.abort(400, '쿼리스트링에 album_id를 지정해주세요.')
        # 필요하다면 “소유자(owner_id) 체크”를 추가할 수 있음

        docs = photo_service.find_by_album(album_id)
        result = []
        base_url = request.host_url.rstrip('/')
        for doc in docs:
            file_url = f"{base_url}/uploads/{doc['filename']}"
            result.append({
                'photo_id': str(doc['_id']),
                'album_id': doc['album_id'],
                'user_id': doc['user_id'],
                'url': file_url,
                'original_filename': doc['original_filename'],
                'created_at': doc['created_at'].isoformat() + 'Z'
            })
        return result, 200

@photo_ns.route('/<string:photo_id>')
@photo_ns.param('photo_id', '조회할 사진의 고유 ID')
class PhotoDetail(Resource):
    @photo_ns.doc(security='Bearer Auth')
    @token_required
    @photo_ns.marshal_with(photo_model, code=200)
    def get(self, photo_id):
        """
        단일 사진 메타데이터 조회.
        - 헤더: Authorization: Bearer {access_token}
        """
        doc = photo_service.find_by_id(photo_id)
        if not doc:
            photo_ns.abort(404, '해당 ID의 사진이 없습니다.')

        base_url = request.host_url.rstrip('/')
        file_url = f"{base_url}/uploads/{doc['filename']}"

        return {
            'photo_id': str(doc['_id']),
            'album_id': doc['album_id'],
            'user_id': doc['user_id'],
            'url': file_url,
            'original_filename': doc['original_filename'],
            'created_at': doc['created_at'].isoformat() + 'Z'
        }, 200

    @photo_ns.doc(security='Bearer Auth')
    @token_required
    def delete(self, photo_id):
        """
        사진 삭제 (메타데이터 + 실제 파일 삭제).
        - 헤더: Authorization: Bearer {access_token}
        """
        doc = photo_service.find_by_id(photo_id)
        if not doc:
            photo_ns.abort(404, '해당 ID의 사진이 없습니다.')

        filename = doc['filename']
        base_dir = os.path.dirname(__file__)
        upload_folder = os.path.abspath(os.path.join(base_dir, '../uploads'))
        file_path = os.path.join(upload_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        success = photo_service.delete(photo_id)
        if not success:
            photo_ns.abort(500, 'DB에서 사진 메타 삭제 중 오류가 발생했습니다.')

        return {'message': '사진이 삭제되었습니다.'}, 200