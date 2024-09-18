import pytest
import json
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_download_models(model_id_list):
    for model in model_id_list:
        response = client.post(f"/model/download-model?model_id={model}")
        assert response.status_code == 200

def test_create_playground(playground_id):
    response = client.post("/playground/create", json={
        "playground_id": playground_id,
        "description": "Test playground with offline NLP models"
    })
    assert response.status_code == 201

def test_add_models_to_playground(playground_id, model_id_list):
    for model in model_id_list:
        response = client.post("/playground/add-model", json={
            "playground_id": playground_id,
            "model_id": model
        })
        assert response.status_code == 200

def test_configure_chain(playground_id, model_id_list):
    response = client.post("/playground/configure-chain", json={
        "playground_id": playground_id,
        "chain": model_id_list
    })
    assert response.status_code == 200

def test_update_chain(playground_id, model_id):
    response = client.post("/playground/configure-chain", json={
        "playground_id": playground_id,
        "chain": [model_id]
    })
    assert response.status_code == 200

def test_remove_tts_model(playground_id):
    response = client.post("/playground/remove-model", json={
        "playground_id": playground_id,
        "model_id": "microsoft/speecht5_tts"
    })
    assert response.status_code == 204

def test_update_playground(playground_id):
    response = client.put("/playground/update", json={
        "playground_id": playground_id,
        "description": "Updated playground with only sentiment analysis model"
    })
    assert response.status_code == 200
    assert response.json().get("message") == "Playground updated successfully"

def test_get_playground_info(playground_id):
    response = client.get("/playground/info", params={"playground_id": playground_id})
    assert response.status_code == 200

def test_delete_playground(playground_id):
    response = client.delete("/playground/delete", params={"playground_id": playground_id})
    assert response.status_code == 204
