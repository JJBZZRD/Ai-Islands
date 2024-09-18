import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.model_control import ModelControl
from backend.settings.settings_service import SettingsService
from backend.controlers.library_control import LibraryControl

@pytest.fixture
def mock_settings_service():
    with patch('backend.controlers.model_control.SettingsService') as mock:
        mock_instance = mock.return_value
        mock_instance.get_hardware_preference.return_value = 'CPU'
        yield mock_instance

@pytest.fixture
def mock_library_control():
    with patch('backend.controlers.model_control.LibraryControl', autospec=True) as mock:
        yield mock.return_value

def test_model_control_init(mock_settings_service, mock_library_control):
    model_control = ModelControl()
    
    assert isinstance(model_control.models, dict)
    assert model_control.models == {}
    assert model_control.hardware_preference == 'CPU'
    assert model_control.library_control is mock_library_control
    
    mock_settings_service.get_hardware_preference.assert_called_once()

@patch('backend.controlers.model_control.SettingsService')
def test_model_control_init_with_gpu_preference(mock_settings_service, mock_library_control):
    mock_settings_instance = mock_settings_service.return_value
    mock_settings_instance.get_hardware_preference.return_value = 'GPU'
    
    model_control = ModelControl()
    
    assert model_control.hardware_preference == 'GPU'
    mock_settings_instance.get_hardware_preference.assert_called_once()

@patch('backend.controlers.model_control.SettingsService', side_effect=Exception("Settings error"))
def test_model_control_init_settings_error(mock_settings_service, mock_library_control):
    with pytest.raises(Exception, match="Settings error"):
        ModelControl()

def test_model_control_init_empty_models(mock_settings_service, mock_library_control):
    model_control = ModelControl()
    assert len(model_control.models) == 0

@patch('backend.controlers.model_control.LibraryControl', side_effect=Exception("Library error"))
def test_model_control_init_library_error(mock_library_control, mock_settings_service):
    with pytest.raises(Exception, match="Library error"):
        ModelControl()