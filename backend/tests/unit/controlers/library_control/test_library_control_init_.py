import pytest
from unittest.mock import patch, mock_open
from backend.controlers.library_control import LibraryControl
from backend.core.exceptions import FileReadError, FileWriteError
from backend.core.config import DOWNLOADED_MODELS_PATH

@pytest.fixture
def mock_library_control():
    return LibraryControl()

@patch('os.path.exists')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_initialise_library_new_file(mock_write_json, mock_exists, mock_library_control):
    mock_exists.return_value = False
    
    result = mock_library_control._initialise_library()
    
    assert result == True
    mock_write_json.assert_called_once_with(DOWNLOADED_MODELS_PATH, {})

@patch('os.path.exists')
@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_initialise_library_empty_file(mock_write_json, mock_read_json, mock_exists, mock_library_control):
    mock_exists.return_value = True
    mock_read_json.side_effect = FileReadError("Empty file")
    
    result = mock_library_control._initialise_library()
    
    assert result == True
    mock_write_json.assert_called_once_with(DOWNLOADED_MODELS_PATH, {})

@patch('os.path.exists')
@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_initialise_library_existing_file(mock_read_json, mock_exists, mock_library_control):
    mock_exists.return_value = True
    mock_read_json.return_value = {"existing": "data"}
    
    result = mock_library_control._initialise_library()
    
    assert result == True
    mock_read_json.assert_called_once()

@patch('os.path.exists')
@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_initialise_library_write_error(mock_write_json, mock_read_json, mock_exists, mock_library_control):
    mock_exists.return_value = True
    mock_read_json.side_effect = FileReadError("Empty file")
    mock_write_json.side_effect = FileWriteError("Write error")
    
    with pytest.raises(FileWriteError, match="Write error"):
        mock_library_control._initialise_library()

@patch('backend.controlers.library_control.logger')
@patch('os.path.exists')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_initialise_library_logging(mock_write_json, mock_exists, mock_logger, mock_library_control):
    mock_exists.return_value = False
    
    mock_library_control._initialise_library()
    
    mock_logger.info.assert_any_call(f"Creating new library at: {DOWNLOADED_MODELS_PATH}")
    mock_logger.info.assert_any_call("Library initialised successfully")