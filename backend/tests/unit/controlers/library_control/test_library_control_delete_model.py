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
            "config": {"param1": "value1"},
            "is_customised": False
        },
        "model2": {
            "base_model": "base_model2",
            "config": {"param2": "value2"},
            "is_customised": True
        }
    }

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_delete_model_existing(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        result = mock_library_control.delete_model(model_id)

    assert result == {"message": f"Model {model_id} deleted from library."}
    mock_read_json.assert_called_once()
    mock_write_json.assert_called_once()
    updated_library = mock_write_json.call_args[0][1]
    assert model_id not in updated_library

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_delete_model_non_existing(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "non_existing_model"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=None):
        result = mock_library_control.delete_model(model_id)

    assert result == {"message": f"Model {model_id} does not exist in library."}
    mock_read_json.assert_not_called()
    mock_write_json.assert_not_called()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_delete_model_file_read_error(mock_write_json, mock_read_json, mock_library_control):
    mock_read_json.side_effect = FileReadError("Error reading file")

    with patch.object(mock_library_control, 'get_model_info_library', side_effect=FileReadError("Error reading file")):
        with pytest.raises(FileReadError, match="Error reading file"):
            mock_library_control.delete_model("model1")

    mock_read_json.assert_not_called()
    mock_write_json.assert_not_called()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_delete_model_file_write_error(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    mock_write_json.side_effect = FileWriteError("Error writing file")
    model_id = "model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        with pytest.raises(FileWriteError, match="Error writing file"):
            mock_library_control.delete_model(model_id)

    mock_read_json.assert_called_once()
    mock_write_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
@patch('backend.controlers.library_control.logger')
def test_delete_model_logging(mock_logger, mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "model1"

    with patch.object(mock_library_control, 'get_model_info_library', return_value=mock_library[model_id]):
        mock_library_control.delete_model(model_id)

    mock_logger.info.assert_called_with(f"Model {model_id} deleted from library.")