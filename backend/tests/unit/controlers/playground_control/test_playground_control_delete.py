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
            "active_playground": Playground("active_playground", "Active playground")
        }
        pc.playgrounds["active_playground"].active_chain = True
        return pc

def test_delete_playground_success(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        result = playground_control.delete_playground("existing_playground")
    
    assert result is True
    assert "existing_playground" not in playground_control.playgrounds
    mock_write.assert_called_once()

def test_delete_playground_nonexistent(playground_control):
    with pytest.raises(KeyError, match="Playground nonexistent_playground does not exist."):
        playground_control.delete_playground("nonexistent_playground")

def test_delete_playground_active_chain(playground_control):
    with pytest.raises(PlaygroundError, match="Playground active_playground is running a chain, please stop it before deleting."):
        playground_control.delete_playground("active_playground")

def test_delete_playground_write_error(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError, match="Write error"):
            playground_control.delete_playground("existing_playground")

@patch('backend.controlers.playground_control.logger')
def test_delete_playground_write_error_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError):
            playground_control.delete_playground("existing_playground")
    
    mock_logger.error.assert_called_with("Error writing updated playground data to JSON file after playground deletion")

def test_delete_playground_removes_from_dict(playground_control):
    initial_count = len(playground_control.playgrounds)
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.delete_playground("existing_playground")
    
    assert len(playground_control.playgrounds) == initial_count - 1
    assert "existing_playground" not in playground_control.playgrounds

def test_delete_playground_does_not_affect_other_playgrounds(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.delete_playground("existing_playground")
    
    assert "active_playground" in playground_control.playgrounds