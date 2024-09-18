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

def test_update_model_id_success(mock_library_control, mock_library):
    old_model_id = "model1"
    new_model_id = "new_model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[old_model_id]):
        with patch.object(mock_library_control, 'update_library') as mock_update_library:
            with patch.object(mock_library_control, 'delete_model', return_value={"message": f"Model {old_model_id} deleted from library."}):
                result = mock_library_control.update_model_id(old_model_id, new_model_id)

    assert result == new_model_id
    mock_update_library.assert_called_once_with(new_model_id, mock_library[old_model_id])

def test_update_model_id_model_not_found(mock_library_control):
    old_model_id = "non_existing_model"
    new_model_id = "new_model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=None):
        result = mock_library_control.update_model_id(old_model_id, new_model_id)

    assert result is None

def test_update_model_id_delete_failure(mock_library_control, mock_library):
    old_model_id = "model1"
    new_model_id = "new_model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[old_model_id]):
        with patch.object(mock_library_control, 'update_library'):
            with patch.object(mock_library_control, 'delete_model', return_value=None):
                result = mock_library_control.update_model_id(old_model_id, new_model_id)

    assert result is None

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_update_model_id_file_read_error(mock_read_json, mock_library_control):
    mock_read_json.side_effect = FileReadError("Error reading file")
    old_model_id = "model1"
    new_model_id = "new_model1"

    with pytest.raises(FileReadError, match="Error reading file"):
        mock_library_control.update_model_id(old_model_id, new_model_id)

@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_model_id_file_write_error(mock_write_json, mock_library_control, mock_library):
    mock_write_json.side_effect = FileWriteError("Error writing file")
    old_model_id = "model1"
    new_model_id = "new_model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[old_model_id]):
        with patch.object(mock_library_control, 'update_library', side_effect=FileWriteError("Error writing file")):
            with pytest.raises(FileWriteError, match="Error writing file"):
                mock_library_control.update_model_id(old_model_id, new_model_id)

@patch('backend.controlers.library_control.logger')
def test_update_model_id_logging(mock_logger, mock_library_control, mock_library):
    old_model_id = "model1"
    new_model_id = "new_model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[old_model_id]):
        with patch.object(mock_library_control, 'update_library'):
            with patch.object(mock_library_control, 'delete_model', return_value={"message": f"Model {old_model_id} deleted from library."}):
                mock_library_control.update_model_id(old_model_id, new_model_id)

    mock_logger.info.assert_any_call(f"Attempting to update model ID from {old_model_id} to {new_model_id}")
    mock_logger.info.assert_any_call(f"Model ID updated from {old_model_id} to {new_model_id}")