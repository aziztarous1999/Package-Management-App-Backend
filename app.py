from flask import Flask, request, jsonify
import os
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
colis_collection = mongo.db.colis

@app.route("/testConnection", methods=["GET"])
def testConnection():
    try:
        mongo.db.command("ping")
        return jsonify({"status": "success", "message": "MongoDB connected!"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
