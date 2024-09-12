import pytest
import json
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

@pytest.mark.order1
def test_get_model_info_index():
    endpoint = "/library/get-model-info-index"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Get Model Info", response)
    assert response.status_code == 200

@pytest.mark.order2
def test_download_model():
    endpoint = "/model/download-model"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Download Model", response)
    assert response.status_code == 200

@pytest.mark.order3
def test_get_model_info_library():
    endpoint = "/library/get-model-info-library"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Get Model Info", response)
    assert response.status_code == 200

@pytest.mark.order4
def test_load_model():
    endpoint = "/model/load"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Load Model", response)
    assert response.status_code == 200

@pytest.mark.order5
def test_list_active_models():
    endpoint = "/model/active"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(endpoint)
    # print_response("List Active Models", response)
    assert response.status_code == 200

@pytest.mark.order6
def test_is_model_loaded():
    endpoint = "/model/is-model-loaded"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Is Model Loaded", response)
    assert response.status_code == 200

@pytest.mark.order7
def test_inference():
    endpoint = "/model/inference"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(endpoint, json={
        "model_id": "ibm/granite-13b-chat-v2",
        "data": {"payload": "Which colony produces quantum crystals?"}
    })
    # print_response("Inference", response)
    assert response.status_code == 200

@pytest.mark.order8
def test_configure_model():
    endpoint = "/model/configure"
    print(f"\nTesting endpoint: {endpoint}")
    
    # Check library content before configuration
    response = client.get("/library/get-model-info-library?model_id=ibm/granite-13b-chat-v2")
    # print_response("Model Info Before Configuration", response)
    assert response.status_code == 200

    # Configure the model
    response = client.post(endpoint, json={
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
    # print_response("Configure Model", response)
    assert response.status_code == 200

    # Check library content after configuration
    response = client.get("/library/get-model-info-library?model_id=ibm/granite-13b-chat-v2")
    # print_response("Model Info After Configuration", response)
    assert response.status_code == 200

@pytest.mark.order9
def test_inference_after_configuration():
    endpoint = "/model/inference"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(endpoint, json={
        "model_id": "ibm/granite-13b-chat-v2",
        "data": {"payload": "Which colony produces quantum crystals?"}
    })
    # print_response("Inference After Configuration", response)
    assert response.status_code == 200

@pytest.mark.order10
def test_unload_model():
    endpoint = "/model/unload"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.post(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Unload Model", response)
    assert response.status_code == 200

@pytest.mark.order11
def test_is_model_loaded_after_unload():
    endpoint = "/model/is-model-loaded"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.get(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Is Model Loaded", response)
    assert response.status_code == 200

@pytest.mark.order12
def test_delete_model():
    endpoint = "/model/delete-model"
    print(f"\nTesting endpoint: {endpoint}")
    response = client.delete(f"{endpoint}?model_id=ibm/granite-13b-chat-v2")
    # print_response("Delete Model", response)
    assert response.status_code == 200

# Commented out as it's not being used in the tests
# def print_response(test_name, response):
#     print(f"\n{test_name} Response:")
#     print(json.dumps(response.json(), indent=2))