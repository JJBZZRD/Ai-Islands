import pytest
from unittest.mock import Mock, patch
from backend.controlers.library_control import LibraryControl

@pytest.fixture
def mock_library_control():
    return LibraryControl()

@pytest.fixture
def mock_library():
    return {
        "Qwen/Qwen2-0.5B-Instruct": {
            "base_model": "Qwen/Qwen2-0.5B-Instruct",
            "is_customised": False
        },
        "Qwen/Qwen2-0.5B-Instruct-configured": {
            "base_model": "Qwen/Qwen2-0.5B-Instruct",
            "is_customised": True
        },
        "meta-llama/Meta-Llama-3-8B-Instruct": {
            "base_model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "is_customised": False
        },
        "google/gemma-2-2b-it": {
            "base_model": "google/gemma-2-2b-it",
            "is_customised": False
        },
        "IDEA-Research/grounding-dino-tiny": {
            "base_model": "IDEA-Research/grounding-dino-tiny",
            "is_customised": False
        }
    }

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_exact_match(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "Qwen/Qwen2-0.5B-Instruct"
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 2
    assert "Qwen/Qwen2-0.5B-Instruct" in result
    assert "Qwen/Qwen2-0.5B-Instruct-configured" in result

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_no_match(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "nonexistent_model"
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 0

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_partial_match(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 1
    assert "meta-llama/Meta-Llama-3-8B-Instruct" in result

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_case_sensitive(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "Qwen/Qwen2-0.5B-Instruct"  # Use the exact case as in the mock_library
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 2
    assert "Qwen/Qwen2-0.5B-Instruct" in result
    assert "Qwen/Qwen2-0.5B-Instruct-configured" in result

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_case_sensitive_no_match(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "qwen/qwen2-0.5b-instruct"  # Different case, should not match
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 0

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_multiple_matches(mock_read_json, mock_library_control, mock_library):
    mock_library["another-qwen-model"] = {
        "base_model": "Qwen/Qwen2-0.5B-Instruct",
        "is_customised": False
    }
    mock_read_json.return_value = mock_library
    base_model = "Qwen/Qwen2-0.5B-Instruct"
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 3
    assert "Qwen/Qwen2-0.5B-Instruct" in result
    assert "Qwen/Qwen2-0.5B-Instruct-configured" in result
    assert "another-qwen-model" in result

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_models_by_base_model_non_text_generation(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "IDEA-Research/grounding-dino-tiny"
    
    result = mock_library_control.get_models_by_base_model(base_model)
    
    assert len(result) == 1
    assert "IDEA-Research/grounding-dino-tiny" in result

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.logger')
def test_get_models_by_base_model_logging(mock_logger, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    base_model = "Qwen/Qwen2-0.5B-Instruct"
    
    mock_library_control.get_models_by_base_model(base_model)
    
    mock_logger.debug.assert_any_call(f"Searching for models with base_model: {base_model}")
    mock_logger.info.assert_called_with(f"Found 2 models with base_model {base_model}")