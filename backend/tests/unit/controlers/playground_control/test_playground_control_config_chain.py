import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.playground_control import PlaygroundControl
from backend.playground.playground import Playground
from backend.core.exceptions import PlaygroundError, ChainNotCompatibleError, FileWriteError

@pytest.fixture
def mock_model_control():
    return MagicMock()

@pytest.fixture
def playground_control(mock_model_control):
    with patch('backend.controlers.playground_control.LibraryControl'):
        pc = PlaygroundControl(mock_model_control)
        pc.playgrounds = {
            "test_playground": Playground("test_playground", "Test playground"),
        }
        pc.playgrounds["test_playground"].models = {
            "model1": {"input": "text", "output": "text"},
            "model2": {"input": "text", "output": "text"},
            "model3": {"input": "image", "output": "text"},
            "model4": {"input": "text", "output": "image"}
        }
        return pc

def test_configure_chain_success(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        result = playground_control.configure_chain("test_playground", ["model1", "model2"])
    
    assert result == {"playground_id": "test_playground", "chain": ["model1", "model2"]}
    assert playground_control.playgrounds["test_playground"].chain == ["model1", "model2"]

def test_configure_chain_active_chain(playground_control):
    playground_control.playgrounds["test_playground"].active_chain = True
    
    with pytest.raises(PlaygroundError, match="Playground test_playground is already running a chain, please stop it before configuring."):
        playground_control.configure_chain("test_playground", ["model1", "model2"])

def test_configure_chain_nonexistent_model(playground_control):
    with pytest.raises(KeyError, match="Model nonexistent_model not found in playground test_playground"):
        playground_control.configure_chain("test_playground", ["model1", "nonexistent_model"])

def test_configure_chain_incompatible_models(playground_control):
    with pytest.raises(ChainNotCompatibleError, match="Model model3 is not a text to text model. All intermediate models in the chain must be text to text models."):
        playground_control.configure_chain("test_playground", ["model1", "model3", "model2"])

def test_configure_chain_incompatible_io(playground_control):
    with pytest.raises(ChainNotCompatibleError, match="Model model3 is not a text to text model. All intermediate models in the chain must be text to text models."):
        playground_control.configure_chain("test_playground", ["model1", "model3", "model2"])

def test_configure_chain_write_error(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json') as mock_write:
        mock_write.side_effect = FileWriteError("Write error")
        
        with pytest.raises(FileWriteError, match="Write error"):
            playground_control.configure_chain("test_playground", ["model1", "model2"])

@patch('backend.controlers.playground_control.logger')
def test_configure_chain_logging(mock_logger, playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.configure_chain("test_playground", ["model1", "model2"])
    
    mock_logger.error.assert_not_called()

def test_configure_chain_updates_playground(playground_control):
    with patch.object(playground_control, '_write_playgrounds_to_json'):
        playground_control.configure_chain("test_playground", ["model1", "model2"])
    
    assert playground_control.playgrounds["test_playground"].chain == ["model1", "model2"]

def test_configure_chain_nonexistent_playground(playground_control):
    with pytest.raises(KeyError):
        playground_control.configure_chain("nonexistent_playground", ["model1", "model2"])

def test_configure_chain_valid_non_text_to_text(playground_control):
    result = playground_control.configure_chain("test_playground", ["model3", "model2", "model4"])
    assert result == {"playground_id": "test_playground", "chain": ["model3", "model2", "model4"]}
    assert playground_control.playgrounds["test_playground"].chain == ["model3", "model2", "model4"]