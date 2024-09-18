import pytest
from unittest.mock import patch, MagicMock
from typing import Any  
from backend.controlers.model_control import ModelControl
from backend.core.exceptions import ModelError, ModelNotAvailableError
from multiprocessing.connection import Connection

@pytest.fixture
def model_control():
    with patch('backend.controlers.model_control.SettingsService') as mock_settings:
        mock_settings.return_value.get_hardware_preference.return_value = "cpu"
        return ModelControl()

@patch('backend.controlers.model_control.execute_script')
@patch('backend.controlers.model_control.RuntimeControl')
def test_download_model_success(mock_runtime_control, mock_execute_script, model_control):
    # Arrange
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_runtime_control.get_runtime_data.return_value = {"success": "Model downloaded successfully"}
    
    # Act
    result = model_control.download_model(model_id)
    
    # Assert
    mock_execute_script.assert_called_once_with("backend/utils/model_download.py", model_id)
    mock_runtime_control.get_runtime_data.assert_called_once_with("download_log")
    assert result == {"message": "Model downloaded successfully"}

@patch('backend.controlers.model_control.execute_script')
@patch('backend.controlers.model_control.RuntimeControl')
def test_download_model_with_auth_token(mock_runtime_control, mock_execute_script, model_control):
    # Arrange
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    auth_token = "test_token"
    mock_runtime_control.get_runtime_data.return_value = {"success": "Model downloaded successfully"}
    
    # Act
    result = model_control.download_model(model_id, auth_token)
    
    # Assert
    mock_execute_script.assert_called_once_with("backend/utils/model_download.py", model_id, "-at", auth_token)
    mock_runtime_control.get_runtime_data.assert_called_once_with("download_log")
    assert result == {"message": "Model downloaded successfully"}

@patch('backend.controlers.model_control.execute_script')
@patch('backend.controlers.model_control.RuntimeControl')
def test_download_model_error(mock_runtime_control, mock_execute_script, model_control):
    # Arrange
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_runtime_control.get_runtime_data.return_value = {
        "error": {
            "error name": "DownloadError",
            "error message": "Failed to download model"
        }
    }
    
    # Act & Assert
    with pytest.raises(ModelError, match="Error: Failed to download model"):
        model_control.download_model(model_id)
    
    mock_execute_script.assert_called_once_with("backend/utils/model_download.py", model_id)
    mock_runtime_control.get_runtime_data.assert_called_once_with("download_log")

@patch('backend.controlers.model_control.execute_script')
@patch('backend.controlers.model_control.RuntimeControl')
def test_download_model_unexpected_error(mock_runtime_control, mock_execute_script, model_control):
    # Arrange
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_runtime_control.get_runtime_data.return_value = {"error": "Unexpected error"}
    
    # Act & Assert
    with pytest.raises(ModelError, match="Unexpected Error occured during model download"):
        model_control.download_model(model_id)
    
    mock_execute_script.assert_called_once_with("backend/utils/model_download.py", model_id)
    mock_runtime_control.get_runtime_data.assert_called_once_with("download_log")

@patch('backend.controlers.model_control.install_packages')
@patch('backend.controlers.model_control.multiprocessing.Process')
@patch('backend.controlers.model_control.multiprocessing.Pipe')
def test_download_model_success_internal(mock_pipe, mock_process, mock_install_packages, model_control):
    # Arrange
    model_id = "test_model"
    mock_model_info = {"requirements": {"required_packages": []}}
    mock_model_class = MagicMock()
    mock_child_conn = MagicMock()
    mock_parent_conn = MagicMock()
    mock_pipe.return_value = (mock_parent_conn, mock_child_conn)
    mock_parent_conn.recv.return_value = "success"
    model_control._get_model_info = MagicMock(return_value=mock_model_info)
    model_control._get_model_class = MagicMock(return_value=mock_model_class)
    model_control.library_control.get_model_info_library = MagicMock(return_value={"some": "info"})

    # Act
    result = model_control._download_model(model_id)

    # Assert
    assert result == {"message": f"Model {model_id} downloaded successfully"}
    mock_install_packages.assert_called_once_with([])
    mock_process.assert_called_once()
    mock_pipe.assert_called_once()

