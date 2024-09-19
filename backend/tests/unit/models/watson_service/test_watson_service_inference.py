import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_service import WatsonService
from backend.core.exceptions import ModelError

@pytest.fixture
def watson_service_nlu():
    service = WatsonService("ibm/natural-language-understanding")
    service.nlu = MagicMock()
    service.is_loaded = True
    return service

@pytest.fixture
def watson_service_tts():
    service = WatsonService("ibm/text-to-speech")
    service.text_to_speech = MagicMock()
    service.is_loaded = True
    return service

@pytest.fixture
def watson_service_stt():
    service = WatsonService("ibm/speech-to-text")
    service.speech_to_text = MagicMock()
    service.is_loaded = True
    return service

def test_nlu_inference(watson_service_nlu):
    watson_service_nlu.nlu_config = {
        "sentiment": True,
        "entities": True
    }
    test_input = "This is a test sentence."
    test_data = {"payload": test_input, "analysis_type": "all"}
    expected_output = {
        "sentiment": {"document": {"score": 0.5, "label": "positive"}},
        "entities": [{"type": "TestEntity", "text": "test"}]
    }
    
    watson_service_nlu.nlu.analyze.return_value.get_result.return_value = expected_output
    
    result = watson_service_nlu.inference(test_data)
    
    assert result == expected_output
    watson_service_nlu.nlu.analyze.assert_called_once()

def test_tts_inference(watson_service_tts):
    watson_service_tts.tts_config = {
        "voice": "en-US_AllisonV3Voice",
        "pitch": 0,
        "speed": 0
    }
    test_input = "This is a test sentence."
    test_data = {"payload": test_input}
    expected_output = b"audio_content"

    # Mock the synthesize method to return a MagicMock with get_result method
    mock_synthesize_result = MagicMock()
    mock_synthesize_result.get_result.return_value.content = expected_output
    watson_service_tts.text_to_speech.synthesize.return_value = mock_synthesize_result

    result = watson_service_tts.inference(test_data)

    assert result["status"] == "success"
    assert "audio_content" in result
    assert isinstance(result["audio_content"], str)  # Check if it's a base64 string
    assert result["voice"] == "en-US_AllisonV3Voice"
    assert result["pitch"] == "0"
    assert result["speed"] == "0"
    watson_service_tts.text_to_speech.synthesize.assert_called_once()

@patch('backend.models.watson_service.os.path.exists')
@patch('backend.models.watson_service.AudioSegment')
@patch('builtins.open', new_callable=MagicMock)
def test_stt_inference(mock_open, mock_audio_segment, mock_exists, watson_service_stt):
    watson_service_stt.stt_config = {
        "model": "en-US_BroadbandModel",
        "content_type": "audio/wav"
    }
    test_input = "path/to/audio/file.wav"
    test_data = {"payload": test_input, "file_path": test_input}
    expected_output = {
        "results": [
            {"alternatives": [{"transcript": "This is a test sentence."}]}
        ]
    }
    
    mock_exists.return_value = True
    mock_open.return_value.__enter__.return_value = "mocked_file_content"
    watson_service_stt.speech_to_text.recognize.return_value.get_result.return_value = expected_output
    
    result = watson_service_stt.inference(test_data)
    
    assert result["status"] == "success"
    assert result["transcription"] == "This is a test sentence."
    watson_service_stt.speech_to_text.recognize.assert_called_once()
    mock_open.assert_called_once_with(test_input, 'rb')

@pytest.mark.parametrize("service_fixture", [
    "watson_service_nlu",
    "watson_service_tts",
    "watson_service_stt"
])
def test_inference_not_loaded(service_fixture, request):
    service = request.getfixturevalue(service_fixture)
    service.is_loaded = False
    
    with pytest.raises(ModelError, match="Model is not loaded"):
        service.inference({"payload": "test"})

@pytest.mark.parametrize("service_fixture, error_message, input_data", [
    ("watson_service_nlu", "Error analyzing text", {"payload": "test", "analysis_type": "all"}),
    ("watson_service_tts", "Error synthesizing text", {"payload": "test"}),
    ("watson_service_stt", "Error transcribing audio", {"payload": "test", "file_path": "test.wav"})
])
def test_inference_api_failure(service_fixture, error_message, input_data, request):
    service = request.getfixturevalue(service_fixture)
    
    if service_fixture == "watson_service_nlu":
        service.nlu.analyze.side_effect = Exception("API request failed")
        service.nlu_config = {"sentiment": True}
    elif service_fixture == "watson_service_tts":
        service.text_to_speech.synthesize.side_effect = Exception("API request failed")
        service.tts_config = {"voice": "en-US_AllisonV3Voice"}
    else:
        service.speech_to_text.recognize.side_effect = Exception("API request failed")
        service.stt_config = {"model": "en-US_BroadbandModel"}
    
    with pytest.raises(ModelError, match=error_message):
        service.inference(input_data)

def test_list_stt_models(watson_service_stt):
    expected_models = ["model1", "model2", "model3"]
    watson_service_stt.speech_to_text.list_models.return_value.get_result.return_value = {
        "models": [{"name": model} for model in expected_models]
    }
    
    result = watson_service_stt.list_stt_models()
    
    assert result == expected_models
    watson_service_stt.speech_to_text.list_models.assert_called_once()