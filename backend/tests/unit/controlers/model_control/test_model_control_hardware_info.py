import pytest
from unittest.mock import Mock, patch
import psutil
import torch
import GPUtil
import subprocess
from backend.controlers.model_control import ModelControl

@pytest.fixture
def mock_model_control():
    with patch('backend.controlers.model_control.LibraryControl'), \
         patch('backend.controlers.model_control.SettingsService'):
        model_control = ModelControl()
        model_control.models = {
            "test_model": {
                "pid": 12345
            }
        }
        yield model_control

@patch('psutil.Process')
@patch('torch.cuda.is_available', return_value=False)
def test_get_model_hardware_usage_cpu_only(mock_cuda, mock_process, mock_model_control):
    mock_process.return_value.cpu_percent.return_value = 10
    mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100 MB
    mock_process.return_value.memory_percent.return_value = 5

    result = mock_model_control.get_model_hardware_usage("test_model")

    assert result == {
        'cpu_percent': 10,
        'memory_used_mb': 100,
        'memory_percent': 5,
        'gpu_memory_used_mb': None,
        'gpu_memory_percent': None,
        'gpu_utilization_percent': None
    }

@patch('psutil.Process')
@patch('torch.cuda.is_available', return_value=True)
@patch('GPUtil.getGPUs')
@patch('subprocess.run')
def test_get_model_hardware_usage_with_gpu(mock_subprocess, mock_gputil, mock_cuda, mock_process, mock_model_control):
    mock_process.return_value.cpu_percent.return_value = 10
    mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100 MB
    mock_process.return_value.memory_percent.return_value = 5

    mock_gpu = Mock()
    mock_gpu.memoryUsed = 1000
    mock_gpu.memoryTotal = 8000
    mock_gputil.return_value = [mock_gpu]

    mock_subprocess.side_effect = [
        Mock(stdout="50\n"),  # GPU utilization
        Mock(stdout="12345\n")  # PID using GPU
    ]

    result = mock_model_control.get_model_hardware_usage("test_model")

    assert result == {
        'cpu_percent': 10,
        'memory_used_mb': 100,
        'memory_percent': 5,
        'gpu_memory_used_mb': 1000,
        'gpu_memory_percent': 12.5,
        'gpu_utilization_percent': 50
    }

@patch('psutil.Process')
@patch('torch.cuda.is_available', return_value=True)
@patch('GPUtil.getGPUs')
def test_get_model_hardware_usage_no_gpus(mock_gputil, mock_cuda, mock_process, mock_model_control):
    mock_process.return_value.cpu_percent.return_value = 10
    mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100 MB
    mock_process.return_value.memory_percent.return_value = 5

    mock_gputil.return_value = []

    result = mock_model_control.get_model_hardware_usage("test_model")

    assert result == {
        'cpu_percent': 10,
        'memory_used_mb': 100,
        'memory_percent': 5,
        'gpu_memory_used_mb': None,
        'gpu_memory_percent': None,
        'gpu_utilization_percent': None
    }

@patch('psutil.Process', side_effect=psutil.NoSuchProcess(12345))
def test_get_model_hardware_usage_no_process(mock_process, mock_model_control):
    result = mock_model_control.get_model_hardware_usage("test_model")

    assert result is None

def test_get_model_hardware_usage_model_not_found(mock_model_control):
    result = mock_model_control.get_model_hardware_usage("nonexistent_model")

    assert result is None

@patch('psutil.Process')
@patch('torch.cuda.is_available', return_value=True)
@patch('GPUtil.getGPUs')
@patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'nvidia-smi'))
def test_get_model_hardware_usage_nvidia_smi_error(mock_subprocess, mock_gputil, mock_cuda, mock_process, mock_model_control):
    mock_process.return_value.cpu_percent.return_value = 10
    mock_process.return_value.memory_info.return_value.rss = 1024 * 1024 * 100  # 100 MB
    mock_process.return_value.memory_percent.return_value = 5

    mock_gpu = Mock()
    mock_gpu.memoryUsed = 1000
    mock_gpu.memoryTotal = 8000
    mock_gputil.return_value = [mock_gpu]

    result = mock_model_control.get_model_hardware_usage("test_model")

    assert result == {
        'cpu_percent': 10,
        'memory_used_mb': 100,
        'memory_percent': 5,
        'gpu_memory_used_mb': 1000,
        'gpu_memory_percent': 12.5,
        'gpu_utilization_percent': None
    }

@patch('backend.controlers.model_control.logger')
def test_get_model_hardware_usage_logging(mock_logger, mock_model_control):
    mock_model_control.get_model_hardware_usage("nonexistent_model")

    mock_logger.error.assert_called_with("Model nonexistent_model not found in active models.")