from flask import Blueprint, request, jsonify
from backend.db.database import get_db
import hashlib
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "email", "password")):
        return jsonify({"error": "Missing fields"}), 400

    username = data["username"]
    email = data["email"]
    password_hash = hash_password(data["password"])

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ("username", "password")):
        return jsonify({"error": "Missing fields"}), 400

    username = data["username"]
    password_hash = hash_password(data["password"])

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?", 
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            token = create_access_token(identity=username)
            return jsonify({"message": "Login successful", "token": token}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
