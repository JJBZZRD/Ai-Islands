import pytest
from unittest.mock import Mock, patch
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ModelError

@pytest.fixture
def mock_model_control(model_info):
    with patch('backend.controlers.model_control.LibraryControl') as mock_library_control, \
         patch('backend.controlers.model_control.SettingsService'):
        model_control = ModelControl()
        model_control.library_control = mock_library_control
        model_control.library_control.get_model_info_library.return_value = model_info
        yield model_control

def test_inference_success(mock_model_control, model_info):
    model_id = model_info['base_model']
    inference_request = {
        "model_id": model_id,
        "data": "test_data"
    }
    expected_response = {"result": "inference_output"}
    
    mock_active_model = {
        'conn': Mock()
    }
    mock_active_model['conn'].recv.return_value = expected_response
    
    mock_model_control.get_active_model = Mock(return_value=mock_active_model)
    
    result = mock_model_control.inference(inference_request)
    
    assert result == expected_response
    mock_model_control.get_active_model.assert_called_once_with(model_id)
    mock_active_model['conn'].send.assert_called_once_with({
        "model_id": model_id,
        "data": "test_data",
        "task": "inference"
    })

def test_inference_model_not_loaded(mock_model_control, model_info):
    model_id = model_info['base_model']
    inference_request = {
        "model_id": model_id,
        "data": "test_data"
    }
    
    mock_model_control.get_active_model = Mock(side_effect=KeyError(model_id))
    
    with pytest.raises(KeyError, match=model_id):
        mock_model_control.inference(inference_request)

def test_inference_missing_model_id(mock_model_control):
    inference_request = {
        "data": "test_data"
    }
    
    with pytest.raises(KeyError, match="model_id"):
        mock_model_control.inference(inference_request)

def test_inference_error_response(mock_model_control, model_info):
    model_id = model_info['base_model']
    inference_request = {
        "model_id": model_id,
        "data": "test_data"
    }
    error_response = {"error": "Inference failed"}
    
    mock_active_model = {
        'conn': Mock()
    }
    mock_active_model['conn'].recv.return_value = error_response
    
    mock_model_control.get_active_model = Mock(return_value=mock_active_model)
    
    with pytest.raises(ModelError, match="Inference failed"):
        mock_model_control.inference(inference_request)

@patch('backend.controlers.model_control.logger')
def test_inference_logging(mock_logger, mock_model_control, model_info):
    model_id = model_info['base_model']
    inference_request = {
        "model_id": model_id,
        "data": "test_data"
    }
    expected_response = {"result": "inference_output"}
    
    mock_active_model = {
        'conn': Mock()
    }
    mock_active_model['conn'].recv.return_value = expected_response
    
    mock_model_control.get_active_model = Mock(return_value=mock_active_model)
    
    mock_model_control.inference(inference_request)
    
    # Check if the logger was called with the expected messages
    mock_logger.error.assert_not_called()