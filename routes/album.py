import os
from flask import request
from flask_restx import Namespace, Resource, fields
from bson import ObjectId
from datetime import datetime
from models.album import Album
from .auth import token_required
from utils.response import make_response

album_ns = Namespace('albums', description='앨범 관련 API')
album_service = Album()

create_album_model = album_ns.model('CreateAlbum', {
    'title': fields.String(required=True, description='앨범 이름'),
    'description': fields.String(required=False, description='앨범 설명'),
    'invite_emails': fields.List(fields.String, required=False, description='초대할 이메일 목록')
})

invite_model = album_ns.model('InviteUsers', {
    'invite_emails': fields.List(fields.String, required=True, description='초대할 사용자 이메일 목록')
})

@album_ns.route('/')
class AlbumCreate(Resource):
    @album_ns.doc(security='Bearer Auth')
    @album_ns.expect(create_album_model)
    @token_required
    def post(self):
        user_id = request.current_user_id
        data = request.json
        title = data.get('title')
        description = data.get('description', '')
        invite_emails = data.get('invite_emails', [])

        result = album_service.create_album(
            owner_id=user_id,
            title=title,
            description=description,
            invite_emails=invite_emails
        )
        return make_response(201, '앨범 생성 및 초대 완료', result)

@album_ns.route('/<string:album_id>/invite')
class AlbumInvite(Resource):
    @album_ns.doc(security='Bearer Auth')
    @album_ns.expect(invite_model)
    @token_required
    def post(self, album_id):
        user_id = request.current_user_id
        data = request.json
        invite_emails = data.get('invite_emails', [])

        result = album_service.invite_users(
            album_id=album_id,
            from_user_id=user_id,
            invite_emails=invite_emails
        )

        return make_response(200, '초대 요청 완료', result)

@album_ns.route('/invitations')
class AlbumInvitations(Resource):
    @album_ns.doc(security='Bearer Auth')
    @token_required
    def get(self):
        user_id = ObjectId(request.current_user_id)
        invites = album_service.invite_collection.aggregate([
            {'$match': {'to_user_id': user_id, 'status': 'pending'}},
            {'$lookup': {
                'from': 'albums',
                'localField': 'album_id',
                'foreignField': '_id',
                'as': 'album_info'
            }},
            {'$unwind': '$album_info'},
            {'$lookup': {
                'from': 'users',
                'localField': 'from_user_id',
                'foreignField': '_id',
                'as': 'from_user'
            }},
            {'$unwind': '$from_user'},
            {'$project': {
                '_id': 0,
                'album_id': {'$toString': '$album_id'},
                'invite_token': 1,
                'from_user': {
                    'user_id': {'$toString': '$from_user._id'},
                    'nickname': '$from_user.nickname'
                },
                'album': {
                    'title': '$album_info.title',
                    'description': '$album_info.description'
                },
                'created_at': 1
            }}
        ])
        return make_response(200, '초대 목록 조회 완료', list(invites))

@album_ns.route('/invitations/<string:invite_token>/accept')
class AcceptInvitation(Resource):
    @album_ns.doc(security='Bearer Auth')
    @token_required
    def post(self, invite_token):
        user_id = ObjectId(request.current_user_id)
        album_doc = album_service.invite_collection.find_one({
            'invite_token': invite_token,
            'to_user_id': user_id,
            'status': 'pending'
        })

        if not album_doc:
            return make_response(404, '유효하지 않은 초대입니다.')

        album_service.member_collection.insert_one({
            'album_id': album_doc['album_id'],
            'user_id': user_id,
            'joined_at': datetime.utcnow()
        })

        album_service.invite_collection.update_one(
            {'_id': album_doc['_id']},
            {'$set': {'status': 'accepted'}}
        )

        return make_response(200, '초대를 수락했습니다.', {
            'album_id': str(album_doc['album_id'])
        })

@album_ns.route('/invitations/<string:invite_token>/reject')
class RejectInvitation(Resource):
    @album_ns.doc(security='Bearer Auth')
    @token_required
    def post(self, invite_token):
        user_id = ObjectId(request.current_user_id)
        result = album_service.invite_collection.update_one(
            {'invite_token': invite_token, 'to_user_id': user_id, 'status': 'pending'},
            {'$set': {'status': 'rejected'}}
        )

        if result.matched_count == 0:
            return make_response(404, '거절할 초대가 없습니다.')

        return make_response(200, '초대를 거절했습니다.')
    
@album_ns.route('/<string:user_id>/my')
@album_ns.param('user_id', '조회할 유저의 고유 ID')
class UserAlbums(Resource):
    @album_ns.doc(security='Bearer Auth')
    @token_required
    def get(self, user_id):
        """
        특정 유저가 생성했거나 멤버로 속한 앨범 목록 조회
        - 헤더: Authorization: Bearer {access_token}
        - 경로 파라미터: user_id
        """
        try:
            user_id = ObjectId(user_id)
        except Exception as e:
            return make_response(400, f'유효하지 않은 user_id: {str(e)}')

        albums = album_service.get_user_albums(user_id)
        return make_response(200, f'{user_id}의 앨범 목록 조회 성공', albums)
    
@album_ns.route('/<string:album_id>/members')
@album_ns.param('album_id', '조회할 앨범의 고유 ID')
class AlbumMembers(Resource):
    @album_ns.doc(security='Bearer Auth')
    @token_required
    def get(self, album_id):
        """
        특정 앨범에 속한 멤버 목록 조회
        - 헤더: Authorization: Bearer {access_token}
        """
        album_oid = ObjectId(album_id)
        members = album_service.member_collection.find({'album_id': album_oid})
        
        result = []
        for member in members:
            user = album_service.user_collection.find_one({'_id': member['user_id']})
            if user:
                result.append({
                    'user_id': str(user['_id']),
                    'nickname': user['nickname'],
                    'joined_at': member['joined_at'].isoformat() + 'Z'
                })
        
        return make_response(200, '앨범 멤버 목록 조회 완료', result)

@album_ns.route('/<string:album_id>/leave')
@album_ns.param('album_id', '나갈 앨범의 고유 ID')
class LeaveAlbum(Resource):
    @album_ns.doc(security='Bearer Auth')
    @token_required
    def post(self, album_id):
        """
        앨범에서 나가기
        - 헤더: Authorization: Bearer {access_token}
        """
        user_id = ObjectId(request.current_user_id)

        member = album_service.member_collection.find_one({
            'album_id': ObjectId(album_id),
            'user_id': user_id
        })

        if not member:
            return make_response(404, '해당 앨범의 멤버가 아닙니다.')

        album_service.member_collection.delete_one({
            'album_id': ObjectId(album_id),
            'user_id': user_id
        })

        return make_response(200, '그룹을 나갔습니다.')

@album_ns.route('/<string:album_id>')
class AlbumDetail(Resource):
    @token_required
    def get(self, album_id):
        album = album_service.collection.find_one({'_id': ObjectId(album_id)})
        if not album:
            return make_response(404, "앨범을 찾을 수 없습니다.", None)
        return make_response(200, "앨범 조회 성공", {
            "album_id": str(album['_id']),
            "title": album['title'],
            "description": album.get('description', ''),
            "created_at": album['created_at'].isoformat() + 'Z'
        })