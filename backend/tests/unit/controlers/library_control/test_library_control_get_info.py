import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.library_control import LibraryControl
from backend.core.exceptions import FileReadError

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

@pytest.fixture
def mock_index():
    return {
        "base_model1": {
            "config": {"default_param1": "default_value1"},
            "other_info": "info1"
        },
        "base_model2": {
            "config": {"default_param2": "default_value2"},
            "other_info": "info2"
        }
    }

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_model_info_library_existing_model(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "model1"

    result = mock_library_control.get_model_info_library(model_id)

    assert result == mock_library[model_id]
    mock_read_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_model_info_library_non_existing_model(mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "non_existing_model"

    with pytest.raises(KeyError, match=f"Model info not found for {model_id}"):
        mock_library_control.get_model_info_library(model_id)

    mock_read_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_model_info_library_file_read_error(mock_read_json, mock_library_control):
    mock_read_json.side_effect = FileReadError("Error reading file")

    with pytest.raises(FileReadError, match="Error reading file"):
        mock_library_control.get_model_info_library("model1")

    mock_read_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_model_info_index_existing_model(mock_read_json, mock_library_control, mock_index):
    mock_read_json.return_value = mock_index
    model_id = "base_model1"

    result = mock_library_control.get_model_info_index(model_id)

    assert result == mock_index[model_id]
    mock_read_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_model_info_index_non_existing_model(mock_read_json, mock_library_control, mock_index):
    mock_read_json.return_value = mock_index
    model_id = "non_existing_model"

    with pytest.raises(KeyError, match=f"Model info not found for {model_id}"):
        mock_library_control.get_model_info_index(model_id)

    mock_read_json.assert_called_once()

@patch('backend.controlers.library_control.JSONHandler.read_json')
def test_get_model_info_index_file_read_error(mock_read_json, mock_library_control):
    mock_read_json.side_effect = FileReadError("Error reading file")

    with pytest.raises(FileReadError, match="Error reading file"):
        mock_library_control.get_model_info_index("base_model1")

    mock_read_json.assert_called_once()