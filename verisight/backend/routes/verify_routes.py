from flask import Blueprint, request, jsonify
from backend.db.database import get_db
import hashlib
import os
from flask_jwt_extended import jwt_required

verify_bp = Blueprint("verify", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../../data/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def hash_file(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def deepfake_check(file_path: str) -> str:
    """Placeholder for deepfake detection."""
    return "Real"  # Replace with real model inference

@verify_bp.route("/api/verify", methods=["POST"])
@jwt_required()
def verify_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    file_bytes = file.read()
    file_hash = hash_file(file_bytes)

    # Save file
    file_path = os.path.join(UPLOAD_FOLDER, f"{file_hash}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    result = deepfake_check(file_path)

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO verifications (hash_value, data, result) VALUES (?, ?, ?)",
            (file_hash, file.filename, result)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify({
        "hash": file_hash,
        "filename": file.filename,
        "verification_result": result
    }), 200
