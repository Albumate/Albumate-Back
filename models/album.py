from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timezone
import uuid

client = MongoClient('mongodb://localhost:27017/')
db = client['albumate']

class Album:
    def __init__(self):
        self.collection = db['albums']
        self.member_collection = db['album_members']
        self.invite_collection = db['album_invitations']
        self.user_collection = db['users']

    def create_album(self, owner_id, title, description, invite_emails):
        invite_token = str(uuid.uuid4())
        album_doc = {
            'owner_id': ObjectId(owner_id),
            'title': title,
            'description': description,
            'invite_token': invite_token,
            'created_at': datetime.now(timezone.utc)
        }
        album_id = self.collection.insert_one(album_doc).inserted_id

        self.member_collection.insert_one({
            'album_id': album_id,
            'user_id': ObjectId(owner_id),
            'joined_at': datetime.now(timezone.utc)
        })

        users = list(self.user_collection.find({'username': {'$in': invite_emails}}))
        for user in users:
            self.invite_collection.insert_one({
                'album_id': album_id,
                'to_user_id': user['_id'],
                'from_user_id': ObjectId(owner_id),
                'invite_token': invite_token,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc)
            })

        return {'album_id': str(album_id), 'invite_token': invite_token}

    def invite_users(self, album_id, from_user_id, invite_emails):
        album_oid = ObjectId(album_id)
        album = self.collection.find_one({'_id': album_oid})
        if not album:
            return {'invited_user_ids': [], 'ignored_emails': invite_emails}

        invite_token = album.get('invite_token')
        users = list(self.user_collection.find({'username': {'$in': invite_emails}}))
        invited = []

        for user in users:
            # 중복 초대 방지
            already_invited = self.invite_collection.find_one({
                'album_id': album_oid,
                'to_user_id': user['_id']
            })
            if already_invited:
                continue

            self.invite_collection.insert_one({
                'album_id': album_oid,
                'to_user_id': user['_id'],
                'from_user_id': ObjectId(from_user_id),
                'invite_token': invite_token,
                'status': 'pending',
                'created_at': datetime.now(timezone.utc)
            })
            invited.append(str(user['_id']))

        return {
            'invited_user_ids': invited,
            'ignored_emails': list(set(invite_emails) - set([u['username'] for u in users]))
        }
    
    def get_user_albums(self, user_id):
        """유저가 소유하거나 멤버로 속한 앨범 조회"""
        user_id = ObjectId(user_id)
        member_albums = self.member_collection.find({'user_id': user_id})
        member_album_ids = [member['album_id'] for member in member_albums]

        albums = self.collection.find({
            '$or': [
                {'owner_id': user_id}, 
                {'_id': {'$in': member_album_ids}}  
            ]
        })

        return [{
            'album_id': str(album['_id']),
            'title': album['title'],
            'description': album.get('description', ''),
            'created_at': album['created_at'].isoformat() + 'Z',
            'is_owner': str(album['owner_id']) == str(user_id)
        } for album in albums]