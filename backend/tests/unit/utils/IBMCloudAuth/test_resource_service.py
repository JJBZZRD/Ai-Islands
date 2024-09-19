import pytest
from unittest.mock import patch, MagicMock
from backend.utils.ibm_cloud_account_auth import ResourceService

@pytest.fixture
def resource_service():
    return ResourceService()

@patch('backend.utils.ibm_cloud_account_auth.requests.get')
def test_get_resource_list(mock_get, resource_service):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'resources': [{'id': 'resource1'}]}
    
    result = resource_service.get_resource_list('fake_token')
    
    assert result == [{'id': 'resource1'}]
    mock_get.assert_called_once()

@patch('backend.utils.ibm_cloud_account_auth.requests.get')
def test_get_service_credentials(mock_get, resource_service):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'credentials': {'apikey': 'fake_key'}}
    
    result = resource_service.get_service_credentials('fake_token', 'service_name')
    
    assert result == {'apikey': 'fake_key'}
    mock_get.assert_called_once()