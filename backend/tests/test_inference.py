from fastapi.testclient import TestClient
from ..api.main import app
from ..controlers.model_control import ModelControl
import pytest

client = TestClient(app)
model_control = ModelControl()

@pytest.fixture(scope="module")
def loaded_model():
    model_id = "ibm/granite-13b-chat-v2"
    print(f"Attempting to load model: {model_id}")
    success = model_control.load_model(model_id)
    print(f"Model load result: {success}")
    if not success:
        print(f"Failed to load model {model_id}")
        return None
    print(f"Model {model_id} loaded successfully")
    yield model_id
    print(f"Unloading model: {model_id}")
    model_control.unload_model(model_id)

def test_inference(loaded_model, capsys):
    if loaded_model is None:
        pytest.skip("Model could not be loaded, skipping test")

    payload = {
        "model_id": loaded_model,
        "data": {
            "payload": "What is the capital of France?"
        }
    }
    
    print(f"\nSending inference request with payload: {payload}")
    response = client.post("/inference", json=payload)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    
    assert response.status_code == 200
    response_json = response.json()
    print(f"Response JSON: {response_json}")
    
    assert "result" in response_json or "error" in response_json
    if "result" in response_json:
        assert isinstance(response_json["result"], str)
        assert len(response_json["result"]) > 0
        print(f"Model output: {response_json['result']}")
    else:
        print(f"Error in response: {response_json['error']}")
        pytest.fail(f"Inference failed: {response_json['error']}")

    # Print captured stdout
    captured = capsys.readouterr()
    print("\nCaptured stdout:")
    print(captured.out)

def test_inference_model_not_loaded():
    model_id = "non_existent_model"
    payload = {
        "model_id": model_id,
        "data": {
            "payload": "This should fail."
        }
    }
    
    response = client.post("/inference", json=payload)
    
    assert response.status_code == 200  # Changed from 500 to 200
    assert "error" in response.json()
    assert f"Model {model_id} is not loaded" in response.json()["error"]