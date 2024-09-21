import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.model_routes import ModelRouter
from backend.core.exceptions import ModelError
from backend.models.transformer_model import TransformerModel
from backend.controlers.model_control import ModelControl
import logging

logger = logging.getLogger(__name__)
class MockTransformerModel(TransformerModel):
    def __init__(self, model_id: str):
        super().__init__(model_id)
        self.model_id = model_id
        self.config = {}
        self.model_dir = 'mock/dir'
        self.is_trained = False
        self.pipeline_tag = 'text-generation'
        self.device = 'cpu'
        self.pipeline = MagicMock()
        self.pipeline.task = self.pipeline_tag
        self.pipeline.side_effect = self._pipeline_return_value

    def _pipeline_return_value(self, *args, **kwargs):

        if args[0][0]['content'] == "model error test":
            raise ModelError("Inference failed")
        else:
            return [{"generated_text":[{"role":"assistant","content":"I'm an AI assistant. How can I help you today?"}]}]

    def load(self, device, model_info):
        self.config = model_info.get('config', {})
        self.model_dir = model_info.get('dir', 'mock/dir')
        self.is_trained = model_info.get('is_trained', False)
        self.pipeline_tag = model_info.get('pipeline_tag', 'text-generation')
        self.device = device

@pytest.fixture
def model_control(model_info_library):
    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=MockTransformerModel), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_library', return_value=model_info_library), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_index', return_value=model_info_library), \
         patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
        model_control = ModelControl()
        model_control.load_model(model_info_library['base_model'])
        yield model_control
        # Clean up after the test
        model_control.unload_model(model_info_library['base_model'])
    


@pytest.fixture
def app(model_control):
    app = FastAPI()
    model_router = ModelRouter(model_control)
    app.include_router(model_router.router, prefix="/model")
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_inference_success(client, model_info_library):
    model_id = model_info_library['base_model']
    inference_data = "Hello, how are you?"
    expected_output =  "I'm an AI assistant. How can I help you today?"

    response = client.post("/model/inference", json={"model_id": model_id, "data": {"payload":inference_data}})
    print(response.json())
    assert response.status_code == 200
    assert response.json()["data"] == expected_output

def test_inference_model_not_loaded(client, model_control):
    model_id = "NonLoadedModel"
    inference_data = "Hello, how are you?"
    
    
    response = client.post("/model/inference", json={"model_id": model_id, "data": {"payload":inference_data}})

    assert response.status_code == 400
    assert f"{model_id}" in response.json()["error"]["message"]

def test_inference_model_error(client, model_info_library):
    model_id = model_info_library['base_model']
    inference_data = "model error test"
    
    response = client.post("/model/inference", json={"model_id": model_id, "data": {"payload":inference_data}})
    print({"response":response.json()})
    assert response.status_code == 500
    assert "Inference failed" in response.json()["error"]["message"]

def test_inference_invalid_request(client):
    response = client.post("/model/inference", json={"data": "Invalid request"})
    assert response.status_code == 422  # Unprocessable Entity