from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

class User:
    def __init__(self, mongo):
        self.collection = mongo.db.users

    def find_by_username(self, username: str):
        return self.collection.find_one({'username': username})

    def find_by_nickname(self, nickname: str):
        return self.collection.find_one({'nickname': nickname})

    def find_by_id(self, user_id: str):
        doc = self.collection.find_one({'_id': ObjectId(user_id)})
        if not doc:
            return None
        return {
            'user_id': str(doc['_id']),
            'username': doc['username'],
            'nickname': doc['nickname']
        }

    def create_user(self, username: str, password: str, nickname: str) -> str | None:
        if self.find_by_username(username) or self.find_by_nickname(nickname):
            return None
        hashed = generate_password_hash(password)
        res = self.collection.insert_one({
            'username': username,
            'password': hashed,
            'nickname': nickname
        })
        return str(res.inserted_id)

    def verify_user(self, username: str, password: str) -> dict | None:
        user = self.find_by_username(username)
        if not user or not check_password_hash(user['password'], password):
            return None
        return user