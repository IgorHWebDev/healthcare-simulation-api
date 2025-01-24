import pytest
from fastapi.testclient import TestClient
from src.healthcare_simulation.api import app
import json

client = TestClient(app)

def test_simulate_scenario():
    headers = {
        "X-API-Key": "test_api_key",
        "Content-Type": "application/json"
    }
    
    payload = {
        "title": "👨‍⚕️ פרמדיק מתמודד עם דום לב",
        "actors": [
            "👨‍⚕️ פרמדיק (Paramedic)",
            "🤒 חולה (Patient)",
            "👨‍👩‍👦 בן משפחה (Family Member)"
        ],
        "steps": [
            {
                "step": 1,
                "description": "🚨 הערכת מצב ראשונית",
                "actions": [
                    {
                        "action": "בדיקת הכרה",
                        "details": "קריאה למטופל וטלטול עדין של הכתפיים",
                        "references": ["AHA ACLS Guidelines 2020 - Initial Assessment"],
                        "vital_signs": {
                            "pre_assessment": {
                                "❤️ דופק": "לא נמוש",
                                "🫁 נשימות": "אין",
                                "🌡️ חום": "36.5",
                                "⚡ לחץ דם": "לא נמדד"
                            }
                        }
                    }
                ]
            }
        ]
    }

    response = client.post("/v1/healthcare/simulate", 
                          headers=headers,
                          json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "scenario_id" in data
    assert "current_state" in data
    assert "next_steps" in data
    assert "feedback" in data

def test_validate_protocol():
    headers = {
        "X-API-Key": "test_api_key",
        "Content-Type": "application/json"
    }
    
    payload = {
        "protocol_type": "ACLS",
        "actions": [
            "Initial assessment",
            "Check responsiveness",
            "Call for help",
            "Check pulse"
        ],
        "patient_context": {
            "age": 65,
            "presenting_condition": "Unresponsive patient",
            "contraindications": []
        }
    }

    response = client.post("/v1/healthcare/validate", 
                          headers=headers,
                          json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "score" in data
    assert isinstance(data["score"], float)
    assert 0 <= data["score"] <= 100

def test_missing_api_key():
    payload = {
        "protocol_type": "ACLS",
        "actions": ["Initial assessment"]
    }
    
    response = client.post("/v1/healthcare/validate", 
                          json=payload)
    
    assert response.status_code == 403
    assert "Could not validate credentials" in response.json()["detail"] 