import pytest
from unittest.mock import patch, MagicMock
from backend.utils.ibm_cloud_account_auth import AccountInfo

@pytest.fixture
def account_info():
    return AccountInfo()

@patch('backend.utils.ibm_cloud_account_auth.Credentials')
@patch('backend.utils.ibm_cloud_account_auth.APIClient')
def test_account_info_lazy_evaluation(mock_api_client, mock_credentials, account_info):
    assert account_info._credentials is None
    assert account_info._watsonx is None
    
    _ = account_info.credentials
    _ = account_info.watsonx
    
    assert account_info._credentials is not None
    assert account_info._watsonx is not None
    mock_credentials.assert_called_once()
    mock_api_client.assert_called_once()

@patch('backend.utils.ibm_cloud_account_auth.requests.get')
def test_list_projects(mock_get, account_info):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'resources': [{'metadata': {'guid': 'project1'}, 'entity': {'name': 'Project 1'}}]}
    
    result = account_info.list_projects('fake_token')
    
    assert result == [{'metadata': {'guid': 'project1'}, 'entity': {'name': 'Project 1'}}]
    mock_get.assert_called_once()