import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

# Constant playground ID for all tests
PLAYGROUND_ID = 'test_playground_router'

def print_response(endpoint, response):
    print(f"\n{endpoint} Response:")
    print(f"Status Code: {response.status_code}")
    try:
        print(response.json())
    except:
        print(response.text)

@pytest.mark.order1
def test_download_models():
    models = ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    for model in models:
        response = client.post(f"/model/download-model?model_id={model}")
        print_response(f"Download Model {model}", response)
        assert response.status_code == 200

@pytest.mark.order2
def test_create_playground():
    # Ensure the playground is deleted before creating it
    client.delete("/playground/delete", params={"playground_id": PLAYGROUND_ID})
    
    response = client.post("/playground/create", json={
        "playground_id": PLAYGROUND_ID,
        "description": "Test playground with Granite and NLU models"
    })
    print_response("Create Playground", response)
    assert response.status_code == 201
    response_data = response.json()
    assert "data" in response_data
    assert "playground_id" in response_data["data"]
    assert response_data["data"]["playground_id"] == PLAYGROUND_ID

@pytest.mark.order3
def test_add_models_to_playground():
    models = ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    for model in models:
        response = client.post("/playground/add-model", json={
            "playground_id": PLAYGROUND_ID,
            "model_id": model
        })
        print_response(f"Add Model {model}", response)
        assert response.status_code == 200

@pytest.mark.order4
def test_configure_chain():
    response = client.post("/playground/configure-chain", json={
        "playground_id": PLAYGROUND_ID,
        "chain": ["ibm/granite-13b-chat-v2", "ibm/natural-language-understanding"]
    })
    print_response("Configure Chain", response)
    assert response.status_code == 200

@pytest.mark.order5
def test_load_playground_chain():
    response = client.post("/playground/load-chain", json={"playground_id": PLAYGROUND_ID})
    print_response("Load Playground Chain", response)
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert response_data["message"] == "Playground chain loaded successfully"
    assert "data" in response_data
    assert "playground_id" in response_data["data"]
    assert response_data["data"]["playground_id"] == PLAYGROUND_ID
    assert "chain" in response_data["data"]
    assert isinstance(response_data["data"]["chain"], list)

@pytest.mark.order6
def test_playground_inference():
    response = client.post("/playground/inference", json={
        "playground_id": PLAYGROUND_ID,
        "data": {"payload": "Analyze the sentiment of this sentence: I love using AI for testing!"}
    })
    print_response("Playground Inference", response)
    assert response.status_code == 200
    # Add more specific assertions about the inference result if needed

@pytest.mark.order7
def test_remove_nlu_model():
    # Stop the chain before removing the model
    stop_response = client.post("/playground/stop-chain", json={"playground_id": PLAYGROUND_ID})
    print_response("Stop Playground Chain Before Removing Model", stop_response)
    assert stop_response.status_code in [200, 204]  # Allow both 200 and 204 (No Content)

    # Fetch playground info to ensure the chain is stopped
    info_response = client.get("/playground/info", params={"playground_id": PLAYGROUND_ID})
    print_response("Get Playground Info Before Removing Model", info_response)
    assert info_response.status_code == 200
    assert "data" in info_response.json()
    assert "playground_id" in info_response.json()["data"]
    assert info_response.json()["data"]["playground_id"] == PLAYGROUND_ID
    assert not info_response.json()["data"]["active_chain"]  # Ensure the chain is not active

    response = client.post("/playground/remove-model", json={
        "playground_id": PLAYGROUND_ID,
        "model_id": "ibm/natural-language-understanding"
    })
    print_response("Remove NLU Model from Playground", response)
    assert response.status_code == 200  # Expect success as chain is stopped

@pytest.mark.order8
def test_update_playground():
    # Stop the chain before updating the playground
    stop_response = client.post("/playground/stop-chain", json={"playground_id": PLAYGROUND_ID})
    print_response("Stop Playground Chain Before Update", stop_response)
    if stop_response.status_code == 404:
        # If the chain is not found, it might already be stopped
        print("Chain not found, assuming it is already stopped.")
    else:
        assert stop_response.status_code in [200, 204]  # Allow both 200 and 204 (No Content)

    # Fetch playground info to ensure the chain is stopped
    info_response = client.get("/playground/info", params={"playground_id": PLAYGROUND_ID})
    print_response("Get Playground Info Before Update", info_response)
    assert info_response.status_code == 200
    assert "data" in info_response.json()
    assert "playground_id" in info_response.json()["data"]
    assert info_response.json()["data"]["playground_id"] == PLAYGROUND_ID
    assert not info_response.json()["data"]["active_chain"]  # Ensure the chain is not active

    response = client.put("/playground/update", json={
        "playground_id": PLAYGROUND_ID,
        "description": "Updated playground with only Granite model"
    })
    print_response("Update Playground", response)
    assert response.status_code == 200

@pytest.mark.order9
def test_get_playground_info():
    response = client.get("/playground/info", params={"playground_id": PLAYGROUND_ID})
    print_response("Get Playground Info", response)
    assert response.status_code == 200

@pytest.mark.order10
def test_reload_playground():
    response = client.post("/playground/load-chain", json={"playground_id": PLAYGROUND_ID})
    print_response("Reload Playground Chain", response)
    assert response.status_code == 200
    assert response.json()["message"] == "Playground chain loaded successfully"

@pytest.mark.order11
def test_playground_inference_after_reload():
    response = client.post("/playground/inference", json={
        "playground_id": PLAYGROUND_ID,
        "data": {"payload": "What's the capital of France?"}
    })
    print_response("Playground Inference After Reload", response)
    assert response.status_code == 200
    # Add more specific assertions about the inference result if needed

@pytest.mark.order12
def test_stop_playground_chain():
    response = client.post("/playground/stop-chain", json={"playground_id": PLAYGROUND_ID})
    print_response("Stop Playground Chain", response)
    assert response.status_code in [200, 204]  # Allow both 200 and 204 (No Content)

@pytest.mark.order13
def test_delete_playground():
    response = client.delete("/playground/delete", params={"playground_id": PLAYGROUND_ID})
    print_response("Delete Playground", response)
    assert response.status_code in [200, 204]  # Allow both 200 and 204 (No Content)

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
        assert response.status_code in [200, 204, 409]  # Allow 409 if model is still in use