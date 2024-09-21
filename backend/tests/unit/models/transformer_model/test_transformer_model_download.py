import pytest
import os
from unittest.mock import patch, MagicMock
from backend.models.transformer_model import TransformerModel

def test_download_success(model_info_index):
    expected_model_dir = os.path.join('data', 'downloads', 'transformers', "Qwen/Qwen2-0.5B-Instruct")
    
    with patch('backend.models.transformer_model.os.path.exists', return_value=False) as mock_exists, \
         patch('backend.models.transformer_model.os.makedirs') as mock_makedirs, \
         patch('backend.models.transformer_model.transformers.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('backend.models.transformer_model.transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
        
        mock_model.return_value = MagicMock()
        mock_tokenizer.return_value = MagicMock()
        
        updated_model_info = TransformerModel.download("Qwen/Qwen2-0.5B-Instruct", model_info_index)
        
        # Assertions
        mock_exists.assert_called_once_with(expected_model_dir)
        mock_makedirs.assert_called_once_with(expected_model_dir, exist_ok=True)
        mock_model.assert_called_once_with(
            "Qwen/Qwen2-0.5B-Instruct",
            cache_dir=expected_model_dir,
            **model_info_index['config']['model_config']
        )
        mock_tokenizer.assert_called_once_with(
            "Qwen/Qwen2-0.5B-Instruct",
            cache_dir=expected_model_dir,
            **model_info_index['config']['tokenizer_config']
        )
        assert updated_model_info["base_model"] == "Qwen/Qwen2-0.5B-Instruct"
        assert updated_model_info["dir"] == expected_model_dir
        assert updated_model_info["is_customised"] is False
        assert "config" in updated_model_info



def test_download_with_auth_token(model_info_index):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    expected_model_dir = os.path.join('data', 'downloads', 'transformers', model_id)
    
    # Modify the model_info_library fixture for this test
    model_info = model_info_index.copy()
    model_info['requirements']['requires_auth'] = True
    model_info['auth_token'] = 'test_auth_token'
    
    with patch('backend.models.transformer_model.os.path.exists', return_value=False) as mock_exists, \
         patch('backend.models.transformer_model.os.makedirs') as mock_makedirs, \
         patch('backend.models.transformer_model.transformers.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('backend.models.transformer_model.transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
        
        mock_model.return_value = MagicMock()
        mock_tokenizer.return_value = MagicMock()
        
        updated_model_info = TransformerModel.download(model_id, model_info)
        
        # Assertions
        mock_exists.assert_called_once_with(expected_model_dir)
        mock_makedirs.assert_called_once_with(expected_model_dir, exist_ok=True)
        
        # Check if the model and tokenizer were called with the auth token
        mock_model.assert_called_once_with(
            model_id,
            cache_dir=expected_model_dir,
            **model_info['config']['model_config']
        )
        mock_tokenizer.assert_called_once_with(
            model_id,
            cache_dir=expected_model_dir,
            **model_info['config']['tokenizer_config']
        )
        
        assert updated_model_info["base_model"] == model_id
        assert updated_model_info["dir"] == expected_model_dir
        assert updated_model_info["is_customised"] is False
        assert "config" in updated_model_info
        assert updated_model_info["config"]["auth_token"] == 'test_auth_token'

