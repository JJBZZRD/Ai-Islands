import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.model_routes import ModelRouter
from backend.controlers.model_control import ModelControl
import multiprocessing as real_multiprocessing  # Import under a different name
from backend.core.exceptions import ModelError, ModelNotAvailableError
from backend.controlers.runtime_control import RuntimeControl
from backend.models.transformer_model import TransformerModel

class MockConnWrapper:
    def __init__(self, conn):
        self.conn = conn
        self.send_result = None

    def send(self, obj):
        self.send_result = obj
    
    def update_test_data(self, test_data):
        self.test_data.update(test_data)

    def recv(self):
        return self.conn.recv()

    def close(self):
        self.conn.close()
    
    def real_send(self):
        self.conn.send(self.send_result)

    def __getattr__(self, name):
        return getattr(self.conn, name)


class MockModelControl(ModelControl):
    async def get_hardware_preference(self):
        return "cpu"

    @staticmethod
    def _download_process(conn, model_class, model_id, model_info, library_control):
        test_data = {}

        # Create mock objects
        from unittest.mock import patch, MagicMock
        mock_class = MagicMock()
        mock_from_pretrained = MagicMock()
        mock_class.from_pretrained = mock_from_pretrained
        test_data.update({"Just before patches": True})
        RuntimeControl.update_runtime_data("test_data", test_data)
        with patch('backend.models.transformer_model.getattr', return_value=mock_class) as mock_getattr, \
             patch('backend.models.transformer_model.os.path.exists', return_value=False) as mock_exists, \
             patch('backend.models.transformer_model.os.makedirs') as mock_makedirs:

                # Collect test data
                wrapped_conn = MockConnWrapper(conn)
                # Call the parent class's _download_process with the wrapped conn
                ModelControl._download_process(wrapped_conn, model_class, model_id, model_info, library_control)

                # After process is done, collect call counts
                test_data['mock_makedirs_called'] = mock_makedirs.called
                test_data['mock_getattr_called'] = mock_getattr.called
                test_data['mock_from_pretrained_call_count'] = mock_from_pretrained.call_count
                RuntimeControl.update_runtime_data("test_data", test_data)
                wrapped_conn.real_send()

    def download_model(self, model_id: str, auth_token: str = None):
        try:
            self._download_model(model_id, auth_token)
            return {"message": f"Model {model_id} downloaded successfully"}
        except Exception as e:
            error_info = {
                "error name": type(e).__name__,
                "error message": str(e)
            }

            if "error name" in error_info and "error message" in error_info:
                raise ModelError(f"Error: {error_info['error message']}")
            else:
                raise ModelError("Unexpected Error occurred during model download")


@pytest.fixture
def model_control():
    return MockModelControl()

@pytest.fixture
def app(model_control):
    app = FastAPI()
    model_router = ModelRouter(model_control)
    app.include_router(model_router.router, prefix="/model")
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_download_model_success(client, model_control, mock_index_entry):
    RuntimeControl._initialise_runtime_data()
    model_id, model_info = next(iter(mock_index_entry.items()))
    print(f"Testing download for model: {model_id}")


    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=TransformerModel):

        print("Sending POST request...")
        response = client.post(f"/model/download-model?model_id={model_id}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

    test_data = RuntimeControl.get_runtime_data("test_data")
    print(f"Runtime data: {test_data}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Model {model_id} downloaded successfully"

    # Access the test data
    assert test_data['mock_makedirs_called'] is True
    assert test_data['mock_getattr_called'] is True
    assert test_data['mock_from_pretrained_call_count'] == 2

    RuntimeControl._initialise_runtime_data()

def test_download_model_not_available(client, model_control):
    RuntimeControl._initialise_runtime_data()
    model_id = "NonExistentModel"
    print(f"Testing download for non-existent model: {model_id}")
    
    with patch.object(ModelControl, '_download_model', side_effect=ModelNotAvailableError("Model not available")):
        print("Sending POST request...")
        response = client.post(f"/model/download-model?model_id={model_id}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

    assert response.status_code == 500
    assert "Model not available" in response.json()["error"]["message"]

    RuntimeControl._initialise_runtime_data()

def test_download_model_error(client, model_control):
    RuntimeControl._initialise_runtime_data()
    model_id = "ErrorModel"
    print(f"Testing download with error for model: {model_id}")
    
    with patch.object(ModelControl, '_download_model', side_effect=Exception("Download failed")):
        print("Sending POST request...")
        response = client.post(f"/model/download-model?model_id={model_id}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

    assert response.status_code == 500
    assert "Download failed" in response.json()["error"]["message"]

    RuntimeControl._initialise_runtime_data()

def test_download_model_with_auth(client, mock_index_entry):
    RuntimeControl._initialise_runtime_data()
    model_id, model_info = next(iter(mock_index_entry.items()))
    auth_token = "test_token"
    print(f"Testing download with auth for model: {model_id}")

    mock_class = MagicMock()
    mock_from_pretrained = MagicMock()
    mock_class.from_pretrained = mock_from_pretrained

    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=TransformerModel), \
         patch('backend.models.transformer_model.getattr', return_value=mock_class), \
         patch('backend.models.transformer_model.os.path.exists', return_value=False), \
         patch('backend.models.transformer_model.os.makedirs'):
        
        print("Sending POST request...")
        response = client.post(f"/model/download-model?model_id={model_id}&auth_token={auth_token}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.content}")

    test_data = RuntimeControl.get_runtime_data("test_data")
    print(f"Runtime data: {test_data}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Model {model_id} downloaded successfully"
    assert test_data['mock_from_pretrained_call_count'] == 2
    
    # Check if auth_token was used in from_pretrained calls
    for call in mock_from_pretrained.call_args_list:
        assert call[1].get('use_auth_token') == auth_token

    RuntimeControl._initialise_runtime_data()