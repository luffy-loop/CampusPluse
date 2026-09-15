import json

import services.ai as ai


def test_ai_falls_back_on_invalid_json(monkeypatch):
    class Response:
        output_text = "not json"

    class Interactions:
        def create(self, **kwargs):
            return Response()

    class Client:
        interactions = Interactions()

    monkeypatch.setattr(ai.genai, "Client", lambda api_key=None: Client())
    ai.client = None

    result = ai.analyze_complaint("Broken classroom fan")

    assert result["category"] == "Other"
    assert result["department"] == "General Administration"
    assert result["priority"] == "Medium"
    assert result["severity"] == 5


def test_ai_normalizes_invalid_values(monkeypatch):
    payload = {
        "category": "Invalid",
        "department": "Invalid",
        "location": "Block A",
        "severity": 99,
        "priority": "Urgent",
        "issue": "Network problem",
        "recommended_action": "Inspect network"
    }

    class Response:
        output_text = json.dumps(payload)

    class Interactions:
        def create(self, **kwargs):
            return Response()

    class Client:
        interactions = Interactions()

    monkeypatch.setattr(ai.genai, "Client", lambda api_key=None: Client())
    ai.client = None

    result = ai.analyze_complaint("Wi-Fi is not working")

    assert result["category"] == "Other"
    assert result["department"] == "General Administration"
    assert result["priority"] == "Medium"
    assert result["severity"] == 5
    assert result["location"] == "Block A"


def test_ai_accepts_valid_analysis(monkeypatch):
    payload = {
        "category": "IT & Network",
        "department": "IT & Network Services",
        "location": "Library",
        "severity": 7,
        "priority": "High",
        "issue": "Wi-Fi outage",
        "recommended_action": "Inspect the network access point."
    }

    class Response:
        output_text = json.dumps(payload)

    class Interactions:
        def create(self, **kwargs):
            return Response()

    class Client:
        interactions = Interactions()

    monkeypatch.setattr(ai.genai, "Client", lambda api_key=None: Client())
    ai.client = None

    result = ai.analyze_complaint("Wi-Fi is down in the library")

    assert result == payload
