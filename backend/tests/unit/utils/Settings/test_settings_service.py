import pytest
from unittest.mock import patch, MagicMock
from backend.settings.settings_service import SettingsService
from backend.utils.watson_settings_manager import WatsonSettingsManager

@pytest.fixture
def settings_service():
    return SettingsService()

@pytest.fixture
def mock_watson_settings():
    return {
        'IBM_CLOUD_API_KEY': 'fake_api_key',
        'IBM_CLOUD_MODELS_URL': 'https://eu-gb.ml.cloud.ibm.com',
        'USER_PROJECT_ID': 'fake_project_id'
    }

@pytest.mark.asyncio
@patch('backend.settings.settings_service.watson_settings')
async def test_update_watson_settings(mock_settings, settings_service):
    mock_settings.set = MagicMock()
    mock_settings.update_location = MagicMock()

    settings = MagicMock(api_key='new_api_key', project_id='new_project_id', location='us-south')
    result = await settings_service.update_watson_settings(settings)

    assert result == "Watson settings updated successfully"
    mock_settings.set.assert_any_call("IBM_CLOUD_API_KEY", "new_api_key")
    mock_settings.set.assert_any_call("USER_PROJECT_ID", "new_project_id")
    mock_settings.update_location.assert_called_once_with("us-south")

@pytest.mark.asyncio
@patch('backend.settings.settings_service.watson_settings')
async def test_get_watson_settings(mock_settings, settings_service, mock_watson_settings):
    mock_settings.get_all_settings.return_value = mock_watson_settings

    result = await settings_service.get_watson_settings()

    assert result == {
        "api_key": "fake_api_key",
        "location": "eu-gb",
        "project": "fake_project_id"
    }

@pytest.mark.asyncio
@patch('backend.settings.settings_service.SettingsService._read_config')
@patch('backend.settings.settings_service.SettingsService._write_config')
async def test_update_chunking_settings(mock_write_config, mock_read_config, settings_service):
    mock_read_config.return_value = {"chunking": {}}
    settings = MagicMock(dict=lambda: {"chunk_size": 1000, "overlap": 200})

    result = await settings_service.update_chunking_settings(settings)

    assert result == "Chunking settings updated successfully"
    mock_write_config.assert_called_once_with({"chunking": {"chunk_size": 1000, "overlap": 200}})

@pytest.mark.asyncio
@patch('backend.settings.settings_service.SettingsService._read_config')
async def test_get_chunking_settings(mock_read_config, settings_service):
    mock_read_config.return_value = {"chunking": {"chunk_size": 1000, "overlap": 200}}

    result = await settings_service.get_chunking_settings()

    assert result == {"chunk_size": 1000, "overlap": 200}

@pytest.mark.asyncio
@patch('backend.settings.settings_service.SettingsService._read_config')
@patch('backend.settings.settings_service.SettingsService._write_config')
@patch('backend.settings.settings_service.torch.cuda.is_available')
async def test_set_hardware_preference(mock_cuda_available, mock_write_config, mock_read_config, settings_service):
    mock_read_config.return_value = {"hardware": "cpu"}
    mock_cuda_available.return_value = True

    result = await settings_service.set_hardware_preference("gpu")

    assert result == "Successfully set hardware to gpu"
    mock_write_config.assert_called_once_with({"hardware": "gpu"})

@pytest.mark.asyncio
@patch('backend.settings.settings_service.SettingsService._read_config')
async def test_get_hardware_preference(mock_read_config, settings_service):
    mock_read_config.return_value = {"hardware": "gpu"}

    result = await settings_service.get_hardware_preference()

    assert result == "gpu"

@pytest.mark.asyncio
@patch('backend.settings.settings_service.torch.cuda.is_available')
@patch('backend.settings.settings_service.torch.version')
@patch('backend.settings.settings_service.torch.backends.cudnn.version')
async def test_check_gpu(mock_cudnn_version, mock_torch_version, mock_cuda_available, settings_service):
    mock_cuda_available.return_value = True
    mock_torch_version.cuda = "11.3"
    mock_cudnn_version.return_value = 8200

    result = await settings_service.check_gpu()

    assert result == {
        "CUDA available": True,
        "CUDA version": "11.3",
        "cuDNN version": 8200
    }