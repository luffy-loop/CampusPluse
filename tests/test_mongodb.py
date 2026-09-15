import mongomock

import mongodb


def test_mongodb_creates_expected_indexes(monkeypatch):
    fake_client = mongomock.MongoClient()
    monkeypatch.setattr(mongodb, "MongoClient", lambda *args, **kwargs: fake_client)
    mongodb.client = None
    mongodb.db = None

    db = mongodb.get_db()
    indexes = db["complaints"].index_information()

    assert any("uni_roll_no" in str(v["key"]) for v in indexes.values())
    assert any("created_at" in str(v["key"]) for v in indexes.values())
    assert any("category" in str(v["key"]) for v in indexes.values())


def test_mongodb_generates_incrementing_ids(monkeypatch):
    fake_client = mongomock.MongoClient()
    monkeypatch.setattr(mongodb, "MongoClient", lambda *args, **kwargs: fake_client)
    mongodb.client = None
    mongodb.db = None

    assert mongodb.get_next_id() == 1
    assert mongodb.get_next_id() == 2


def test_mongodb_stores_and_filters_complaints(monkeypatch):
    fake_client = mongomock.MongoClient()
    monkeypatch.setattr(mongodb, "MongoClient", lambda *args, **kwargs: fake_client)
    mongodb.client = None
    mongodb.db = None

    complaints = mongodb.get_complaints()
    complaints.insert_many([
        {"id": 1, "uni_roll_no": "A001", "status": "Pending"},
        {"id": 2, "uni_roll_no": "B001", "status": "Resolved"}
    ])

    rows = list(complaints.find({"uni_roll_no": "A001"}))

    assert len(rows) == 1
    assert rows[0]["id"] == 1
    assert rows[0]["status"] == "Pending"
