import os
import datetime
from bson import ObjectId
from flask import url_for, current_app

class Photo:
    def __init__(self, mongo):
        self.collection = mongo.db.photos

    def upload(self, file_storage, album_id: str) -> dict:
        now = datetime.datetime.utcnow()
        filename = f"{now.timestamp()}_{file_storage.filename}"
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        save_path = os.path.join(upload_dir, filename)
        file_storage.save(save_path)

        public_url = url_for('static', filename=filename, _external=True)
        doc = {
            'filename': filename,
            'url': public_url,
            'album_id': album_id,
            'uploaded_at': now
        }
        res = self.collection.insert_one(doc)
        return {
            'id': str(res.inserted_id),
            'filename': filename,
            'url': public_url,
            'album_id': album_id,
            'uploaded_at': now.isoformat() + 'Z'
        }

    def list_by_album(self, album_id: str) -> list[dict]:
        out = []
        for doc in self.collection.find({'album_id': album_id}).sort('uploaded_at', -1):
            out.append({
                'id': str(doc['_id']),
                'filename': doc['filename'],
                'url': doc['url'],
                'album_id': doc['album_id'],
                'uploaded_at': doc['uploaded_at'].isoformat() + 'Z'
            })
        return out

    def get(self, photo_id: str) -> dict | None:
        doc = self.collection.find_one({'_id': ObjectId(photo_id)})
        if not doc:
            return None
        return {
            'id': str(doc['_id']),
            'filename': doc['filename'],
            'url': doc['url'],
            'album_id': doc['album_id'],
            'uploaded_at': doc['uploaded_at'].isoformat() + 'Z'
        }

    def delete(self, photo_id: str) -> bool:
        doc = self.collection.find_one({'_id': ObjectId(photo_id)})
        if not doc:
            return False
        try:
            os.remove(os.path.join(current_app.root_path, 'uploads', doc['filename']))
        except:
            pass
        res = self.collection.delete_one({'_id': ObjectId(photo_id)})
        return res.deleted_count == 1