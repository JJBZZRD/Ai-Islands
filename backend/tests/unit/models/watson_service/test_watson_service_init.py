import pytest
from backend.models.watson_service import WatsonService

def test_watson_service_init_nlu():
    model = WatsonService("ibm/natural-language-understanding")
    assert model.model_id == "ibm/natural-language-understanding"
    assert model.account_info is None
    assert model.nlu is None
    assert model.text_to_speech is None
    assert model.speech_to_text is None
    assert model.api_key is None
    assert model.is_loaded is False

def test_watson_service_init_tts():
    model = WatsonService("ibm/text-to-speech")
    assert model.model_id == "ibm/text-to-speech"
    assert model.account_info is None
    assert model.nlu is None
    assert model.text_to_speech is None
    assert model.speech_to_text is None
    assert model.api_key is None
    assert model.is_loaded is False

def test_watson_service_init_stt():
    model = WatsonService("ibm/speech-to-text")
    assert model.model_id == "ibm/speech-to-text"
    assert model.account_info is None
    assert model.nlu is None
    assert model.text_to_speech is None
    assert model.speech_to_text is None
    assert model.api_key is None
    assert model.is_loaded is False