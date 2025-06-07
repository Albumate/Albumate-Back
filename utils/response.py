from json import JSONEncoder
from datetime import datetime

def make_response(code, message, data=None):
    if data:
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        from json import dumps
        data = JSONEncoder(default=convert_datetime).encode(data)

    return {'code': code, 'message': message, 'data': data}, code
