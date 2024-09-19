import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_service import WatsonService
from backend.core.exceptions import ModelError

@pytest.fixture
def watson_service_nlu():
    return WatsonService("ibm/natural-language-understanding")

@pytest.fixture
def watson_service_tts():
    return WatsonService("ibm/text-to-speech")

@pytest.fixture
def watson_service_stt():
    return WatsonService("ibm/speech-to-text")

@pytest.mark.parametrize("service_fixture, service_class, service_attr, attribute_name", [
    ("watson_service_nlu", "NaturalLanguageUnderstandingV1", "natural-language-understanding", "nlu"),
    ("watson_service_tts", "TextToSpeechV1", "text-to-speech", "text_to_speech"),
    ("watson_service_stt", "SpeechToTextV1", "speech-to-text", "speech_to_text")
])
def test_watson_service_load_success(service_fixture, service_class, service_attr, attribute_name, request):
    service = request.getfixturevalue(service_fixture)
    model_info = {
        "config": {
            "service_name": service_attr
        }
    }
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings, \
         patch('backend.models.watson_service.AccountInfo') as mock_account_info, \
         patch(f'backend.models.watson_service.{service_class}') as mock_service:
        
        mock_settings.get.side_effect = ["fake_api_key", "fake_project_id"]
        mock_account_info.return_value.get_service_credentials.return_value = {
            "url": "fake_url",
            "apikey": "fake_api_key"
        }
        
        result = service.load("cpu", model_info)
        
        assert result is True
        assert service.is_loaded is True
        assert getattr(service, attribute_name) is not None
        assert service.api_key == "fake_api_key"
        assert service.account_info is not None

@pytest.mark.parametrize("service_fixture", [
    "watson_service_nlu",
    "watson_service_tts",
    "watson_service_stt"
])
def test_watson_service_load_missing_api_key(service_fixture, request):
    service = request.getfixturevalue(service_fixture)
    model_info = {
        "config": {
            "service_name": "test_service"
        }
    }
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings:
        mock_settings.get.return_value = None
        
        with pytest.raises(ModelError, match="No IBM API key found"):
            service.load("cpu", model_info)

@pytest.mark.parametrize("service_fixture, service_attr", [
    ("watson_service_nlu", "natural-language-understanding"),
    ("watson_service_tts", "text-to-speech"),
    ("watson_service_stt", "speech-to-text")
])
def test_watson_service_load_missing_credentials(service_fixture, service_attr, request):
    service = request.getfixturevalue(service_fixture)
    model_info = {
        "config": {
            "service_name": service_attr
        }
    }
    
    with patch('backend.models.watson_service.watson_settings') as mock_settings, \
         patch('backend.models.watson_service.AccountInfo') as mock_account_info:
        
        mock_settings.get.side_effect = ["fake_api_key", "fake_project_id"]
        mock_account_info.return_value.get_service_credentials.return_value = None
        
        with pytest.raises(ModelError, match="Failed to retrieve or create .* service credentials"):
            service.load("cpu", model_info)