@patch('backend.controlers.model_control.install_packages')
@patch('backend.controlers.model_control.multiprocessing.Process')
@patch('backend.controlers.model_control.multiprocessing.Pipe')
def test_download_model_error_internal(mock_pipe, mock_process, mock_install_packages, model_control):
    # Arrange
    model_id = "test_model"
    mock_model_info = {"requirements": {"required_packages": []}}
    mock_model_class = MagicMock()
    mock_child_conn = MagicMock()
    mock_parent_conn = MagicMock()
    mock_pipe.return_value = (mock_parent_conn, mock_child_conn)
    mock_parent_conn.recv.return_value = {"error": ModelError("Download failed")}
    model_control._get_model_info = MagicMock(return_value=mock_model_info)
    model_control._get_model_class = MagicMock(return_value=mock_model_class)
    model_control.library_control.get_model_info_library = MagicMock(return_value=None)

    # Act & Assert
    with pytest.raises(ModelError, match="Download failed"):
        model_control._download_model(model_id)

@patch('backend.controlers.model_control.install_packages')
@patch('backend.controlers.model_control.multiprocessing.Process')
@patch('backend.controlers.model_control.multiprocessing.Pipe')
def test_download_model_not_available_error_internal(mock_pipe, mock_process, mock_install_packages, model_control):
    # Arrange
    model_id = "test_model"
    mock_model_info = {"requirements": {"required_packages": []}}
    mock_model_class = MagicMock()
    mock_child_conn = MagicMock()
    mock_parent_conn = MagicMock()
    mock_pipe.return_value = (mock_parent_conn, mock_child_conn)
    mock_parent_conn.recv.return_value = {"error": ModelNotAvailableError("Model not available")}
    model_control._get_model_info = MagicMock(return_value=mock_model_info)
    model_control._get_model_class = MagicMock(return_value=mock_model_class)
    model_control.library_control.get_model_info_library = MagicMock(return_value=None)

    # Act & Assert
    with pytest.raises(ModelNotAvailableError, match="Model test_model is currently not available in the repository. Please try again later."):
        model_control._download_model(model_id)

def test_download_process_success():
    # Arrange
    conn = MagicMock()
    conn.send = MagicMock()  # Add send method to the mock
    model_class = MagicMock()
    model_id = "test_model"
    model_info = {"some": "info"}
    library_control = MagicMock()
    
    model_class.download.return_value = {"new": "entry"}
    
    # Act
    ModelControl._download_process(conn, model_class, model_id, model_info, library_control)
    
    # Assert
    model_class.download.assert_called_once_with(model_id, model_info)
    library_control.update_library.assert_called_once_with(model_id, {"new": "entry"})
    conn.send.assert_called_once_with("success")

def test_download_process_model_error():
    # Arrange
    conn = MagicMock()
    conn.send = MagicMock()  # Add send method to the mock
    model_class = MagicMock()
    model_id = "test_model"
    model_info = {"some": "info"}
    library_control = MagicMock()
    
    model_error = ModelError("Download failed")
    model_class.download.side_effect = model_error
    
    # Act
    ModelControl._download_process(conn, model_class, model_id, model_info, library_control)
    
    # Assert
    model_class.download.assert_called_once_with(model_id, model_info)
    library_control.update_library.assert_not_called()
    conn.send.assert_called_once_with({"error": model_error})

def test_download_process_unexpected_error():
    # Arrange
    conn = MagicMock()
    model_class = MagicMock()
    model_id = "test_model"
    model_info = {"some": "info"}
    library_control = MagicMock()

    unexpected_error = Exception("Unexpected error")
    model_class.download.side_effect = unexpected_error

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        ModelControl._download_process(conn, model_class, model_id, model_info, library_control)

    assert str(exc_info.value) == "Unexpected error"
    model_class.download.assert_called_once_with(model_id, model_info)
    library_control.update_library.assert_not_called()
    conn.send.assert_not_called()

def test_download_process_library_update_error():
    # Arrange
    conn = MagicMock()
    model_class = MagicMock()
    model_id = "test_model"
    model_info = {"some": "info"}
    library_control = MagicMock()

    model_class.download.return_value = {"new": "entry"}
    update_error = Exception("Library update failed")
    library_control.update_library.side_effect = update_error

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        ModelControl._download_process(conn, model_class, model_id, model_info, library_control)

    assert str(exc_info.value) == "Library update failed"
    model_class.download.assert_called_once_with(model_id, model_info)
    library_control.update_library.assert_called_once_with(model_id, {"new": "entry"})
    conn.send.assert_not_called()