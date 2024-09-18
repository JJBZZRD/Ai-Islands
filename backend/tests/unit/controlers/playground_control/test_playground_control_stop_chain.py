import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.playground_control import PlaygroundControl
from backend.playground.playground import Playground
from backend.core.exceptions import FileReadError, FileWriteError, ModelError

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
        }
        pc.playgrounds["test_playground"].chain = ["model1", "model2"]
        pc.playgrounds["test_playground"].active_chain = True
        return pc

@patch('backend.controlers.playground_control.RuntimeControl')
def test_stop_playground_chain_success(mock_runtime_control, playground_control):
    mock_runtime_control.get_runtime_data.return_value = {
        "model1": ["test_playground"],
        "model2": ["test_playground"]
    }
    
    result = playground_control.stop_playground_chain("test_playground")
    
    assert result == True
    assert playground_control.playgrounds["test_playground"].active_chain == False
    playground_control.model_control.unload_model.assert_any_call("model1")
    playground_control.model_control.unload_model.assert_any_call("model2")
    mock_runtime_control.update_runtime_data.assert_called_once()

def test_stop_playground_chain_nonexistent_playground(playground_control):
    with pytest.raises(KeyError, match="Playground nonexistent_playground not found"):
        playground_control.stop_playground_chain("nonexistent_playground")

@patch('backend.controlers.playground_control.RuntimeControl')
def test_stop_playground_chain_runtime_read_error(mock_runtime_control, playground_control):
    mock_runtime_control.get_runtime_data.side_effect = FileReadError("Read error")
    
    with pytest.raises(FileReadError, match="Read error"):
        playground_control.stop_playground_chain("test_playground")

@patch('backend.controlers.playground_control.RuntimeControl')
def test_stop_playground_chain_runtime_write_error(mock_runtime_control, playground_control):
    mock_runtime_control.get_runtime_data.return_value = {
        "model1": ["test_playground"],
        "model2": ["test_playground"]
    }
    mock_runtime_control.update_runtime_data.side_effect = FileWriteError("Write error")
    
    with pytest.raises(FileWriteError, match="Write error"):
        playground_control.stop_playground_chain("test_playground")

@patch('backend.controlers.playground_control.RuntimeControl')
def test_stop_playground_chain_updates_runtime_data(mock_runtime_control, playground_control):
    mock_runtime_data = {
        "model1": ["test_playground", "other_playground"],
        "model2": ["test_playground"]
    }
    mock_runtime_control.get_runtime_data.return_value = mock_runtime_data
    
    playground_control.stop_playground_chain("test_playground")
    
    expected_runtime_data = {
        "model1": ["other_playground"]
    }
    mock_runtime_control.update_runtime_data.assert_called_once_with("playground", expected_runtime_data)

@patch('backend.controlers.playground_control.RuntimeControl')
def test_stop_playground_chain_model_unload_error(mock_runtime_control, playground_control):
    mock_runtime_control.get_runtime_data.return_value = {
        "model1": ["test_playground"],
        "model2": ["test_playground"]
    }
    playground_control.model_control.unload_model.side_effect = [None, ModelError("Unload error")]
    
    result = playground_control.stop_playground_chain("test_playground")
    
    assert result == True
    assert playground_control.playgrounds["test_playground"].active_chain == False

@patch('backend.controlers.playground_control.RuntimeControl')
@patch('backend.controlers.playground_control.logger')
def test_stop_playground_chain_logging(mock_logger, mock_runtime_control, playground_control):
    mock_runtime_control.get_runtime_data.return_value = {
        "model1": ["test_playground"],
        "model2": ["test_playground"]
    }
    
    playground_control.stop_playground_chain("test_playground")
    
    mock_logger.info.assert_any_call("Model model1 unloaded")
    mock_logger.info.assert_any_call("Model model2 unloaded")

@patch('backend.controlers.playground_control.RuntimeControl')
def test_stop_playground_chain_model_in_use(mock_runtime_control, playground_control):
    mock_runtime_control.get_runtime_data.return_value = {
        "model1": ["test_playground", "other_playground"],
        "model2": ["test_playground"]
    }
    
    playground_control.stop_playground_chain("test_playground")
    
    # Check that unload_model was called for both models
    playground_control.model_control.unload_model.assert_any_call("model1")
    playground_control.model_control.unload_model.assert_any_call("model2")
    
    # Check that unload_model was called exactly twice
    assert playground_control.model_control.unload_model.call_count == 2
    
    # Check that the playground's active_chain is set to False
    assert playground_control.playgrounds["test_playground"].active_chain == False
    
    # Check that the runtime data was updated correctly
    expected_runtime_data = {
        "model1": ["other_playground"]
    }
    mock_runtime_control.update_runtime_data.assert_called_once_with("playground", expected_runtime_data)