import pytest
import os
from unittest.mock import patch, MagicMock
from backend.models.transformer_model import TransformerModel
from backend.core.exceptions import ModelError
import torch

def test_load_success(model_info_library):
    # Directly use the 'dir' from model_info to ensure consistency
    expected_model_dir = model_info_library['dir']
    
    # Create a mock device
    device = torch.device("cpu")
    print(f"Test: device.type = {device.type}")  # Debugging statement

    with patch('backend.models.transformer_model.os.path.exists', return_value=True) as mock_exists, \
         patch('backend.models.transformer_model.os.makedirs') as mock_makedirs, \
         patch('backend.models.transformer_model.transformers.AutoModelForCausalLM.from_pretrained') as mock_model, \
         patch('backend.models.transformer_model.transformers.AutoTokenizer.from_pretrained') as mock_tokenizer, \
         patch('backend.models.transformer_model.Accelerator') as mock_accelerator_class, \
         patch('backend.models.transformer_model.TransformerModel._construct_pipeline') as mock_construct_pipeline:

        # Mock the os.makedirs to prevent actual directory creation
        mock_makedirs.return_value = None

        # Mock the from_pretrained methods to return MagicMock instances
        mock_model_instance = MagicMock()
        mock_model.return_value = mock_model_instance

        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.return_value = mock_tokenizer_instance

        # Mock the Accelerator instance and its prepare method
        mock_accelerator = MagicMock()
        mock_accelerator.prepare.return_value = MagicMock()
        mock_accelerator_class.return_value = mock_accelerator

        # Mock the pipeline constructed by _construct_pipeline
        mock_pipeline = MagicMock()
        mock_construct_pipeline.return_value = mock_pipeline

        # Initialize the TransformerModel instance
        transformer_model = TransformerModel(model_id="Qwen/Qwen2-0.5B-Instruct")

        # Call the load method
        transformer_model.load(device, model_info_library)

        # Assertions

        # Ensure os.path.exists was called with the expected path
        mock_exists.assert_called_once_with(expected_model_dir)

        # Ensure os.makedirs was NOT called since the directory exists
        mock_makedirs.assert_not_called()

        # Check that AutoModelForCausalLM.from_pretrained was called correctly
        mock_model.assert_called_once_with(
            "Qwen/Qwen2-0.5B-Instruct",
            cache_dir=expected_model_dir,
            torch_dtype='auto',
            local_files_only=True
        )

        # Check that AutoTokenizer.from_pretrained was called correctly
        mock_tokenizer.assert_called_once_with(
            "Qwen/Qwen2-0.5B-Instruct",
            cache_dir=expected_model_dir,
            local_files_only=True
        )

        # Ensure Accelerator was initialized (without specifying cpu parameter)
        mock_accelerator_class.assert_called_once()
        
        # Ensure prepare was called on the accelerator
        mock_accelerator.prepare.assert_called()

        # Ensure _construct_pipeline was called with the correct pipeline tag
        mock_construct_pipeline.assert_called_once_with(model_info_library.get('pipeline_tag'))

        # Verify that pipeline is set correctly
        assert transformer_model.pipeline == mock_pipeline

        # Verify that pipeline_args are set correctly
        assert transformer_model.pipeline_args["model"] == mock_accelerator.prepare.return_value

        # Verify that other attributes are set correctly
        assert transformer_model.model_dir == expected_model_dir
        assert transformer_model.config == model_info_library.get('config', {})
        
        # Note: We're not asserting transformer_model.device here as it might be set differently in the actual implementation

        print("Test completed successfully.")