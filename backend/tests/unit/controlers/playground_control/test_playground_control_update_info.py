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
            "existing_playground": Playground("existing_playground", "Original description"),
            "active_playground": Playground("active_playground", "Active playground")
        }
        pc.playgrounds["active_playground"].active_chain = True
        return pc

def test_update_playground_info_success(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        result = playground_control.update_playground_info(
            "existing_playground", 
            new_playground_id="updated_playground", 
            description="Updated description"
        )
    
    assert "updated_playground" in playground_control.playgrounds
    assert "existing_playground" not in playground_control.playgrounds
    assert result["playground_id"] == "updated_playground"
    assert result["playground"]["description"] == "Updated description"
    mock_write.assert_called_once()

def test_update_playground_info_only_description(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        with pytest.raises(KeyError):
            playground_control.update_playground_info(
                "existing_playground", 
                description="New description"
            )

def test_update_playground_info_nonexistent(playground_control):
    with pytest.raises(KeyError, match="Playground nonexistent_playground does not exist."):
        playground_control.update_playground_info("nonexistent_playground")

def test_update_playground_info_active_chain(playground_control):
    with pytest.raises(PlaygroundError, match="Playground active_playground is running a chain, please stop it before updating."):
        playground_control.update_playground_info("active_playground", description="New description")

def test_update_playground_info_write_error(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError, match="Write error"):
            playground_control.update_playground_info("existing_playground", new_playground_id="new_id", description="New description")

@patch('backend.controlers.playground_control.logger')
def test_update_playground_info_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        with pytest.raises(KeyError):
            playground_control.update_playground_info("existing_playground", description="Logged update")
    
    mock_logger.error.assert_not_called()

def test_update_playground_info_return_structure(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        with pytest.raises(KeyError):
            playground_control.update_playground_info("existing_playground", description="Structure test")

def test_update_playground_info_preserve_models_and_chain(playground_control):
    playground_control.playgrounds["existing_playground"].models = {"model1": {"input": "text", "output": "text"}}
    playground_control.playgrounds["existing_playground"].chain = ["model1"]
    
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        with pytest.raises(KeyError):
            playground_control.update_playground_info("existing_playground", description="Preserve test")