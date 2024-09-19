import pytest
from unittest.mock import Mock, patch
from backend.controlers.model_control import ModelControl

@pytest.fixture
def mock_model_control(model_info_library):
    with patch('backend.controlers.model_control.LibraryControl') as mock_library_control, \
         patch('backend.controlers.model_control.SettingsService'):
        model_control = ModelControl()
        model_control.library_control = mock_library_control
        model_control.library_control.get_model_info_library.return_value = model_info_library
        yield model_control

def test_configure_model_success(mock_model_control):
    model_id = "test_model"
    config_data = {"key": "value"}
    configure_request = {
        "model_id": model_id,
        "data": config_data
    }
    
    mock_model_control.library_control.update_model_config.return_value = True
    mock_model_control.is_model_loaded = Mock(return_value=False)
    
    result = mock_model_control.configure_model(configure_request)
    
    assert result == {"message": f"Model {model_id} configuration updated in library"}
    mock_model_control.library_control.update_model_config.assert_called_once_with(model_id, config_data)

def test_configure_model_loaded(mock_model_control):
    model_id = "test_model"
    config_data = {"key": "value"}
    configure_request = {
        "model_id": model_id,
        "data": config_data
    }
    
    mock_model_control.library_control.update_model_config.return_value = True
    mock_model_control.is_model_loaded = Mock(return_value=True)
    mock_model_control.unload_model = Mock()
    mock_model_control.load_model = Mock()
    
    result = mock_model_control.configure_model(configure_request)
    
    assert result == {"message": f"Model {model_id} configuration updated in library"}
    mock_model_control.unload_model.assert_called_once_with(model_id)
    mock_model_control.load_model.assert_called_once_with(model_id)

def test_configure_model_update_failed(mock_model_control):
    model_id = "test_model"
    config_data = {"key": "value"}
    configure_request = {
        "model_id": model_id,
        "data": config_data
    }
    
    mock_model_control.library_control.update_model_config.return_value = False
    
    result = mock_model_control.configure_model(configure_request)
    
    assert result == {"error": f"Failed to update configuration for model {model_id}"}

def test_configure_model_not_found(mock_model_control):
    model_id = "nonexistent_model"
    configure_request = {
        "model_id": model_id,
        "data": {}
    }
    
    mock_model_control.library_control.update_model_config.side_effect = KeyError(model_id)
    
    result = mock_model_control.configure_model(configure_request)
    
    assert result == {"error": f"Model {model_id} not found in library"}

def test_reset_model_config_success(mock_model_control):
    model_id = "test_model"
    
    mock_model_control.library_control.reset_model_config.return_value = True
    mock_model_control.is_model_loaded = Mock(return_value=False)
    
    result = mock_model_control.reset_model_config(model_id)
    
    assert result == {"message": f"Model {model_id} configuration reset in library"}
    mock_model_control.library_control.reset_model_config.assert_called_once_with(model_id)

def test_reset_model_config_loaded(mock_model_control):
    model_id = "test_model"
    
    mock_model_control.library_control.reset_model_config.return_value = True
    mock_model_control.is_model_loaded = Mock(return_value=True)
    mock_model_control.unload_model = Mock()
    mock_model_control.load_model = Mock()
    
    result = mock_model_control.reset_model_config(model_id)
    
    assert result == {"message": f"Model {model_id} configuration reset in library"}
    mock_model_control.unload_model.assert_called_once_with(model_id)
    mock_model_control.load_model.assert_called_once_with(model_id)

def test_reset_model_config_not_found(mock_model_control):
    model_id = "nonexistent_model"
    
    mock_model_control.library_control.reset_model_config.side_effect = KeyError(model_id)
    
    result = mock_model_control.reset_model_config(model_id)
    
    assert result == {"error": f"Model {model_id} not found in library"}

@patch('backend.controlers.model_control.logger')
def test_configure_model_logging(mock_logger, mock_model_control):
    model_id = "test_model"
    configure_request = {
        "model_id": model_id,
        "data": {"key": "value"}
    }
    
    mock_model_control.library_control.update_model_config.return_value = True
    mock_model_control.is_model_loaded = Mock(return_value=False)
    
    mock_model_control.configure_model(configure_request)
    
    mock_logger.error.assert_not_called()

@patch('backend.controlers.model_control.logger')
def test_reset_model_config_logging(mock_logger, mock_model_control):
    model_id = "test_model"
    
    mock_model_control.library_control.reset_model_config.return_value = True
    mock_model_control.is_model_loaded = Mock(return_value=False)
    
    mock_model_control.reset_model_config(model_id)
    
    mock_logger.error.assert_not_called()