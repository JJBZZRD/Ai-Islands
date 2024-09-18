import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.library_control import LibraryControl
from backend.core.exceptions import FileReadError, FileWriteError

@pytest.fixture
def mock_library_control():
    return LibraryControl()

@pytest.fixture
def mock_library():
    return {
        "model1": {
            "base_model": "base_model1",
            "config": {"param1": "value1", "param2": "value2"},
            "is_customised": False
        }
    }

def test_save_new_model_success(mock_library_control, mock_library):
    model_id = "model1"
    new_model_id = "new_model1"
    new_config = {"param1": "new_value1", "param3": "new_value3"}

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        with patch.object(mock_library_control, 'update_library') as mock_update_library:
            with patch.object(mock_library_control, 'update_model_config', return_value=new_config):
                result = mock_library_control.save_new_model(model_id, new_model_id, new_config)

    assert result == new_model_id
    mock_update_library.assert_called_once_with(new_model_id, mock_library[model_id])

def test_save_new_model_existing_model_not_found(mock_library_control):
    model_id = "non_existing_model"
    new_model_id = "new_model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_library', return_value=None):
        result = mock_library_control.save_new_model(model_id, new_model_id, new_config)

    assert result is None

def test_save_new_model_update_config_failure(mock_library_control, mock_library):
    model_id = "model1"
    new_model_id = "new_model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        with patch.object(mock_library_control, 'update_library'):
            with patch.object(mock_library_control, 'update_model_config', return_value=None):
                result = mock_library_control.save_new_model(model_id, new_model_id, new_config)

    assert result is None

def test_save_new_model_file_read_error(mock_library_control):
    model_id = "model1"
    new_model_id = "new_model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_library', side_effect=FileReadError("Error reading file")):
        with pytest.raises(FileReadError, match="Error reading file"):
            mock_library_control.save_new_model(model_id, new_model_id, new_config)

def test_save_new_model_file_write_error(mock_library_control, mock_library):
    model_id = "model1"
    new_model_id = "new_model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        with patch.object(mock_library_control, 'update_library'):
            with patch.object(mock_library_control, 'update_model_config', side_effect=FileWriteError("Error writing file")):
                with pytest.raises(FileWriteError, match="Error writing file"):
                    mock_library_control.save_new_model(model_id, new_model_id, new_config)

@patch('backend.controlers.library_control.logger')
def test_save_new_model_logging(mock_logger, mock_library_control, mock_library):
    model_id = "model1"
    new_model_id = "new_model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        with patch.object(mock_library_control, 'update_library'):
            with patch.object(mock_library_control, 'update_model_config', return_value=new_config):
                mock_library_control.save_new_model(model_id, new_model_id, new_config)

    mock_logger.info.assert_any_call(f"Attempting to save new model {new_model_id} based on {model_id}")
    mock_logger.info.assert_any_call(f"New model {new_model_id} saved successfully")