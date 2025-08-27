from flask import Flask, request, jsonify
import os
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
import re

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "defaultsecret")
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

users_collection = mongo.db.users


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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
