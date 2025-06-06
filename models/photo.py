from pymongo import MongoClient
from bson import ObjectId
import datetime
import os

MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['albumate']

class Photo:
    def __init__(self):
        self.collection = db['photos']

    def create(self, album_id, user_id, filename, original_filename):
        doc = {
            'album_id': album_id,
            'user_id': user_id,
            'filename': filename,
            'original_filename': original_filename,
            'created_at': datetime.datetime.utcnow()
        }
        result = self.collection.insert_one(doc)
        return str(result.inserted_id)

    def find_by_id(self, photo_id):
        try:
            oid = ObjectId(photo_id)
        except:
            return None
        return self.collection.find_one({'_id': oid})

    def find_by_album(self, album_id):
        return list(self.collection.find({'album_id': album_id}))

    def delete(self, photo_id):
        try:
            oid = ObjectId(photo_id)
        except:
            return False
        result = self.collection.delete_one({'_id': oid})
        return result.deleted_count == 1