import pytest
from unittest.mock import patch, MagicMock
from backend.utils.ibm_cloud_account_auth import ResourceService
from backend.core.exceptions import ModelError

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
    mock_get.return_value.json.return_value = {'resources': [{'name': 'service1', 'guid': 'fake-guid', 'credentials': {'apikey': 'fake_key'}}]}

    result = resource_service.get_service_credentials('fake_token', 'service1')
    
    assert result == {'apikey': 'fake_key'}

@patch('backend.utils.ibm_cloud_account_auth.requests.get')
def test_get_service_credentials_not_found(mock_get, resource_service):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'resources': [{'name': 'service2'}]}

    with pytest.raises(ModelError, match="No matching instance found for the specified service name"):
        resource_service.get_service_credentials('fake_token', 'service1')

@patch('backend.utils.ibm_cloud_account_auth.requests.get')
def test_get_service_credentials_error(mock_get, resource_service):
    mock_get.return_value.status_code = 400
    mock_get.return_value.text = "Bad Request"

    with pytest.raises(ModelError, match="Failed to get service credentials"):
        resource_service.get_service_credentials('fake_token', 'service1')