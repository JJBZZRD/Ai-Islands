import pytest
from unittest.mock import Mock, patch
from backend.controlers.model_control import ModelControl

@pytest.fixture
def mock_model_control():
    with patch('backend.controlers.model_control.LibraryControl') as mock_library_control, \
         patch('backend.controlers.model_control.SettingsService') as mock_settings_service:
        mock_model_control = ModelControl()
        mock_model_control.library_control = mock_library_control
        yield mock_model_control

@pytest.fixture
def model_info():
    return {
        "base_model": "Qwen/Qwen2-0.5B-Instruct",
        "dir": "/path/to/model"
    }

def test_delete_base_model(mock_model_control, model_info):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control.library_control.get_models_by_base_model.return_value = ["dependent_model1", "dependent_model2"]
    mock_model_control.is_model_loaded = Mock(return_value=False)

    with patch('os.path.exists', return_value=True), \
         patch('shutil.rmtree') as mock_rmtree:
        result = mock_model_control.delete_model(model_id)

    assert result == {"message": f"Model {model_id} and its dependent models deleted"}
    mock_model_control.library_control.delete_model.assert_any_call("dependent_model1")
    mock_model_control.library_control.delete_model.assert_any_call("dependent_model2")
    mock_rmtree.assert_called_once_with("/path/to/model")

def test_delete_dependent_model(mock_model_control, model_info):
    model_id = "dependent_model"
    model_info["base_model"] = "base_model"
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control.is_model_loaded = Mock(return_value=False)

    result = mock_model_control.delete_model(model_id)

    assert result == {"message": f"Model {model_id} deleted"}
    mock_model_control.library_control.delete_model.assert_called_once_with(model_id)

def test_delete_loaded_model(mock_model_control, model_info):
    model_id = "loaded_model"
    model_info["base_model"] = "base_model"
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control.is_model_loaded = Mock(return_value=True)
    mock_model_control.unload_model = Mock()

    result = mock_model_control.delete_model(model_id)

    assert result == {"message": f"Model {model_id} deleted"}
    mock_model_control.unload_model.assert_called_once_with(model_id)
    mock_model_control.library_control.delete_model.assert_called_once_with(model_id)

def test_delete_nonexistent_model(mock_model_control):
    model_id = "nonexistent_model"
    mock_model_control._get_model_info = Mock(side_effect=ValueError("Model not found"))

    result = mock_model_control.delete_model(model_id)

    assert result == {"error": "Model not found"}

@patch('backend.controlers.model_control.logger')
def test_delete_model_logging(mock_logger, mock_model_control, model_info):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control.library_control.get_models_by_base_model.return_value = ["dependent_model"]
    mock_model_control.is_model_loaded = Mock(return_value=False)

    with patch('os.path.exists', return_value=True), \
         patch('shutil.rmtree'):
        mock_model_control.delete_model(model_id)

    mock_logger.info.assert_any_call("Deleted dependent model: dependent_model")
    mock_logger.info.assert_any_call(f"Model {model_id} directory deleted")

def test_delete_model_directory_not_found(mock_model_control, model_info):
    model_id = "Qwen/Qwen2-0.5B-Instruct"
    mock_model_control._get_model_info = Mock(return_value=model_info)
    mock_model_control.library_control.get_models_by_base_model.return_value = []
    mock_model_control.is_model_loaded = Mock(return_value=False)

    with patch('os.path.exists', return_value=False), \
         patch('shutil.rmtree') as mock_rmtree:
        result = mock_model_control.delete_model(model_id)

    assert result == {"message": f"Model {model_id} and its dependent models deleted"}
    # The directory deletion should not be called
    mock_rmtree.assert_not_called()