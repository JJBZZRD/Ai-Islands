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
        
    def load_model(self, model_id):

        mock_conn = MagicMock()
        mock_conn.send = MagicMock()
        mock_conn.recv = MagicMock()
        mock_conn.recv.return_value = self._custom_inference_result(model_id)

        self.models[model_id] = {'process': MagicMock(), 'conn': mock_conn, "pid": 1234}

        return {"message": f"Model {model_id} loaded successfully"}

    def unload_model(self, model_id):
        if model_id in self.models:
            del self.models[model_id]
            return True
        return False

    def is_model_loaded(self, model_id):
        return model_id in self.models
    
    def _custom_inference_result(self, model_id):
        return f"Inference result for {model_id}"
    
    


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
        self._load_model_control_model()

    def _load_model_control_model(self):
        playground_data = self.playground_data.get("test_playground")
        for model_id in playground_data["chain"]:
            self.model_control.load_model(model_id)

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

def test_inference_success(client):
    RuntimeControl._initialise_runtime_data()
    playground_id = "test_playground"
    client.post("/playground/load-chain", json={"playground_id": playground_id})

    inference_request = {
        "playground_id": playground_id,
        "data": {"payload": "Test input"}
    }
    expected_result = "Inference result for model2"

    response = client.post("/playground/inference", json=inference_request)
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()["data"]
    assert response.json()["data"] == expected_result
    RuntimeControl._initialise_runtime_data()

def test_inference_playground_not_found(client):
    playground_id = "non_existent_playground"
    inference_request = {
        "playground_id": playground_id,
        "data": {"input": "Test input"}
    }

    response = client.post("/playground/inference", json=inference_request)
    print(f"Response: {response.json()}")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "'non_existent_playground'"

def test_inference_chain_not_active(client):
    playground_id = "test_playground"
    inference_request = {
        "playground_id": playground_id,
        "data": {"input": "Test input"}
    }
    with patch.object(MockModelControl, 'get_active_model', side_effect=KeyError("Model not found")):

        response = client.post("/playground/inference", json=inference_request)
    print(f"Response: {response.json()}")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "'Model not found'"

def test_inference_model_error(client, mock_playground_control):
    RuntimeControl._initialise_runtime_data()
    playground_id = "test_playground"

    inference_request = {
        "playground_id": playground_id,
        "data": {"input": "Test input"}
    }

    def error_inference_result(model_id):
        return {"error": f"{model_id} Inference failed"}

    with patch.object(MockModelControl, '_custom_inference_result', side_effect=error_inference_result):
        client.post("/playground/load-chain", json={"playground_id": playground_id})
        first_runtime_data = RuntimeControl.get_runtime_data("playground")
        response = client.post("/playground/inference", json=inference_request)
        second_runtime_data = RuntimeControl.get_runtime_data("playground")

    
    assert response.status_code == 500
    assert "Inference failed" in response.json()["error"]["message"]
    RuntimeControl._initialise_runtime_data()

def test_inference_invalid_request(client):
    inference_request = {
        "playground_id": "test_playground"
        # Missing 'data' field
    }

    response = client.post("/playground/inference", json=inference_request)
    print(f"Response: {response.json()}")
    assert response.status_code == 422  # Unprocessable Entity
    assert "Field required" in response.json()["detail"][0]["msg"]


