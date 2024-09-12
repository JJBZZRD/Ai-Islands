import pytest
import json
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def print_response(test_name, response):
    print(f"\n{test_name} Response:")
    print(json.dumps(response.json(), indent=2))

@pytest.mark.order1
def test_get_model_info_index():
    response = client.get("/library/get-model-info-index?model_id=ibm/granite-13b-chat-v2")
    print_response("Get Model Info", response)
    assert response.status_code == 200

@pytest.mark.order2
def test_download_model():
    response = client.post("/model/download-model?model_id=ibm/granite-13b-chat-v2")
    print_response("Download Model", response)
    assert response.status_code == 200

@pytest.mark.order3
def test_get_model_info_library():
    response = client.get("/library/get-model-info-library?model_id=ibm/granite-13b-chat-v2")
    print_response("Get Model Info", response)
    assert response.status_code == 200

@pytest.mark.order4
def test_load_model():
    response = client.post("/model/load?model_id=ibm/granite-13b-chat-v2")
    print_response("Load Model", response)
    assert response.status_code == 200

@pytest.mark.order5
def test_list_active_models():
    response = client.get("/model/active")
    print_response("List Active Models", response)
    assert response.status_code == 200

@pytest.mark.order6
def test_is_model_loaded():
    response = client.get("/model/is-model-loaded?model_id=ibm/granite-13b-chat-v2")
    print_response("Is Model Loaded", response)
    assert response.status_code == 200

@pytest.mark.order7
def test_inference():
    response = client.post("/model/inference", json={
        "model_id": "ibm/granite-13b-chat-v2",
        "data": {"payload": "Which colony produces quantum crystals?"}
    })
    print_response("Inference", response)
    assert response.status_code == 200

@pytest.mark.order8
def test_configure_model():
    # Check library content before configuration
    response = client.get("/library/get-model-info-library?model_id=ibm/granite-13b-chat-v2")
    print_response("Model Info Before Configuration", response)
    assert response.status_code == 200

    # Configure the model
    response = client.post("/model/configure", json={
        "model_id": "ibm/granite-13b-chat-v2",
        "data": {
            "rag_settings": {
                "use_dataset": True,
                "dataset_name": "fictional_space_colonies",
                "similarity_threshold": 0.4,
                "use_chunking": False
            }
        }
    })
    print_response("Configure Model", response)
    assert response.status_code == 200

    # Check library content after configuration
    response = client.get("/library/get-model-info-library?model_id=ibm/granite-13b-chat-v2")
    print_response("Model Info After Configuration", response)
    assert response.status_code == 200

@pytest.mark.order9
def test_inference_after_configuration():
    response = client.post("/model/inference", json={
        "model_id": "ibm/granite-13b-chat-v2",
        "data": {"payload": "Which colony produces quantum crystals?"}
    })
    print_response("Inference After Configuration", response)
    assert response.status_code == 200

@pytest.mark.order10
def test_unload_model():
    response = client.post("/model/unload?model_id=ibm/granite-13b-chat-v2")
    print_response("Unload Model", response)
    assert response.status_code == 200

@pytest.mark.order11
def test_is_model_loaded():
    response = client.get("/model/is-model-loaded?model_id=ibm/granite-13b-chat-v2")
    print_response("Is Model Loaded", response)
    assert response.status_code == 200

@pytest.mark.order12
def test_delete_model():
    response = client.delete("/model/delete-model?model_id=ibm/granite-13b-chat-v2")
    print_response("Delete Model", response)
    assert response.status_code == 200