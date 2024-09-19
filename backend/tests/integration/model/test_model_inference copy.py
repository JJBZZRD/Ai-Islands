import pytest
from unittest.mock import MagicMock
from backend.models.transformer_model import TransformerModel

class MockTransformerModel(TransformerModel):
    def __init__(self, model_id: str, model_info: dict):
        super().__init__(model_id)
        self.model_id = model_id
        self.config = model_info.get('config', {})
        self.model_dir = model_info.get('dir')
        self.is_trained = model_info.get('is_trained', False)
        self.pipeline_tag = model_info.get('pipeline_tag')
        
        # Create a mock pipeline
        self.pipeline = MagicMock()
        self.pipeline.task = self.pipeline_tag
        self.pipeline.return_value = [{"generated_text": "Mocked inference result"}]

    def load(self, device, model_info: dict):
        self.device = device

    def inference(self, data: dict):
        # Use the mocked pipeline for inference
        result = self.pipeline(data.get('payload', ''))
        return result[0]['generated_text']

@pytest.fixture
def mock_transformer_model(model_info_library):
    return MockTransformerModel("Qwen/Qwen2-0.5B-Instruct", model_info_library)

# Example test function
def test_mock_transformer_model(mock_transformer_model, gpu_device, model_info_library):
    assert mock_transformer_model.model_id == "Qwen/Qwen2-0.5B-Instruct"
    assert mock_transformer_model.config == model_info_library['config']
    assert mock_transformer_model.model_dir == model_info_library['dir']
    assert mock_transformer_model.is_trained == False
    assert mock_transformer_model.pipeline_tag == model_info_library['pipeline_tag']

    mock_transformer_model.load(gpu_device, model_info_library)
    assert mock_transformer_model.device == gpu_device

    result = mock_transformer_model.inference({"payload": "Test input"})
    assert result == "Mocked inference result"
    mock_transformer_model.pipeline.assert_called_once_with("Test input")

# Add more tests as needed