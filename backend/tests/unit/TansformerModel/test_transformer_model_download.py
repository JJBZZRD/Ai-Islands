import pytest
import os
from unittest.mock import patch, MagicMock
from backend.models.transformer_model import TransformerModel
from backend.core.exceptions import ModelError

def test_download_success(model_info_library):
    # Define the expected model directory path
    expected_model_dir = os.path.join('data', 'downloads', 'transformers', "Qwen/Qwen2-0.5B-Instruct")
    
    with patch('backend.models.transformer_model.os.path.exists', return_value=False) as mock_exists, \
         patch('backend.models.transformer_model.os.makedirs') as mock_makedirs, \
         patch('backend.models.transformer_model.transformers.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('backend.models.transformer_model.transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
        
        # Mock the return values of from_pretrained methods
        mock_model.return_value = MagicMock()
        mock_tokenizer.return_value = MagicMock()
        
        # Call the download method
        updated_model_info = TransformerModel.download("Qwen/Qwen2-0.5B-Instruct", model_info_library)
        
        # Assertions
        
        # Ensure os.path.exists was called with the expected path
        mock_exists.assert_called_once_with(expected_model_dir)
        
        # Ensure os.makedirs was called since os.path.exists returned False
        mock_makedirs.assert_called_once_with(expected_model_dir, exist_ok=True)
        
        # Check that AutoModelForCausalLM.from_pretrained was called correctly
        mock_model.assert_called_once_with(
            "Qwen/Qwen2-0.5B-Instruct",
            cache_dir=expected_model_dir,
            **model_info_library['config']['model_config']
        )
        
        # Check that AutoTokenizer.from_pretrained was called correctly
        mock_tokenizer.assert_called_once_with(
            "Qwen/Qwen2-0.5B-Instruct",
            cache_dir=expected_model_dir,
            **model_info_library['config']['tokenizer_config']
        )
        
        # Verify that model_info is updated correctly
        assert updated_model_info["base_model"] == "Qwen/Qwen2-0.5B-Instruct"
        assert updated_model_info["dir"] == expected_model_dir
        assert updated_model_info["is_customised"] is False
        assert "config" in updated_model_info


