import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_model import WatsonModel
from backend.core.exceptions import ModelError

@pytest.fixture
def watson_foundation_model():
    return WatsonModel("ibm/granite-13b-instruct-v1")

@pytest.fixture
def watson_embedding_model():
    return WatsonModel("ibm/slate-30m-english-rtrvr")

@patch('backend.models.watson_model.watson_settings')
@patch('backend.models.watson_model.Authentication')
def test_download_success_foundation(mock_auth, mock_settings, watson_foundation_model, watson_foundation_model_info):
    mock_settings.get.return_value = "fake_api_key"
    mock_auth.return_value.validate_api_key.return_value = True
    
    model_id = "ibm/granite-13b-instruct-v1"
    result = WatsonModel.download(model_id, watson_foundation_model_info)
    
    expected_result = watson_foundation_model_info.copy()
    expected_result['base_model'] = model_id
    expected_result['dir'] = f"data\\downloads\\watson\\{model_id}"
    expected_result['is_online'] = True
    
    assert result == expected_result

@patch('backend.models.watson_model.watson_settings')
@patch('backend.models.watson_model.Authentication')
def test_download_success_embedding(mock_auth, mock_settings, watson_embedding_model, watson_embedding_model_info):
    mock_settings.get.return_value = "fake_api_key"
    mock_auth.return_value.validate_api_key.return_value = True
    
    model_id = "ibm/slate-30m-english-rtrvr"
    result = WatsonModel.download(model_id, watson_embedding_model_info)
    
    expected_result = watson_embedding_model_info.copy()
    expected_result['base_model'] = model_id
    expected_result['dir'] = f"data\\downloads\\watson\\{model_id}"
    expected_result['is_online'] = True
    
    assert result == expected_result

@patch('backend.models.watson_model.watson_settings')
def test_download_no_api_key(mock_settings, watson_foundation_model, watson_foundation_model_info):
    mock_settings.get.return_value = None
    
    with pytest.raises(ModelError, match="No IBM API key found"):
        WatsonModel.download("ibm/granite-13b-instruct-v1", watson_foundation_model_info)

@patch('backend.models.watson_model.watson_settings')
@patch('backend.models.watson_model.Authentication')
def test_download_invalid_api_key(mock_auth, mock_settings, watson_foundation_model, watson_foundation_model_info):
    mock_settings.get.return_value = "fake_api_key"
    mock_auth.return_value.validate_api_key.return_value = False
    
    with pytest.raises(ModelError, match="Invalid IBM API key"):
        WatsonModel.download("ibm/granite-13b-instruct-v1", watson_foundation_model_info)