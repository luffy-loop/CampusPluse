import os
from pymongo import MongoClient, ASCENDING, DESCENDING

client = None
db = None


def get_db():
    global client, db

    if db is not None:
        return db

    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB_URI is not configured.")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
        maxPoolSize=20,
        minPoolSize=1
    )
    client.admin.command("ping")
    db = client[os.getenv("MONGODB_DB", "campuspluse")]

    complaints = db["complaints"]
    complaints.create_index([("uni_roll_no", ASCENDING)])
    complaints.create_index([("created_at", DESCENDING)])
    complaints.create_index([("category", ASCENDING), ("department", ASCENDING), ("location", ASCENDING)])

    return db


def get_complaints():
    return get_db()["complaints"]


def get_next_id():
    counters = get_db()["counters"]
    result = counters.find_one_and_update(
        {"_id": "complaints"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )
    return result["value"]
