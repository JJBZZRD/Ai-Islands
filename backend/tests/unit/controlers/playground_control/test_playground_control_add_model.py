import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.playground_control import PlaygroundControl
from backend.core.exceptions import FileWriteError, PlaygroundError
from backend.playground.playground import Playground

@pytest.fixture
def mock_model_control():
    return MagicMock()

@pytest.fixture
def mock_library_control():
    mock = MagicMock()
    mock.get_model_info_library.return_value = {
        "mapping": {"input": "text", "output": "text"},
        "pipeline_tag": "text-generation"
    }
    return mock

@pytest.fixture
def playground_control(mock_model_control, mock_library_control):
    with patch('backend.controlers.playground_control.LibraryControl', return_value=mock_library_control):
        pc = PlaygroundControl(mock_model_control)
        pc.playgrounds = {
            "existing_playground": Playground("existing_playground", "Test playground"),
        }
        return pc

def test_add_model_to_playground_success(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        result = playground_control.add_model_to_playground("existing_playground", "new_model")
    
    assert "new_model" in result["models"]
    assert result["models"]["new_model"]["pipeline_tag"] == "text-generation"
    assert result["models"]["new_model"]["is_online"] == False

def test_add_model_to_playground_nonexistent_playground(playground_control):
    with pytest.raises(KeyError, match="Playground nonexistent_playground not found"):
        playground_control.add_model_to_playground("nonexistent_playground", "new_model")

def test_add_model_to_playground_existing_model(playground_control):
    playground_control.playgrounds["existing_playground"].models = {"existing_model": {}}
    
    result = playground_control.add_model_to_playground("existing_playground", "existing_model")
    
    assert result["models"] == {"existing_model": {}}

def test_add_model_to_playground_model_not_in_library(playground_control, mock_library_control):
    mock_library_control.get_model_info_library.return_value = None
    
    with pytest.raises(KeyError, match="Model nonexistent_model not in library"):
        playground_control.add_model_to_playground("existing_playground", "nonexistent_model")

def test_add_model_to_playground_write_error(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError, match="Write error"):
            playground_control.add_model_to_playground("existing_playground", "new_model")

@patch('backend.controlers.playground_control.logger')
def test_add_model_to_playground_write_error_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError):
            playground_control.add_model_to_playground("existing_playground", "new_model")
    
    mock_logger.error.assert_called_with("Error writing updated playground data to JSON file after adding model")

def test_add_model_to_playground_return_structure(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        result = playground_control.add_model_to_playground("existing_playground", "new_model")
    
    assert set(result.keys()) == {"playground_id", "models"}
    assert result["playground_id"] == "existing_playground"
    assert isinstance(result["models"], dict)