import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.playground_routes import PlaygroundRouter
from backend.controlers.playground_control import PlaygroundControl
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ChainNotCompatibleError, PlaygroundError, FileWriteError

@pytest.fixture
def mock_playground_control(mock_playground_data):
    with patch('backend.data_utils.json_handler.JSONHandler.read_json', return_value=mock_playground_data), \
         patch('backend.data_utils.json_handler.JSONHandler.write_json', return_value=True):
        yield PlaygroundControl(ModelControl())

@pytest.fixture
def client(mock_playground_control):
    app = PlaygroundRouter(mock_playground_control).router
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_settings_service():
    with patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
        yield

def test_configure_chain_success(client, mock_playground_data):
    playground_id = "test_playground"
    chain = ["model1", "model2"]
    response = client.post("/configure-chain", json={
        "playground_id": playground_id,
        "chain": chain
    })
    assert response.status_code == 200
    assert response.json()["data"]["playground_id"] == playground_id
    assert response.json()["data"]["chain"] == chain

def test_configure_chain_playground_not_found(client, mock_playground_data):
    playground_id = "non_existent_playground"
    chain = ["model1", "model2"]
    response = client.post("/configure-chain", json={
        "playground_id": playground_id,
        "chain": chain
    })
    assert response.status_code == 404
    assert "error" in response.json()
    assert playground_id in response.json()["error"]["message"]

def test_configure_chain_incompatible_models(client, mock_playground_data):
    playground_id = "test_playground"
    chain = ["model1", "model3"]  # Assuming model3 is incompatible
    with patch.object(PlaygroundControl, 'configure_chain', side_effect=ChainNotCompatibleError("Incompatible models")):
        response = client.post("/configure-chain", json={
            "playground_id": playground_id,
            "chain": chain
        })
    assert response.status_code == 422
    assert "error" in response.json()
    assert "incompatible" in response.json()["error"]["message"].lower()

def test_configure_chain_active_chain(client, mock_playground_data):
    playground_id = "test_playground"
    chain = ["model1", "model2"]
    with patch.object(PlaygroundControl, 'configure_chain', side_effect=PlaygroundError("Chain is already active")):
        response = client.post("/configure-chain", json={
            "playground_id": playground_id,
            "chain": chain
        })
    assert response.status_code == 409
    assert "error" in response.json()
    assert "already active" in response.json()["error"]["message"].lower()

def test_configure_chain_file_write_error(client, mock_playground_data):
    playground_id = "test_playground"
    chain = ["model1", "model2"]
    with patch('backend.controlers.playground_control.PlaygroundControl._write_playgrounds_to_json', side_effect=FileWriteError("File write error")):
        response = client.post("/configure-chain", json={
            "playground_id": playground_id,
            "chain": chain
        })
    assert response.status_code == 500
    assert "error" in response.json()
    assert "file write error" in response.json()["error"]["message"].lower()

def test_configure_chain_empty_chain(client, mock_playground_data):
    playground_id = "test_playground"
    chain = []
    response = client.post("/configure-chain", json={
        "playground_id": playground_id,
        "chain": chain
    })
    assert response.status_code == 200
    assert response.json()["data"]["playground_id"] == playground_id
    assert response.json()["data"]["chain"] == chain

def test_configure_chain_non_existent_model(client, mock_playground_data):
    playground_id = "test_playground"
    chain = ["model1", "non_existent_model"]
    with patch.object(PlaygroundControl, 'configure_chain', side_effect=KeyError("Model not found")):
        response = client.post("/configure-chain", json={
            "playground_id": playground_id,
            "chain": chain
        })
    assert response.status_code == 404
    assert "error" in response.json()
    assert "not found" in response.json()["error"]["message"].lower()