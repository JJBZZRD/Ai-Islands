import pytest
from unittest.mock import patch, MagicMock
import torch
from backend.models.transformer_model import TransformerModel

@pytest.fixture
def transformer_model():
    return TransformerModel("test_model_id")

def test_transformer_model_init(transformer_model):
    assert transformer_model.model_id == "test_model_id"
    assert transformer_model.pipeline_args == {}
    assert transformer_model.pipeline is None
    assert transformer_model.config is None
    assert transformer_model.device is None
    assert transformer_model.model_dir is None
    assert transformer_model.languages == {}
    assert transformer_model.accelerator is None
    assert transformer_model.model_instance_data == []
    assert transformer_model.is_trained is False
    assert transformer_model.dataset_management is None

@patch('backend.models.transformer_model.Accelerator')
@patch('backend.models.transformer_model.transformers')
@patch('backend.models.transformer_model.DatasetManagement')
def test_transformer_model_load(mock_dataset_management, mock_transformers, mock_accelerator, transformer_model, model_info_library):
    mock_device = MagicMock(spec=torch.device)
    mock_accelerator_instance = MagicMock()
    mock_accelerator.return_value = mock_accelerator_instance

    transformer_model.load(mock_device, model_info_library)

    assert transformer_model.model_dir == model_info_library['dir']
    assert transformer_model.config == model_info_library['config']
    assert transformer_model.device == mock_device
    assert transformer_model.languages == model_info_library.get('languages', {})
    assert transformer_model.is_trained == model_info_library.get('is_trained', False)

    mock_accelerator.assert_called_once_with(cpu=(mock_device == "cpu"))
    mock_transformers.pipeline.assert_called_once()
    
    if model_info_library['config'].get('rag_settings', {}).get('use_dataset'):
        mock_dataset_management.assert_called_once()
    else:
        mock_dataset_management.assert_not_called()

@patch('backend.models.transformer_model.transformers')
def test_transformer_model_load_with_quantization(mock_transformers, transformer_model, model_info_library):
    mock_device = MagicMock(spec=torch.device)
    model_info_library['config']['quantization_config'] = {'current_mode': 'int8'}
    model_info_library['config']['quantization_config_options'] = {'int8': {'load_in_8bit': True}}

    transformer_model.load(mock_device, model_info_library)

    mock_transformers.BitsAndBytesConfig.assert_called_once_with(load_in_8bit=True)

@patch('backend.models.transformer_model.transformers')
def test_transformer_model_load_with_bfloat16(mock_transformers, transformer_model, model_info_library):
    mock_device = MagicMock(spec=torch.device)
    model_info_library['config']['quantization_config'] = {'current_mode': 'bfloat16'}

    transformer_model.load(mock_device, model_info_library)

    assert transformer_model.config['model_config']['torch_dtype'] == torch.bfloat16

@patch('backend.models.transformer_model.transformers')
def test_transformer_model_load_with_translation_config(mock_transformers, transformer_model, model_info_library):
    mock_device = MagicMock(spec=torch.device)
    model_info_library['config']['translation_config'] = {'src_lang': 'en', 'tgt_lang': 'fr'}
    model_info_library['languages'] = {'en': 'English', 'fr': 'French'}

    # Mock the _is_languages_supported method to return True
    with patch.object(TransformerModel, '_is_languages_supported', return_value=True):
        transformer_model.load(mock_device, model_info_library)

    # Check if the pipeline was created with the correct task
    mock_transformers.pipeline.assert_called_once()
    call_args = mock_transformers.pipeline.call_args
    assert call_args[1]['task'] == 'translation_en_to_fr'

    # Additional assertions
    assert transformer_model.languages == {'en': 'English', 'fr': 'French'}
    assert transformer_model.config['translation_config'] == {'src_lang': 'en', 'tgt_lang': 'fr'}

@patch('backend.models.transformer_model.transformers')
def test_transformer_model_load_error_handling(mock_transformers, transformer_model, model_info_library):
    mock_device = MagicMock(spec=torch.device)
    mock_transformers.pipeline.side_effect = Exception("Test error")

    with pytest.raises(Exception) as exc_info:
        transformer_model.load(mock_device, model_info_library)

    assert str(exc_info.value) == "Test error"

# Add more tests as needed for other methods like inference, train, etc.