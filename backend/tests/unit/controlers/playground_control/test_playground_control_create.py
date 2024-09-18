import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.playground_control import PlaygroundControl
from backend.core.exceptions import PlaygroundAlreadyExistsError, FileWriteError
from backend.playground.playground import Playground

@pytest.fixture
def mock_model_control():
    return MagicMock()

@pytest.fixture
def playground_control(mock_model_control):
    with patch('backend.controlers.playground_control.LibraryControl'):
        return PlaygroundControl(mock_model_control)

def test_create_playground_success(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        # Use a unique playground ID that doesn't exist yet
        unique_id = "new_test_playground"
        result = playground_control.create_playground(unique_id, "Test description")
        
    assert result["playground_id"] == unique_id
    assert isinstance(result["playground"], dict)
    assert result["playground"]["description"] == "Test description"
    assert result["playground"]["models"] == {}
    assert result["playground"]["chain"] == []
    assert result["playground"]["active_chain"] == False
    mock_write.assert_called_once()

    # Verify that the playground was added to the PlaygroundControl instance
    assert unique_id in playground_control.playgrounds
    assert isinstance(playground_control.playgrounds[unique_id], Playground)

def test_create_playground_no_id(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        result = playground_control.create_playground(description="Auto-generated ID")
        
    assert result["playground_id"].startswith("new_playground_")
    assert result["playground"]["description"] == "Auto-generated ID"

def test_create_playground_already_exists(playground_control):
    # First, create a playground
    existing_id = "existing_playground"
    playground_control.create_playground(existing_id, "Existing playground")

    # Now try to create a playground with the same ID
    with pytest.raises(PlaygroundAlreadyExistsError, match=f"Playground with ID {existing_id} already exists"):
        playground_control.create_playground(existing_id, "This should fail")

def test_create_playground_write_error(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError):
            playground_control.create_playground("error_playground")

@patch('backend.controlers.playground_control.logger')
def test_create_playground_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.create_playground("logged_playground")
    
    mock_logger.info.assert_called_with("Created new playground with ID: logged_playground")

def test_create_playground_in_memory(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.create_playground("memory_playground")
    
    assert "memory_playground" in playground_control.playgrounds
    assert isinstance(playground_control.playgrounds["memory_playground"], Playground)

def test_create_playground_return_structure(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        result = playground_control.create_playground("structure_test")
    
    assert set(result.keys()) == {"playground_id", "playground"}
    assert set(result["playground"].keys()) == {"description", "models", "chain", "active_chain"}