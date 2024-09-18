import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.playground_control import PlaygroundControl
from backend.core.exceptions import FileWriteError, PlaygroundError
from backend.playground.playground import Playground

@pytest.fixture
def mock_model_control():
    return MagicMock()

@pytest.fixture
def playground_control(mock_model_control):
    with patch('backend.controlers.playground_control.LibraryControl'):
        pc = PlaygroundControl(mock_model_control)
        pc.playgrounds = {
            "existing_playground": Playground("existing_playground", "Test playground"),
        }
        pc.playgrounds["existing_playground"].models = {
            "existing_model": {"input": "text", "output": "text"},
            "chained_model": {"input": "text", "output": "text"}
        }
        pc.playgrounds["existing_playground"].chain = ["chained_model"]
        return pc

def test_remove_model_from_playground_success(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        result = playground_control.remove_model_from_playground("existing_playground", "existing_model")
    
    assert result is True
    assert "existing_model" not in playground_control.playgrounds["existing_playground"].models

def test_remove_model_from_playground_nonexistent_playground(playground_control):
    with pytest.raises(KeyError, match="Playground nonexistent_playground not found"):
        playground_control.remove_model_from_playground("nonexistent_playground", "existing_model")

def test_remove_model_from_playground_nonexistent_model(playground_control):
    result = playground_control.remove_model_from_playground("existing_playground", "nonexistent_model")
    assert result == {"playground_id": "existing_playground", "models": playground_control.playgrounds["existing_playground"].models}

def test_remove_model_from_playground_model_in_chain(playground_control):
    with pytest.raises(PlaygroundError, match="Model chained_model is in the chain of playground existing_playground. Please remove it from the chain before removing it from the playground."):
        playground_control.remove_model_from_playground("existing_playground", "chained_model")

def test_remove_model_from_playground_write_error(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError, match="Write error"):
            playground_control.remove_model_from_playground("existing_playground", "existing_model")

@patch('backend.controlers.playground_control.logger')
def test_remove_model_from_playground_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.remove_model_from_playground("existing_playground", "existing_model")
    
    mock_logger.info.assert_called_with("Removed model existing_model from playground existing_playground")

def test_remove_model_from_playground_updates_models(playground_control):
    initial_model_count = len(playground_control.playgrounds["existing_playground"].models)
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.remove_model_from_playground("existing_playground", "existing_model")
    
    assert len(playground_control.playgrounds["existing_playground"].models) == initial_model_count - 1

@patch('backend.controlers.playground_control.logger')
def test_remove_model_from_playground_write_error_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError):
            playground_control.remove_model_from_playground("existing_playground", "existing_model")
    
    mock_logger.error.assert_called_with("Error writing updated playground data to JSON file after removing model")