
import base64
import gzip
import json
import os
import time
from flask import Blueprint, request

router = Blueprint("auth", __name__, url_prefix="/api")

def xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

def xor_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])

@router.route("/auth", methods=["POST"])
def auth():
    data = request.get_json(silent=True)
    username = data.get("username")
    password = data.get("password")
    env_username = os.getenv("AUTH_USERNAME")
    env_password = os.getenv("AUTH_PASSWORD")

    if username == env_username and password == env_password:
        token_obj = {
            "username": username,
            "timestamp": int(time.time())
        }
        token_json = json.dumps(token_obj).encode("utf-8")
        xor_key = os.getenv("TOKEN_SECRET", "default_secret").encode("utf-8")
        encrypted = xor_encrypt(token_json, xor_key)
        compressed = gzip.compress(encrypted)
        token = base64.urlsafe_b64encode(compressed).decode("utf-8")
        return {"status": True, "message": "Authentication successful", "token": token }
    else:
        return {"status": False, "message": "Invalid credentials"}

@router.route("/validate", methods=["GET"])
def validate_token():
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return {"status": False, "message": "Invalid token"}
    token = authorization.split(" ", 1)[1]
    try:
        compressed = base64.urlsafe_b64decode(token)
        xor_key = os.getenv("TOKEN_SECRET", "default_secret").encode("utf-8")
        encrypted = gzip.decompress(compressed)
        token_json = xor_decrypt(encrypted, xor_key)
        token_obj = json.loads(token_json.decode("utf-8"))
        expiry_minutes = int(os.getenv("TOKEN_EXPIRY_MINUTES", "5"))
        now = int(time.time())
        if (now - token_obj.get("timestamp", 0)) > (expiry_minutes * 60):
            return {"status": False, "message": "Token has expired"}
        return {"status": True, "message": "Token is valid", "token_data": token_obj}
    except Exception:
        return {"status": False, "message": "Invalid token"}

def token_required(request):
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return False
    token = authorization.split(" ", 1)[1]
    try:
        compressed = base64.urlsafe_b64decode(token)
        xor_key = os.getenv("TOKEN_SECRET", "default_secret").encode("utf-8")
        encrypted = gzip.decompress(compressed)
        token_json = xor_decrypt(encrypted, xor_key)
        token_obj = json.loads(token_json.decode("utf-8"))
        expiry_minutes = int(os.getenv("TOKEN_EXPIRY_MINUTES", "5"))
        now = int(time.time())
        if (now - token_obj.get("timestamp", 0)) > (expiry_minutes * 60):
            return False
        return True
    except Exception:
        return False
