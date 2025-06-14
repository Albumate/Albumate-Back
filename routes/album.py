from flask         import request, g
from flask_restx   import Namespace, Resource, fields

from app                  import mongo
from models.album         import Album, Invitation, Membership
from routes.auth          import token_required, error_response

album_ns       = Namespace('albums', description='앨범 관련 API')
album_svc      = Album(mongo)
invite_svc     = Invitation(mongo)
membership_svc = Membership(mongo)

# 입력 DTO
album_model    = album_ns.model('AlbumDTO', {
    'title':       fields.String(required=True, example='여행 사진'),
    'description': fields.String(example='제주도 여행 사진 모음')
})
# 응답 모델
album_resp     = album_ns.inherit('AlbumResp', album_model, {
    'id':           fields.String(example='60af884f4f1c4e3f2c8b4567'),
    'owner_id':     fields.String(example='60af884f4f1c4e3f2c8b4567'),
    'created_at':   fields.DateTime(example='2025-06-10T12:00:00Z')
})
invite_model   = album_ns.model('InviteDTO', {
    'user_id':      fields.String(required=True, example='60af884f4f1c4e3f2c8b4567')
})
invitation_resp= album_ns.model('InvitationResp', {
    'invite_token': fields.String(example='abcdef1234'),
    'album_id':     fields.String(example='60af884f4f1c4e3f2c8b4567'),
    'inviter_id':   fields.String(example='60af884f4f1c4e3f2c8b4567'),
    'invitee_id':   fields.String(example='60af884f4f1c4e3f2c8b4567'),
    'status':       fields.String(example='pending'),
    'created_at':   fields.DateTime(example='2025-06-10T12:00:00Z')
})

@album_ns.route('/')
class AlbumList(Resource):
    @album_ns.doc(security='Bearer Auth', description='모든 앨범 조회 (생성일 내림차순)')
    @album_ns.response(200, '조회 성공', fields.List(fields.Nested(album_resp)))
    @token_required
    def get(self):
        return album_svc.list_all(), 200

    @album_ns.doc(security='Bearer Auth', description='새 앨범 생성')
    @album_ns.expect(album_model, validate=True)
    @album_ns.response(201, '생성 성공', album_resp)
    @token_required
    def post(self):
        d = request.json
        new = album_svc.create(g.user_id, d['title'], d.get('description',''))
        membership_svc.add(new['id'], g.user_id)
        return new, 201

@album_ns.route('/<string:user_id>/my')
class MyAlbums(Resource):
    @album_ns.doc(security='Bearer Auth', description='내가 소유하거나 참가 중인 앨범 조회')
    @album_ns.response(200, '조회 성공', fields.List(fields.Nested(album_resp)))
    @token_required
    def get(self, user_id):
        own = album_svc.list_by_owner(user_id)
        part_ids = membership_svc.list_user_albums(user_id)
        part = [album_svc.get(aid) for aid in part_ids if album_svc.get(aid)]
        combined = {a['id']: a for a in (own + part)}.values()
        return list(combined), 200

@album_ns.route('/<string:album_id>/invite')
class AlbumInvite(Resource):
    @album_ns.doc(security='Bearer Auth', description='다른 사용자를 앨범에 초대')
    @album_ns.expect(invite_model, validate=True)
    @album_ns.response(201, '초대 성공', fields.String(description='invite_token'))
    @album_ns.response(404, '앨범 없음', error_response)
    @token_required
    def post(self, album_id):
        if not album_svc.get(album_id):
            return {'code':404,'message':'앨범을 찾을 수 없습니다.'}, 404
        token = invite_svc.create(album_id, g.user_id, request.json['user_id'])
        return {'invite_token': token}, 201

@album_ns.route('/invitations')
class InvitationsList(Resource):
    @album_ns.doc(security='Bearer Auth', description='내가 받은 모든 초대 조회')
    @album_ns.response(200, '조회 성공', fields.List(fields.Nested(invitation_resp)))
    @token_required
    def get(self):
        return invite_svc.list_for_user(g.user_id), 200

@album_ns.route('/invitations/<string:token>/accept')
class InvitationAccept(Resource):
    @album_ns.doc(security='Bearer Auth', description='초대 수락')
    @album_ns.response(200, '수락 성공')
    @album_ns.response(404, '초대 없음', error_response)
    @token_required
    def post(self, token):
        inv = invite_svc.get_by_token(token)
        if not inv or str(inv['invitee_id']) != g.user_id:
            return {'code':404,'message':'초대를 찾을 수 없습니다.'}, 404
        invite_svc.update_status(token, 'accepted')
        membership_svc.add(inv['album_id'], g.user_id)
        return {'code':200,'message':'수락되었습니다.'}, 200

@album_ns.route('/invitations/<string:token>/reject')
class InvitationReject(Resource):
    @album_ns.doc(security='Bearer Auth', description='초대 거절')
    @album_ns.response(200, '거절 성공')
    @album_ns.response(404, '초대 없음', error_response)
    @token_required
    def post(self, token):
        inv = invite_svc.get_by_token(token)
        if not inv or str(inv['invitee_id']) != g.user_id:
            return {'code':404,'message':'초대를 찾을 수 없습니다.'}, 404
        invite_svc.update_status(token, 'rejected')
        return {'code':200,'message':'거절되었습니다.'}, 200

@album_ns.route('/<string:album_id>/members')
class AlbumMembers(Resource):
    @album_ns.doc(security='Bearer Auth', description='앨범 멤버 목록 조회')
    @album_ns.response(200, '조회 성공', fields.List(fields.String))
    @album_ns.response(404, '앨범 없음', error_response)
    @token_required
    def get(self, album_id):
        if not album_svc.get(album_id):
            return {'code':404,'message':'앨범을 찾을 수 없습니다.'}, 404
        return membership_svc.list_members(album_id), 200

@album_ns.route('/<string:album_id>/leave')
class AlbumLeave(Resource):
    @album_ns.doc(security='Bearer Auth', description='앨범에서 나가기')
    @album_ns.response(200, '나가기 성공')
    @album_ns.response(404, '앨범 없음', error_response)
    @token_required
    def post(self, album_id):
        if not album_svc.get(album_id):
            return {'code':404,'message':'앨범을 찾을 수 없습니다.'}, 404
        membership_svc.remove(album_id, g.user_id)
        return {'code':200,'message':'나갔습니다.'}, 200

@album_ns.route('/<string:album_id>')
class AlbumDetail(Resource):
    @album_ns.doc(security='Bearer Auth', description='단일 앨범 상세 조회')
    @album_ns.response(200, '조회 성공', album_resp)
    @album_ns.response(404, '앨범 없음', error_response)
    @token_required
    def get(self, album_id):
        a = album_svc.get(album_id)
        if not a:
            return {'code':404,'message':'앨범을 찾을 수 없습니다.'}, 404
        return a, 200

    @album_ns.doc(security='Bearer Auth', description='단일 앨범 삭제')
    @album_ns.response(204, '삭제 성공')
    @album_ns.response(404, '앨범 없음', error_response)
    @token_required
    def delete(self, album_id):
        if not album_svc.delete(album_id):
            return {'code':404,'message':'앨범을 찾을 수 없습니다.'}, 404
        return '', 204