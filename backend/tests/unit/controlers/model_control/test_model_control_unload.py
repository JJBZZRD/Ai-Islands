import pytest
from unittest.mock import Mock, patch
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ModelError

@pytest.fixture
def mock_model_control():
    with patch('backend.controlers.model_control.LibraryControl'), \
         patch('backend.controlers.model_control.SettingsService'):
        yield ModelControl()

@pytest.fixture
def mock_runtime_control():
    with patch('backend.controlers.model_control.RuntimeControl') as mock_runtime:
        yield mock_runtime

def test_unload_model_success(mock_model_control, mock_runtime_control):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_conn = Mock()
    mock_process = Mock()
    mock_model_control.models = {
        model_id: {
            'conn': mock_conn,
            'process': mock_process
        }
    }
    mock_runtime_control.get_runtime_data.return_value = {}

    result = mock_model_control.unload_model(model_id)

    assert result is True
    assert model_id not in mock_model_control.models
    mock_conn.send.assert_called_once_with("terminate")
    mock_process.join.assert_called_once()

def test_unload_model_active_in_chain(mock_model_control, mock_runtime_control):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_model_control.models = {model_id: {}}
    mock_runtime_control.get_runtime_data.return_value = {model_id: ["active_chain"]}

    with pytest.raises(ModelError, match=f"Model {model_id} is active in a chain. Please stop the chain first."):
        mock_model_control.unload_model(model_id)

def test_unload_model_not_found(mock_model_control):
    model_id = "NonexistentModel"

    result = mock_model_control.unload_model(model_id)

    assert isinstance(result, KeyError)
    assert str(result) == f"'Model {model_id} not found in active models.'"

@patch('backend.controlers.model_control.gc')
def test_unload_model_garbage_collection(mock_gc, mock_model_control, mock_runtime_control):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_model_control.models = {
        model_id: {
            'conn': Mock(),
            'process': Mock()
        }
    }
    mock_runtime_control.get_runtime_data.return_value = {}

    mock_model_control.unload_model(model_id)

    mock_gc.collect.assert_called_once()

@patch('backend.controlers.model_control.logger')
def test_unload_model_logging(mock_logger, mock_model_control, mock_runtime_control):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_model_control.models = {
        model_id: {
            'conn': Mock(),
            'process': Mock()
        }
    }
    mock_runtime_control.get_runtime_data.return_value = {}

    mock_model_control.unload_model(model_id)

    mock_logger.info.assert_called_with(f"Model {model_id} unloaded and memory freed.")

def test_unload_model_multiple_models(mock_model_control, mock_runtime_control):
    model_id1 = "Qwen/Qwen2-0.5B-Instruct"
    model_id2 = "AnotherModel"
    mock_conn1 = Mock()
    mock_process1 = Mock()
    mock_conn2 = Mock()
    mock_process2 = Mock()
    mock_model_control.models = {
        model_id1: {
            'conn': mock_conn1,
            'process': mock_process1
        },
        model_id2: {
            'conn': mock_conn2,
            'process': mock_process2
        }
    }
    mock_runtime_control.get_runtime_data.return_value = {}

    result = mock_model_control.unload_model(model_id1)

    assert result is True
    assert model_id1 not in mock_model_control.models
    assert model_id2 in mock_model_control.models
    mock_conn1.send.assert_called_once_with("terminate")
    mock_process1.join.assert_called_once()
    assert not mock_conn2.send.called
    assert not mock_process2.join.called