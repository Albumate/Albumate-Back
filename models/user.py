from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

client = MongoClient('mongodb://localhost:27017/')
db = client['albumate']

class User:
    def __init__(self):
        self.collection = db['users']

    def find_by_username(self, username):
        return self.collection.find_one({'username': username})

    def find_by_nickname(self, nickname):
        return self.collection.find_one({'nickname': nickname})

    def create_user(self, username, password, nickname):
        if self.collection.find_one({'username': username}) or self.collection.find_one({'nickname': nickname}):
            return None

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        user_id = self.collection.insert_one({
            'username': username,
            'password': hashed_password,
            'nickname': nickname
        }).inserted_id
        return str(user_id)

    def verify_user(self, username, password):
        user = self.find_by_username(username)
        if not user:
            return None
        if not check_password_hash(user['password'], password):
            return None
        return user