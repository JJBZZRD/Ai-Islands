import pytest
from unittest.mock import patch, MagicMock
from backend.utils.ibm_cloud_account_auth import Authentication
from backend.core.exceptions import ModelError

@pytest.fixture
def mock_watson_settings():
    return {
        'IBM_CLOUD_API_KEY': 'fake_api_key',
    }

@patch('backend.utils.ibm_cloud_account_auth.watson_settings')
def test_authentication_init(mock_settings, mock_watson_settings):
    mock_settings.get.side_effect = lambda key: mock_watson_settings.get(key)
    auth = Authentication()
    assert auth.api_key == 'fake_api_key'

@patch('backend.utils.ibm_cloud_account_auth.requests.post')
@patch('backend.utils.ibm_cloud_account_auth.watson_settings')
def test_get_iam_token_success(mock_settings, mock_post, mock_watson_settings):
    mock_settings.get.side_effect = lambda key: mock_watson_settings.get(key)
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {'access_token': 'fake_token'}
    
    auth = Authentication()
    token = auth.get_iam_token()
    
    assert token == 'fake_token'

@patch('backend.utils.ibm_cloud_account_auth.requests.post')
@patch('backend.utils.ibm_cloud_account_auth.watson_settings')
def test_get_iam_token_failure(mock_settings, mock_post, mock_watson_settings):
    mock_settings.get.side_effect = lambda key: mock_watson_settings.get(key)
    mock_post.return_value.status_code = 400
    mock_post.return_value.text = 'Bad Request'
    
    auth = Authentication()
    with pytest.raises(ModelError, match="Failed to get IAM token: HTTP 400"):
        auth.get_iam_token()

def test_validate_api_key_success(mock_watson_settings):
    with patch.object(Authentication, 'get_iam_token', return_value='fake_token'):
        auth = Authentication()
        assert auth.validate_api_key() is True

def test_validate_api_key_failure(mock_watson_settings):
    with patch.object(Authentication, 'get_iam_token', side_effect=Exception("API key validation failed")):
        auth = Authentication()
        assert auth.validate_api_key() is False