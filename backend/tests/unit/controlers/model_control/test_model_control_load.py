import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ModelError
import multiprocessing
import threading

@pytest.fixture
def mock_model_control():
    with patch('backend.controlers.model_control.LibraryControl') as mock_library_control, \
         patch('backend.controlers.model_control.SettingsService') as mock_settings_service:
        mock_settings_service().get_hardware_preference.return_value = 'cpu'
        yield ModelControl()

@pytest.fixture
def mock_torch():
    with patch('backend.controlers.model_control.torch') as mock_torch:
        mock_torch.cuda.is_available.return_value = False
        mock_torch.device.return_value = 'cpu'
        yield mock_torch

@pytest.fixture
def mock_model_class():
    return Mock()

@pytest.fixture
def mock_conn():
    return Mock()

@pytest.fixture
def mock_lock():
    return Mock()

def test_load_model_success(mock_model_control, model_info, mock_torch):
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control._get_model_class = Mock()
    mock_process = Mock()
    mock_process.start = Mock()
    mock_conn = Mock()
    mock_conn.recv.return_value = "Model loaded"

    with patch('multiprocessing.Process', return_value=mock_process), \
         patch('multiprocessing.Pipe', return_value=(mock_conn, Mock())):
        result = mock_model_control.load_model("Qwen/Qwen2-0.5B-Instruct")

    assert result is True
    assert "Qwen/Qwen2-0.5B-Instruct" in mock_model_control.models

def test_load_model_already_loaded(mock_model_control):
    mock_model_control.models = {"Qwen/Qwen2-0.5B-Instruct": {}}
    result = mock_model_control.load_model("Qwen/Qwen2-0.5B-Instruct")
    assert result is True

def test_load_model_file_not_found(mock_model_control, model_info):
    model_info['is_online'] = False
    model_info['dir'] = '/nonexistent/path'
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control._get_model_class = Mock()

    with pytest.raises(FileNotFoundError):
        mock_model_control.load_model("Qwen/Qwen2-0.5B-Instruct")

def test_load_model_error_response(mock_model_control, model_info, mock_torch):
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control._get_model_class = Mock()
    mock_process = Mock()
    mock_process.start = Mock()
    mock_conn = Mock()
    mock_conn.recv.return_value = {"error": "Failed to load model"}

    with patch('multiprocessing.Process', return_value=mock_process), \
         patch('multiprocessing.Pipe', return_value=(mock_conn, Mock())):
        with pytest.raises(ModelError):
            mock_model_control.load_model("Qwen/Qwen2-0.5B-Instruct")

def test_load_model_unexpected_response(mock_model_control, model_info, mock_torch):
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control._get_model_class = Mock()
    mock_process = Mock()
    mock_process.start = Mock()
    mock_conn = Mock()
    mock_conn.recv.return_value = "Unexpected response"

    with patch('multiprocessing.Process', return_value=mock_process), \
         patch('multiprocessing.Pipe', return_value=(mock_conn, Mock())):
        with pytest.raises(ModelError):
            mock_model_control.load_model("Qwen/Qwen2-0.5B-Instruct")

def test_load_model_value_error(mock_model_control):
    mock_model_control._get_model_info = Mock(side_effect=ValueError("Model info not found"))

    with pytest.raises(ValueError):
        mock_model_control.load_model("NonexistentModel")

# Tests for _load_process

def test_load_process_success(mock_model_class, mock_conn, mock_lock):
    model_id = "test_model"
    device = "cpu"
    model_info = {"some": "info"}
    
    mock_model_instance = Mock()
    mock_model_class.return_value = mock_model_instance
    
    mock_conn.recv.side_effect = ["terminate"]
    
    ModelControl._load_process(mock_model_class, mock_conn, model_id, device, model_info, mock_lock)
    
    mock_model_class.assert_called_once_with(model_id=model_id)
    mock_model_instance.load.assert_called_once_with(device=device, model_info=model_info)
    mock_conn.send.assert_any_call("Model loaded")

def test_load_process_load_error(mock_model_class, mock_conn, mock_lock):
    model_id = "test_model"
    device = "cpu"
    model_info = {"some": "info"}
    
    mock_model_instance = Mock()
    mock_model_class.return_value = mock_model_instance
    mock_model_instance.load.side_effect = Exception("Load error")
    
    ModelControl._load_process(mock_model_class, mock_conn, model_id, device, model_info, mock_lock)
    
    mock_conn.send.assert_called_with("error: Failed to load model test_model: Load error")

def test_load_process_inference(mock_model_class, mock_conn, mock_lock):
    model_id = "test_model"
    device = "cpu"
    model_info = {"some": "info"}
    
    mock_model_instance = Mock()
    mock_model_class.return_value = mock_model_instance
    mock_model_instance.inference.return_value = {"result": "inference_output"}
    
    mock_conn.recv.side_effect = [
        {"task": "inference", "data": "input_data"},
        "terminate"
    ]
    
    # Use a real threading.Lock() instead of a mock
    real_lock = threading.Lock()
    
    # Run _load_process in a separate thread
    thread = threading.Thread(target=ModelControl._load_process, 
                              args=(mock_model_class, mock_conn, model_id, device, model_info, real_lock))
    thread.start()
    thread.join(timeout=1)  # Wait for the thread to finish or timeout after 1 second
    
    mock_model_instance.inference.assert_called_once_with("input_data")
    mock_conn.send.assert_any_call({"result": "inference_output"})

def test_load_process_unknown_request(mock_model_class, mock_conn, mock_lock):
    model_id = "test_model"
    device = "cpu"
    model_info = {"some": "info"}
    
    mock_model_instance = Mock()
    mock_model_class.return_value = mock_model_instance
    
    mock_conn.recv.side_effect = [
        {"task": "unknown_task"},
        "terminate"
    ]
    
    ModelControl._load_process(mock_model_class, mock_conn, model_id, device, model_info, mock_lock)
    
    mock_conn.send.assert_any_call({"error": "Unknown request"})

def test_load_process_exception_handling(mock_model_class, mock_conn, mock_lock):
    model_id = "test_model"
    device = "cpu"
    model_info = {"some": "info"}
    
    mock_model_instance = Mock()
    mock_model_class.return_value = mock_model_instance
    mock_model_instance.inference.side_effect = Exception("Inference error")
    
    mock_conn.recv.side_effect = [
        {"task": "inference", "data": "input_data"},
        "terminate"
    ]
    
    # Use a real threading.Lock() instead of a mock
    real_lock = threading.Lock()
    
    # Run _load_process in a separate thread
    thread = threading.Thread(target=ModelControl._load_process, 
                              args=(mock_model_class, mock_conn, model_id, device, model_info, real_lock))
    thread.start()
    thread.join(timeout=1)  # Wait for the thread to finish or timeout after 1 second
    
    mock_conn.send.assert_any_call({"error": "Inference error"})

def test_load_process_termination(mock_model_class, mock_conn, mock_lock):
    model_id = "test_model"
    device = "cpu"
    model_info = {"some": "info"}
    
    mock_model_instance = Mock()
    mock_model_class.return_value = mock_model_instance
    
    mock_conn.recv.return_value = "terminate"
    
    ModelControl._load_process(mock_model_class, mock_conn, model_id, device, model_info, mock_lock)
    
    mock_conn.send.assert_called_with("Terminating")