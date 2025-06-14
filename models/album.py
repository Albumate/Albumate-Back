import datetime
import uuid
from bson import ObjectId

class Album:
    def __init__(self, mongo):
        self.collection = mongo.db.albums

    def create(self, owner_id: str, title: str, description: str = '') -> dict:
        now = datetime.datetime.utcnow()
        doc = {
            'owner_id': ObjectId(owner_id),
            'title': title,
            'description': description,
            'created_at': now
        }
        res = self.collection.insert_one(doc)
        return {
            'id': str(res.inserted_id),
            'owner_id': owner_id,
            'title': title,
            'description': description,
            'created_at': now.isoformat() + 'Z'
        }

    def get(self, album_id: str) -> dict | None:
        doc = self.collection.find_one({'_id': ObjectId(album_id)})
        if not doc:
            return None
        return {
            'id': str(doc['_id']),
            'owner_id': str(doc['owner_id']),
            'title': doc['title'],
            'description': doc.get('description',''),
            'created_at': doc['created_at'].isoformat() + 'Z'
        }

    def delete(self, album_id: str) -> bool:
        res = self.collection.delete_one({'_id': ObjectId(album_id)})
        return res.deleted_count == 1

    def list_all(self) -> list[dict]:
        out = []
        for doc in self.collection.find().sort('created_at', -1):
            out.append({
                'id': str(doc['_id']),
                'owner_id': str(doc['owner_id']),
                'title': doc['title'],
                'description': doc.get('description',''),
                'created_at': doc['created_at'].isoformat() + 'Z'
            })
        return out

    def list_by_owner(self, owner_id: str) -> list[dict]:
        out = []
        for doc in self.collection.find({'owner_id': ObjectId(owner_id)}).sort('created_at', -1):
            out.append({
                'id': str(doc['_id']),
                'owner_id': owner_id,
                'title': doc['title'],
                'description': doc.get('description',''),
                'created_at': doc['created_at'].isoformat() + 'Z'
            })
        return out

class Invitation:
    def __init__(self, mongo):
        self.collection = mongo.db.album_invitations

    def create(self, album_id: str, inviter_id: str, invitee_id: str) -> str:
        token = uuid.uuid4().hex
        now = datetime.datetime.utcnow()
        doc = {
            'album_id': ObjectId(album_id),
            'inviter_id': ObjectId(inviter_id),
            'invitee_id': ObjectId(invitee_id),
            'token': token,
            'status': 'pending',
            'created_at': now
        }
        self.collection.insert_one(doc)
        return token

    def list_for_user(self, user_id: str) -> list[dict]:
        out = []
        for doc in self.collection.find({'invitee_id': ObjectId(user_id)}).sort('created_at', -1):
            out.append({
                'invite_token': doc['token'],
                'album_id': str(doc['album_id']),
                'inviter_id': str(doc['inviter_id']),
                'status': doc['status'],
                'created_at': doc['created_at'].isoformat() + 'Z'
            })
        return out

    def get_by_token(self, token: str):
        return self.collection.find_one({'token': token})

    def update_status(self, token: str, status: str) -> bool:
        res = self.collection.update_one({'token': token}, {'$set': {'status': status}})
        return res.matched_count == 1

class Membership:
    def __init__(self, mongo):
        self.collection = mongo.db.album_members

    def add(self, album_id: str, user_id: str):
        q = {'album_id': ObjectId(album_id), 'user_id': ObjectId(user_id)}
        if not self.collection.find_one(q):
            self.collection.insert_one(q)

    def remove(self, album_id: str, user_id: str) -> bool:
        res = self.collection.delete_one({
            'album_id': ObjectId(album_id),
            'user_id': ObjectId(user_id)
        })
        return res.deleted_count == 1

    def list_members(self, album_id: str) -> list[str]:
        return [str(d['user_id']) for d in
                self.collection.find({'album_id': ObjectId(album_id)})]

    def list_user_albums(self, user_id: str) -> list[str]:
        return [str(d['album_id']) for d in
                self.collection.find({'user_id': ObjectId(user_id)})]