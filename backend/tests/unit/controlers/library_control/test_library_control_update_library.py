import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.library_control import LibraryControl

@pytest.fixture
def mock_library_control():
    return LibraryControl()

@pytest.fixture
def mock_library():
    return {
        "Qwen/Qwen2-0.5B-Instruct": {
            "is_online": False,
            "model_source": "transformers",
            "model_class": "TransformerModel",
            "mapping": {
                "input": "text",
                "output": "text"
            },
            "tags": ["transformers", "pytorch", "text-generation"],
            "pipeline_tag": "text-generation",
            "config": {
                "chat_history": False,
                "model_config": {
                    "torch_dtype": "auto"
                },
                "pipeline_config": {
                    "max_length": 512,
                    "temperature": 0.6
                }
            },
            "auth_token": None,
            "base_model": "Qwen/Qwen2-0.5B-Instruct",
            "dir": "data\\downloads\\transformers\\Qwen/Qwen2-0.5B-Instruct",
            "is_customised": False
        }
    }

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_library_existing_model(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    updates = {
        "is_online": True,
        "config": {
            "pipeline_config": {
                "temperature": 0.7
            }
        }
    }

    mock_library_control.update_library(model_id, updates)

    mock_write_json.assert_called_once()
    updated_library = mock_write_json.call_args[0][1]
    assert updated_library[model_id]["is_online"] is True
    assert updated_library[model_id]["config"]["pipeline_config"]["temperature"] == 0.7

    # Check if max_length is present in the original configuration
    original_max_length = mock_library[model_id]["config"]["pipeline_config"].get("max_length")
    if original_max_length is not None:
        assert updated_library[model_id]["config"]["pipeline_config"]["max_length"] == original_max_length
    else:
        assert "max_length" not in updated_library[model_id]["config"]["pipeline_config"]

    # Check if is_customised is present in the original configuration
    if "is_customised" in mock_library[model_id]:
        assert updated_library[model_id]["is_customised"] == mock_library[model_id]["is_customised"]
    else:
        assert "is_customised" not in updated_library[model_id]

    # Additional checks to verify other fields remain unchanged
    for key in mock_library[model_id]:
        if key not in updates and key != "config":
            assert updated_library[model_id][key] == mock_library[model_id][key]

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_library_new_model(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "new_model"
    updates = {
        "is_online": True,
        "model_source": "custom",
        "model_class": "CustomModel",
        "mapping": {
            "input": "text",
            "output": "text"
        },
        "tags": ["custom", "text-generation"],
        "pipeline_tag": "text-generation",
        "config": {
            "chat_history": True
        },
        "base_model": "new_model",
        "dir": "data\\downloads\\custom\\new_model"
    }

    mock_library_control.update_library(model_id, updates)

    mock_write_json.assert_called_once()
    updated_library = mock_write_json.call_args[0][1]
    assert model_id in updated_library
    assert updated_library[model_id] == updates
    assert "is_customised" not in updated_library[model_id]

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_library_invalid_update(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    updates = {
        "invalid_key": "invalid_value"
    }

    mock_library_control.update_library(model_id, updates)

    mock_write_json.assert_called_once()
    updated_library = mock_write_json.call_args[0][1]
    assert "invalid_key" in updated_library[model_id]

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
def test_update_library_nested_config(mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    updates = {
        "config": {
            "new_nested_config": {
                "key1": "value1",
                "key2": "value2"
            }
        }
    }

    mock_library_control.update_library(model_id, updates)

    mock_write_json.assert_called_once()
    updated_library = mock_write_json.call_args[0][1]
    assert "new_nested_config" in updated_library[model_id]["config"]
    assert updated_library[model_id]["config"]["new_nested_config"]["key1"] == "value1"
    assert updated_library[model_id]["config"]["new_nested_config"]["key2"] == "value2"

@patch('backend.controlers.library_control.JSONHandler.read_json')
@patch('backend.controlers.library_control.JSONHandler.write_json')
@patch('backend.controlers.library_control.logger')
def test_update_library_logging(mock_logger, mock_write_json, mock_read_json, mock_library_control, mock_library):
    mock_read_json.return_value = mock_library
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    updates = {
        "is_online": True
    }

    mock_library_control.update_library(model_id, updates)

    mock_logger.info.assert_called_with(f"Library updated with new entry: {updates}")
    mock_logger.debug.assert_any_call(f"Model {model_id} found in library, updating entry")