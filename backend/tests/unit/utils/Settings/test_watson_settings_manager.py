import pytest
from unittest.mock import patch, mock_open
from backend.utils.watson_settings_manager import WatsonSettingsManager

@pytest.fixture
def watson_settings():
    return WatsonSettingsManager()

def test_singleton_instance():
    instance1 = WatsonSettingsManager()
    instance2 = WatsonSettingsManager()
    assert instance1 is instance2

@patch('backend.utils.watson_settings_manager.find_dotenv')
@patch('backend.utils.watson_settings_manager.load_dotenv')
def test_reload(mock_load_dotenv, mock_find_dotenv, watson_settings):
    mock_find_dotenv.return_value = 'C:\\Users\\costa\\Ai-Islands\\.env'
    watson_settings.reload()
    mock_load_dotenv.assert_called_once_with('C:\\Users\\costa\\Ai-Islands\\.env', override=True)

@patch('backend.utils.watson_settings_manager.os.getenv')
def test_get(mock_getenv, watson_settings):
    mock_getenv.return_value = 'test_value'
    assert watson_settings.get('TEST_KEY') == 'test_value'

@patch('backend.utils.watson_settings_manager.set_key')
@patch('backend.utils.watson_settings_manager.os.environ', new_callable=dict)
def test_set(mock_environ, mock_set_key, watson_settings):
    watson_settings.set('TEST_KEY', 'test_value')
    mock_set_key.assert_called_once_with(watson_settings.env_file, 'TEST_KEY', 'test_value')
    assert mock_environ['TEST_KEY'] == 'test_value'

@patch('backend.utils.watson_settings_manager.WatsonSettingsManager.set')
def test_update_location(mock_set, watson_settings):
    watson_settings.update_location('us-south')
    assert mock_set.call_count == 5
    mock_set.assert_any_call('IBM_CLOUD_MODELS_URL', 'https://us-south.ml.cloud.ibm.com')

@patch('backend.utils.watson_settings_manager.WatsonSettingsManager.get')
def test_get_all_settings(mock_get, watson_settings):
    mock_get.side_effect = lambda key: f'fake_{key.lower()}'
    settings = watson_settings.get_all_settings()
    assert len(settings) == 7
    assert settings['IBM_CLOUD_API_KEY'] == 'fake_ibm_cloud_api_key'

@patch('builtins.open', new_callable=mock_open)
@patch('backend.utils.watson_settings_manager.find_dotenv', return_value='')
def test_create_default_env(mock_find_dotenv, mock_file, watson_settings):
    watson_settings.create_default_env()
    mock_file.assert_called_once_with('.env', 'w')
    handle = mock_file()
    assert handle.write.call_count == len(WatsonSettingsManager.DEFAULT_ENV_VARS)