import base64
import json


def encode_token(key):
    data = json.dumps(key).encode()

    return base64.urlsafe_b64encode(data).decode()


def decode_token(token):
    data = base64.urlsafe_b64decode(token)

    return json.loads(data)
