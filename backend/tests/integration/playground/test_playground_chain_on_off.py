import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.playground_routes import PlaygroundRouter
from backend.controlers.playground_control import PlaygroundControl
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ModelError, PlaygroundError
from backend.playground.playground import Playground
from backend.settings.settings_service import SettingsService
from backend.controlers.runtime_control import RuntimeControl

class MockModelControl(ModelControl):
    def __init__(self):
        self.models = {}

    def load_model(self, model_id):
        self.models[model_id] = {'process': MagicMock(), 'conn': MagicMock()}
        return {"message": f"Model {model_id} loaded successfully"}

    def unload_model(self, model_id):
        if model_id in self.models:
            del self.models[model_id]
            return True
        return False

    def is_model_loaded(self, model_id):
        return model_id in self.models

@pytest.fixture
def mock_model_control():
    return MockModelControl()

@pytest.fixture
def mock_playground_data_1():
    return {
        "test_playground": {
            "description": "Test playground",
            "models": {
                "model1": {"input": "text", "output": "text"},
                "model2": {"input": "text", "output": "text"}
            },
            "chain": ["model1", "model2"],
            "active_chain": False
        }
    }

class MockPlaygroundControl(PlaygroundControl):
    def __init__(self, model_control, playground_data):
        self.playground_data= playground_data
        super().__init__(model_control)
        

    def _initialise_all_playgrounds(self):
        for playground_id in self.playground_data:
            self._initialise_playground(playground_id)

    def _get_playground_json_data(self, playground_id: str):
        return self.playground_data[playground_id]
    

@pytest.fixture
def mock_playground_control(mock_model_control, mock_playground_data_1):
    return MockPlaygroundControl(mock_model_control, mock_playground_data_1)

@pytest.fixture
def app(mock_playground_control):
    print("\n--- Creating app fixture ---")
    app = FastAPI()
    playground_router = PlaygroundRouter(mock_playground_control)
    print(f"Router routes: {playground_router.router.routes}")
    app.include_router(playground_router.router, prefix="/playground")
    print(f"App routes: {app.routes}")
    return app

@pytest.fixture
def client(app):
    print("\n--- Creating client fixture ---")
    return TestClient(app)

def test_load_chain_success(client, mock_playground_data_1):
    RuntimeControl._initialise_runtime_data()
    print("\n--- Running test_load_chain_success ---")
    playground_id = "test_playground"
    playground = mock_playground_data_1[playground_id]
        
    print(f"Sending POST request to /playground/load-chain with playground_id: {playground_id}")
    response = client.post("/playground/load-chain", json={"playground_id": playground_id})
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 200
    assert response.json()["data"] == {"playground_id": playground_id, "chain": playground["chain"]}
    assert response.json()["message"] == f"Playground chain loaded successfully"
    RuntimeControl._initialise_runtime_data()

def test_load_chain_playground_not_found(client):
    RuntimeControl._initialise_runtime_data()
    print("\n--- Running test_load_chain_playground_not_found ---")
    playground_id = "non_existent_playground"
        
    print(f"Sending POST request to /playground/load-chain with playground_id: {playground_id}")
    response = client.post("/playground/load-chain", json={"playground_id": playground_id})
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "\'Playground non_existent_playground not found\'"
    RuntimeControl._initialise_runtime_data()

def test_load_chain_already_active(client):
    RuntimeControl._initialise_runtime_data()
    print("\n--- Running test_load_chain_already_active ---")
    playground_id = "test_playground"
    client.post("/playground/load-chain", json={"playground_id": playground_id})
    first_runtime_data = RuntimeControl.get_runtime_data("playground")
    

    print(f"Sending POST request to /playground/load-chain with playground_id: {playground_id}")
    response = client.post("/playground/load-chain", json={"playground_id": playground_id})
    second_runtime_data = RuntimeControl.get_runtime_data("playground")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert first_runtime_data == second_runtime_data
    assert response.status_code == 409
    assert response.json()["error"]["message"] == f"Playground {playground_id} is already running a chain, please stop it before loading."
    RuntimeControl._initialise_runtime_data()

def test_load_chain_model_error(client):
    print("\n--- Running test_load_chain_model_error ---")
    playground_id = "test_playground"

    with patch.object(MockModelControl, 'load_model', side_effect=ModelError("Failed to load model")):

        print(f"Sending POST request to /playground/load-chain with playground_id: {playground_id}")
        response = client.post("/playground/load-chain", json={"playground_id": playground_id})
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 500
    assert response.json()["error"]["message"] == "Failed to load model"

def test_stop_chain_success(client):
    RuntimeControl._initialise_runtime_data()
    print("\n--- Running test_stop_chain_success ---")
    playground_id = "test_playground"
    client.post("/playground/load-chain", json={"playground_id": playground_id})
    first_runtime_data = RuntimeControl.get_runtime_data("playground")

        
    print(f"Sending POST request to /playground/stop-chain with playground_id: {playground_id}")
    response = client.post("/playground/stop-chain", json={"playground_id": playground_id})
    second_runtime_data = RuntimeControl.get_runtime_data("playground")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert first_runtime_data != second_runtime_data
    assert response.status_code == 204
    RuntimeControl._initialise_runtime_data()

def test_stop_chain_playground_not_found(client):
    print("\n--- Running test_stop_chain_playground_not_found ---")
    playground_id = "non_existent_playground"
    
        
    print(f"Sending POST request to /playground/stop-chain with playground_id: {playground_id}")
    response = client.post("/playground/stop-chain", json={"playground_id": playground_id})
    
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == f"\'Playground non_existent_playground not found\'"

def test_stop_chain_not_active(client):

    print("\n--- Running test_stop_chain_not_active ---")
    playground_id = "test_playground"
    

        
    print(f"Sending POST request to /playground/stop-chain with playground_id: {playground_id}")
    response = client.post("/playground/stop-chain", json={"playground_id": playground_id})
    

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 409
    assert response.json()["error"]["message"] == f"Playground {playground_id} is not running a chain, please load it before stopping."

def test_stop_chain_unload_error(client):
    print("\n--- Running test_stop_chain_unload_error ---")
    playground_id = "test_playground"
    
    client.post("/playground/load-chain", json={"playground_id": playground_id})
    with patch.object(MockModelControl, 'unload_model', side_effect=ModelError("Failed to unload model")):
        
        print(f"Sending POST request to /playground/stop-chain with playground_id: {playground_id}")
        response = client.post("/playground/stop-chain", json={"playground_id": playground_id})

    #This should always return 204 as due to implementation in model_control.py, unload_model will not be called if the model is in use by another playground
    assert response.status_code == 204
    


# @pytest.fixture(autouse=True)
# def mock_settings_service():
#     print("\n--- Setting up mock_settings_service ---")
#     async def mock_get_hardware_preference():
#         return 'cpu'

#     with patch('backend.settings.settings_service.SettingsService.get_hardware_preference', new=mock_get_hardware_preference):
#         yield