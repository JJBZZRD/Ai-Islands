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
        },
        "model2": {
            "base_model": "base_model2",
            "config": {"param3": "value3", "param4": "value4"},
            "is_customised": True
        }
    }

@pytest.fixture
def mock_index():
    return {
        "base_model1": {
            "config": {"param1": "value1", "param2": "value2"}
        },
        "base_model2": {
            "config": {"param3": "default3", "param4": "default4"}
        }
    }

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_model_config_existing_model(mock_write_json, mock_read_json, mock_library_control, mock_library, mock_index):
    mock_read_json.return_value = mock_library
    model_id = "model1"
    new_config = {"param1": "new_value1", "param3": "new_value3"}

    with patch.object(mock_library_control, 'get_model_info_index', return_value=mock_index["base_model1"]):
        result = mock_library_control.update_model_config(model_id, new_config)

    assert result == {"param1": "new_value1", "param2": "value2", "param3": "new_value3"}
    assert mock_library[model_id]["is_customised"] == True
    mock_read_json.assert_called_once()
    mock_write_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_model_config_reset_to_default(mock_write_json, mock_read_json, mock_library_control, mock_library, mock_index):
    mock_read_json.return_value = mock_library
    model_id = "model2"
    new_config = {"param3": "default3", "param4": "default4"}

    with patch.object(mock_library_control, 'get_model_info_index', return_value=mock_index["base_model2"]):
        result = mock_library_control.update_model_config(model_id, new_config)

    assert result == new_config
    assert mock_library[model_id]["is_customised"] == False
    mock_read_json.assert_called_once()
    mock_write_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_model_config_non_existing_model(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "non_existing_model"
    new_config = {"param": "value"}

    with pytest.raises(KeyError, match=f"Model {model_id} not found in library"):
        mock_library_control.update_model_config(model_id, new_config)

    mock_read_json.assert_called_once()
    mock_write_json.assert_not_called()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_model_config_file_read_error(mock_write_json, mock_read_json, mock_library_control):
    mock_read_json.side_effect = FileReadError("Error reading file")
    model_id = "model1"
    new_config = {"param": "value"}

    with pytest.raises(FileReadError, match="Error reading file"):
        mock_library_control.update_model_config(model_id, new_config)

    mock_read_json.assert_called_once()
    mock_write_json.assert_not_called()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_model_config_file_write_error(mock_write_json, mock_read_json, mock_library_control, mock_library, mock_index):
    mock_read_json.return_value = mock_library
    mock_write_json.side_effect = FileWriteError("Error writing file")
    model_id = "model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_index', return_value=mock_index["base_model1"]):
        with pytest.raises(FileWriteError, match="Error writing file"):
            mock_library_control.update_model_config(model_id, new_config)

    mock_read_json.assert_called_once()
    mock_write_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
@patch('backend.controlers.library_control.logger')
def test_update_model_config_logging(mock_logger, mock_write_json, mock_read_json, mock_library_control, mock_library, mock_index):
    mock_read_json.return_value = mock_library
    model_id = "model1"
    new_config = {"param1": "new_value1"}

    with patch.object(mock_library_control, 'get_model_info_index', return_value=mock_index["base_model1"]):
        mock_library_control.update_model_config(model_id, new_config)

    mock_logger.info.assert_called_with(f"Configuration updated for model {model_id}")

# New tests for reset_model_config
def test_reset_model_config_success(mock_library_control, mock_library, mock_index):
    with patch('backend.controlers.library_control.JSONHandler.read_json') as mock_read_json:
        with patch('backend.controlers.library_control.JSONHandler.write_json') as mock_write_json:
            mock_read_json.side_effect = [mock_library, mock_index, mock_library]
            
            result = mock_library_control.reset_model_config("model2")
            
            assert result == {"param3": "default3", "param4": "default4"}
            assert mock_library["model2"]["config"] == {"param3": "default3", "param4": "default4"}
            assert mock_library["model2"]["is_customised"] == False
            mock_write_json.assert_called_once()

def test_reset_model_config_model_not_found(mock_library_control):
    with patch.object(mock_library_control, 'get_model_info_library', return_value=None):
        result = mock_library_control.reset_model_config("non_existing_model")
        assert result is None

def test_reset_model_config_base_model_not_found(mock_library_control, mock_library):
    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library["model1"]):
        with patch.object(mock_library_control, 'get_model_info_index', return_value=None):
            result = mock_library_control.reset_model_config("model1")
            assert result is None

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_reset_model_config_file_read_error(mock_read_json, mock_library_control):
    mock_read_json.side_effect = FileReadError("Error reading file")
    with pytest.raises(FileReadError, match="Error reading file"):
        mock_library_control.reset_model_config("model1")

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_reset_model_config_file_write_error(mock_write_json, mock_read_json, mock_library_control, mock_library, mock_index):
    mock_read_json.side_effect = [mock_library, mock_index, mock_library]
    mock_write_json.side_effect = FileWriteError("Error writing file")
    with pytest.raises(FileWriteError, match="Error writing file"):
        mock_library_control.reset_model_config("model1")

@patch('backend.controlers.library_control.logger')
def test_reset_model_config_logging(mock_logger, mock_library_control, mock_library, mock_index):
    with patch('backend.controlers.library_control.JSONHandler.read_json') as mock_read_json:
        with patch('backend.controlers.library_control.JSONHandler.write_json'):
            mock_read_json.side_effect = [mock_library, mock_index, mock_library]
            
            mock_library_control.reset_model_config("model1")
            
            mock_logger.info.assert_any_call("Attempting to reset configuration for model model1")
            mock_logger.info.assert_any_call("Configuration reset for model model1")


