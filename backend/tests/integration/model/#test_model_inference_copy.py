import pytest
from unittest.mock import patch, MagicMock
from backend.models.transformer_model import TransformerModel
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ModelError

# Define MockTransformerModel at module level
class MockTransformerModel(TransformerModel):
    def __init__(self, model_id: str):
        super().__init__(model_id)
        self.model_id = model_id
        # Initialize attributes with default values
        self.config = {}
        self.model_dir = 'mock/dir'
        self.is_trained = False
        self.pipeline_tag = 'text-generation'
        self.device = 'cpu'
        
        # Create and set up the mock pipeline directly
        self.pipeline = MagicMock()
        self.pipeline.task = self.pipeline_tag
        self.pipeline.return_value = [{"generated_text": [{"content": "Mocked inference result"}]}]

    def load(self, device, model_info):
        # Use model_info to set up attributes
        self.config = model_info.get('config', {})
        self.model_dir = model_info.get('dir', 'mock/dir')
        self.is_trained = model_info.get('is_trained', False)
        self.pipeline_tag = model_info.get('pipeline_tag', 'text-generation')
        self.device = device
        # Simulate model loading
        pass

# Adjust the fixture to use MockTransformerModel
@pytest.fixture
def model_control(model_info_library):
    with patch('backend.controlers.model_control.ModelControl._get_model_class', return_value=MockTransformerModel), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_library', return_value=model_info_library), \
         patch('backend.controlers.model_control.LibraryControl.get_model_info_index', return_value=model_info_library), \
         patch('backend.settings.settings_service.SettingsService.get_hardware_preference', return_value='cpu'):
        model_control = ModelControl()
        model_control.load_model(model_info_library['base_model'])
        return model_control

def test_model_inference(model_control, model_info_library):
    model_id = model_info_library['base_model']
    inference_request = {
        'model_id': model_id,
        'data': {'payload': 'Test input'}
    }
    result = model_control.inference(inference_request)
    model_control.unload_model(model_id)
    expected_output = "Mocked inference result"
    print("result", result)
    assert result == expected_output
