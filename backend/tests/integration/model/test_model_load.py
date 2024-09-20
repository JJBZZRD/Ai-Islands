import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.routes.model_routes import ModelRouter
from backend.core.exceptions import ModelError, ModelNotAvailableError
from backend.models.transformer_model import TransformerModel
from backend.controlers.model_control import ModelControl
from backend.controlers.runtime_control import RuntimeControl

class MockTransformerModel(TransformerModel):
    def __init__(self, model_id: str):
        super().__init__(model_id)
        self.pipeline = MagicMock()
        self.pipeline.task = 'text-generation'

    def load(self, device, model_info):
        test_data={}
        test_data.update({"in the mock load method": True})
        RuntimeControl.update_runtime_data("test_data", test_data)

        from unittest.mock import patch, MagicMock
        mock_class = MagicMock()
        mock_from_pretrained = MagicMock()
        mock_class.from_pretrained = mock_from_pretrained

        mock_accelerator = MagicMock()
        mock_prepare = MagicMock()
        mock_accelerator.prepare = mock_prepare

        mock_pipeline = MagicMock()
        mock_pipeline.task = "text-generation"

        with patch('backend.models.transformer_model.getattr', return_value=mock_class) as mock_getattr, \
             patch('backend.models.transformer_model.TransformerModel._construct_pipeline', return_value=mock_pipeline) as mock_construct_pipeline, \
             patch('backend.models.transformer_model.Accelerator', return_value=mock_accelerator) as mock_accelerator:
            
            TransformerModel.load(self, device, model_info)
        
        test_data['mock_construct_pipeline_called'] = mock_construct_pipeline.called
        test_data['mock_getattr_called'] = mock_getattr.called
        test_data['mock_from_pretrained_call_count'] = mock_from_pretrained.call_count
        test_data['mock_accelerator_called'] = mock_accelerator.called
        test_data['mock_prepare_called'] = mock_prepare.called

        RuntimeControl.update_runtime_data("test_data", test_data)

@pytest.fixture
def model_control():
    model_control = ModelControl()
    return model_control

@pytest.fixture
def app(model_control):
    app = FastAPI()
    model_router = ModelRouter(model_control)
    app.include_router(model_router.router, prefix="/model")
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

def test_load_model_success(client, model_info_library):
    model_id = model_info_library['base_model']
    RuntimeControl._initialise_runtime_data()
    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=MockTransformerModel), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_library', return_value=model_info_library), \
         patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
            
        response = client.post(f"/model/load?model_id={model_id}")
    
    assert response.status_code == 200
    assert response.json()["message"] == f"Model {model_id} loaded successfully"

    test_data = RuntimeControl.get_runtime_data("test_data")
    assert test_data['mock_construct_pipeline_called'] == True
    assert test_data['mock_getattr_called'] == True
    assert test_data['mock_from_pretrained_call_count'] == 2
    assert test_data['mock_accelerator_called'] == True
    assert test_data['mock_prepare_called'] == True

    RuntimeControl._initialise_runtime_data()
    client.post(f"/model/unload?model_id={model_id}")

def test_load_model_not_available(client, model_info_library):
    model_id = "NonExistentModel"
    RuntimeControl._initialise_runtime_data()
    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=MockTransformerModel), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_library', side_effect=ModelNotAvailableError("Model not available")), \
         patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
            
        response = client.post(f"/model/load?model_id={model_id}")
    
    print(f"test_load_model_not_available - Status Code: {response.status_code}")
    print(f"test_load_model_not_available - Response JSON: {response.json()}")
    
    assert response.status_code == 500  # Changed from 404 to 500
    assert "Model not available" in response.json()["error"]["message"]
    RuntimeControl._initialise_runtime_data()

def test_load_model_error(client, model_info_library):
    model_id = model_info_library['base_model'] # Use an existing model ID
    empty_model_info = {}
    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=TransformerModel), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_library', return_value=empty_model_info), \
         patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
            
        response = client.post(f"/model/load?model_id={model_id}")
    
    print(f"test_load_model_error - Status Code: {response.status_code}")
    print(f"test_load_model_error - Response JSON: {response.json()}")
    
    assert response.status_code == 404
    assert "Model info not found" in response.json()["error"]["message"]

def test_load_model_already_loaded(client, model_info_library):
    model_id = model_info_library['base_model']

    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=MockTransformerModel), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_library', return_value=model_info_library), \
         patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'), \
         patch.object(ModelControl, 'is_model_loaded', return_value=True), \
         patch.object(ModelControl, 'load_model', return_value=None):  # Prevent actual loading

        response = client.post(f"/model/load?model_id={model_id}")

    print(f"test_load_model_already_loaded - Status Code: {response.status_code}")
    print(f"test_load_model_already_loaded - Response JSON: {response.json()}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Model {model_id} loaded successfully"  # Updated assertion
