import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_service import WatsonService
from backend.core.exceptions import ModelError

@pytest.mark.parametrize("model_id, model_info_fixture", [
    ("ibm/natural-language-understanding", "watson_nlu_model_info"),
    ("ibm/text-to-speech", "watson_tts_model_info"),
    ("ibm/speech-to-text", "watson_stt_model_info")
])
def test_watson_service_download_success(model_id, model_info_fixture, request):
    model_info = request.getfixturevalue(model_info_fixture)
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings, \
         patch('backend.models.watson_service.Authentication') as mock_auth, \
         patch('backend.models.watson_service.AccountInfo') as mock_account_info, \
         patch('backend.models.watson_service.json.dump'), \
         patch('backend.models.watson_service.os.makedirs'), \
         patch('builtins.open', MagicMock()):
        
        mock_settings.get.return_value = "fake_api_key"
        mock_auth.return_value.validate_api_key.return_value = True
        mock_account_info.return_value.get_resource_list.return_value = [
            {"name": model_info['config']['service_name']}
        ]
        
        result = WatsonService.download(model_id, model_info)
        
        assert result['base_model'] == model_id
        assert result['is_customised'] is False
        assert 'dir' in result

@pytest.mark.parametrize("model_id, model_info_fixture", [
    ("ibm/natural-language-understanding", "watson_nlu_model_info"),
    ("ibm/text-to-speech", "watson_tts_model_info"),
    ("ibm/speech-to-text", "watson_stt_model_info")
])
def test_watson_service_download_missing_api_key(model_id, model_info_fixture, request):
    model_info = request.getfixturevalue(model_info_fixture)
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings:
        mock_settings.get.return_value = None
        
        with pytest.raises(ModelError, match="No IBM API key found"):
            WatsonService.download(model_id, model_info)

@pytest.mark.parametrize("model_id, model_info_fixture", [
    ("ibm/natural-language-understanding", "watson_nlu_model_info"),
    ("ibm/text-to-speech", "watson_tts_model_info"),
    ("ibm/speech-to-text", "watson_stt_model_info")
])
def test_watson_service_download_invalid_api_key(model_id, model_info_fixture, request):
    model_info = request.getfixturevalue(model_info_fixture)
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings, \
         patch('backend.models.watson_service.Authentication') as mock_auth:
        
        mock_settings.get.return_value = "fake_api_key"
        mock_auth.return_value.validate_api_key.return_value = False
        
        with pytest.raises(ModelError, match="Invalid IBM API key"):
            WatsonService.download(model_id, model_info)

@pytest.mark.parametrize("model_id, model_info_fixture", [
    ("ibm/natural-language-understanding", "watson_nlu_model_info"),
    ("ibm/text-to-speech", "watson_tts_model_info"),
    ("ibm/speech-to-text", "watson_stt_model_info")
])
def test_watson_service_download_missing_service(model_id, model_info_fixture, request):
    model_info = request.getfixturevalue(model_info_fixture)
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings, \
         patch('backend.models.watson_service.Authentication') as mock_auth, \
         patch('backend.models.watson_service.AccountInfo') as mock_account_info:
        
        mock_settings.get.return_value = "fake_api_key"
        mock_auth.return_value.validate_api_key.return_value = True
        mock_account_info.return_value.get_resource_list.return_value = []
        
        with pytest.raises(ModelError, match="The required service .* is missing from your IBM Cloud account"):
            WatsonService.download(model_id, model_info)