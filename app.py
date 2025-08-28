from flask import Flask, request, jsonify
import os
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta, datetime
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import re
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "defaultsecret")
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

users_collection = mongo.db.users
colis_collection = mongo.db.colis


#check if email follows standard format
def valid_email(email: str) -> bool:
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None


#password must be 8 chars or more, at least 1 uppercase and 1 special char
def valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

# auth
@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    email = data["email"].strip()
    password = data["password"]

    if not valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400

    if not valid_password(password):
        return jsonify({
            "error": "Password must be at least 8 characters long, "
                     "contain 1 uppercase letter and 1 special character"
        }), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    users_collection.insert_one({"email": email, "password": hashed_pw})

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    user = users_collection.find_one({"email": data["email"]})
    if not user or not bcrypt.check_password_hash(user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=user["email"], expires_delta=timedelta(hours=1))
    return jsonify({"access_token": token}), 200

# generate random id
def generate_tracking_id():
    return str(uuid.uuid4())[:8]

# package status
ALLOWED_STATUSES = {"pending", "delivered", "canceled"}
TERMINAL_STATUSES = {"delivered", "canceled"}

# package routes
@app.route("/colis", methods=["POST"])
@jwt_required()
def create_colis():
    current_user = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    recipient_name = (data.get("recipient_name") or "").strip()
    address = (data.get("address") or "").strip()
    description = (data.get("description") or "").strip()
    status = "pending"

    if not recipient_name or not address:
        return jsonify({"error": "Missing required fields: recipient_name, address"}), 400

    if status not in ALLOWED_STATUSES:
        return jsonify({"error": f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}"}), 400

    tracking_id = generate_tracking_id()
    now = datetime.utcnow()

    colis_doc = {
        "tracking_id": tracking_id,
        "recipient_name": recipient_name,
        "address": address,
        "description": description,
        "status": status,
        "created_at": now,
        "updated_at": now,
        "sender_email": current_user,
    }

    colis_collection.insert_one(colis_doc)
    return jsonify({"message": "Package has been created", "tracking_id": tracking_id}), 201


@app.route("/colis/all", methods=["GET"])
@jwt_required()
def get_all_colis():
    current_user = get_jwt_identity()
    query = {"sender_email": current_user}
    colis_list = colis_collection.find(query, {"_id": 0}).sort("updated_at", -1)
    return jsonify(list(colis_list)), 200


@app.route("/colis/<tracking_id>", methods=["GET"])
@jwt_required()
def get_colis(tracking_id):
    current_user = get_jwt_identity()
    colis = colis_collection.find_one(
        {"tracking_id": tracking_id, "sender_email": current_user}, {"_id": 0}
    )
    if not colis:
        return jsonify({"error": "Package not found"}), 404
    return jsonify(colis), 200


@app.route("/colis/<tracking_id>/status", methods=["PATCH"])
@jwt_required()
def update_colis_status(tracking_id):
    current_user = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().lower()

    if new_status not in ALLOWED_STATUSES:
        return jsonify({"error": f"Invalid status. Allowed: {sorted(ALLOWED_STATUSES)}"}), 400

    colis = colis_collection.find_one({"tracking_id": tracking_id, "sender_email": current_user})
    if not colis:
        return jsonify({"error": "Package not found"}), 404

    if colis.get("status") in TERMINAL_STATUSES and new_status != colis.get("status"):
        return jsonify({"error": f"Cannot change status from terminal '{colis.get('status')}'"}), 409

    now = datetime.utcnow()
    update = {
        "$set": {"status": new_status, "updated_at": now},
    }

    colis_collection.update_one({"_id": colis["_id"]}, update)

    updated = colis_collection.find_one({"_id": colis["_id"]}, {"_id": 0})
    return jsonify(updated), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
