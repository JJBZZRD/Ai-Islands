import pytest
import json
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def print_response(test_name, response):
    print(f"\n{test_name} Response:")
    print(json.dumps(response.json(), indent=2))

@pytest.mark.order1
def test_download_models():
    models = ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    for model in models:
        response = client.post(f"/model/download-model?model_id={model}")
        print_response(f"Download Model {model}", response)
        assert response.status_code == 200

@pytest.mark.order2
def test_create_playground():
    response = client.post("/playground/create", json={
        "description": "Test playground with Granite and NLU models"
    })
    print_response("Create Playground", response)
    assert response.status_code == 200
    assert "playground_id" in response.json()
    global playground_id
    playground_id = response.json()["playground_id"]

@pytest.mark.order3
def test_add_models_to_playground():
    models = ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    for model in models:
        response = client.post("/playground/add-model", json={
            "playground_id": playground_id,
            "model_id": model
        })
        print_response(f"Add Model {model} to Playground", response)
        assert response.status_code == 200

@pytest.mark.order4
def test_configure_chain():
    response = client.post("/playground/configure-chain", params={"playground_id": playground_id}, json={
        "chain": ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    })
    print_response("Configure Chain", response)
    assert response.status_code == 200

@pytest.mark.order5
def test_load_playground_chain():
    response = client.post("/playground/load-chain", params={"playground_id": playground_id})
    print_response("Load Playground Chain", response)
    assert response.status_code == 200
    assert response.json() == {"message": "Playground chain loaded successfully"}

@pytest.mark.order6
def test_playground_inference():
    response = client.post("/playground/inference", json={
        "playground_id": playground_id,
        "data": {"payload": "Analyze the sentiment of this sentence: I love using AI for testing!"}
    })
    print_response("Playground Inference", response)
    assert response.status_code == 200

@pytest.mark.order7
def test_remove_nlu_model():
    response = client.post("/playground/remove-model", json={
        "playground_id": playground_id,
        "model_id": "ibm/natural-language-understanding"
    })
    print_response("Remove NLU Model from Playground", response)
    assert response.status_code == 200

@pytest.mark.order8
def test_update_playground():
    response = client.put("/playground/update", json={
        "playground_id": playground_id,
        "description": "Updated playground with only Granite model"
    })
    print_response("Update Playground", response)
    assert response.status_code == 200

@pytest.mark.order9
def test_get_playground_info():
    response = client.get("/playground/info", params={"playground_id": playground_id})
    print_response("Get Playground Info", response)
    assert response.status_code == 200

@pytest.mark.order10
def test_reload_playground():
    response = client.post("/playground/load-chain", params={"playground_id": playground_id})
    print_response("Reload Playground Chain", response)
    assert response.status_code == 200
    assert response.json() == {"message": "Playground chain loaded successfully"}

@pytest.mark.order11
def test_playground_inference_after_reload():
    response = client.post("/playground/inference", json={
        "playground_id": playground_id,
        "data": {"payload": "What's the capital of France?"}
    })
    print_response("Playground Inference After Reload", response)
    assert response.status_code == 200

@pytest.mark.order12
def test_stop_playground_chain():
    response = client.post("/playground/stop-chain", params={"playground_id": playground_id})
    print_response("Stop Playground Chain", response)
    assert response.status_code == 200
    assert response.json() == {"message": "Playground chain stopped successfully"}

@pytest.mark.order13
def test_delete_playground():
    response = client.delete("/playground/delete", params={"playground_id": playground_id})
    print_response("Delete Playground", response)
    assert response.status_code == 200
    assert "message" in response.json()

@pytest.mark.order14
def test_unload_and_delete_models():
    models = ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    for model in models:
        response = client.post(f"/model/models/unload?model_id={model}")
        print_response(f"Unload Model {model}", response)
        if response.status_code != 200:
            print(f"Warning: Failed to unload model {model}. Status code: {response.status_code}")
            print(f"Response: {response.json()}")
        
        response = client.delete(f"/model/delete-model?model_id={model}")
        print_response(f"Delete Model {model}", response)
        assert response.status_code == 200