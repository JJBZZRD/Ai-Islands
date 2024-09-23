import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_model import WatsonModel
from backend.core.exceptions import ModelError

@pytest.fixture
def watson_foundation_model(watson_foundation_model_info):
    model = WatsonModel("ibm/granite-13b-instruct-v1")
    with patch('backend.models.watson_model.watson_settings') as mock_settings, \
         patch('backend.models.watson_model.Authentication') as mock_auth, \
         patch('backend.models.watson_model.AccountInfo') as mock_account_info, \
         patch('backend.models.watson_model.ModelInference') as mock_model_inference:
        mock_settings.get.side_effect = ["fake_api_key", "fake_project_id", "fake_url"]
        mock_auth.return_value.validate_api_key.return_value = True
        mock_auth.return_value.validate_project.return_value = True
        mock_account_info.return_value.get_service_credentials.return_value = {"url": "test_url", "apikey": "test_apikey"}
        model.load("cpu", watson_foundation_model_info)
    return model

@pytest.fixture
def watson_embedding_model(watson_embedding_model_info):
    model = WatsonModel("ibm/slate-30m-english-rtrvr")
    with patch('backend.models.watson_model.watson_settings') as mock_settings, \
         patch('backend.models.watson_model.Authentication') as mock_auth, \
         patch('backend.models.watson_model.WatsonxEmbeddings') as mock_embeddings:
        mock_settings.get.side_effect = ["fake_api_key", "fake_project_id", "fake_url"]
        mock_auth.return_value.validate_api_key.return_value = True
        mock_auth.return_value.validate_project.return_value = True
        model.load("cpu", watson_embedding_model_info)
    return model

def test_inference_success_foundation(watson_foundation_model):
    test_input = "Hello, how are you?"
    test_data = {"payload": test_input}
    expected_output = "I'm an AI assistant. How can I help you today?"
    
    watson_foundation_model.model_inference.generate_text.return_value = expected_output
    
    result = watson_foundation_model.inference(test_data)
    
    assert isinstance(result, dict)
    assert result['result'] == expected_output
    assert result['relevant_entries_count'] == 0
    assert result['total_entries_count'] == 0

def test_inference_success_embedding(watson_embedding_model):
    test_input = "Hello, how are you?"
    test_data = {"payload": test_input}
    expected_output = {'dimensions': 3, 'embedding': [0.1, 0.2, 0.3]}

    watson_embedding_model.embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
    
    result = watson_embedding_model.inference(test_data)
    
    assert result['dimensions'] == expected_output['dimensions']
    assert isinstance(result['embedding'], list)
    assert len(result['embedding']) == 3
    watson_embedding_model.embeddings.embed_query.assert_called_once_with(test_input)

def test_inference_with_chat_history(watson_foundation_model):
    watson_foundation_model.config['chat_history'] = True
    test_input = "What's the weather like?"
    test_data = {"payload": test_input}
    expected_output = "I'm sorry, I don't have real-time weather information. Is there anything else I can help you with?"

    watson_foundation_model.model_inference.generate_text.return_value = expected_output

    result = watson_foundation_model.inference(test_data)

    assert isinstance(result, dict)
    assert result['result'] == expected_output
    assert 'relevant_entries_count' in result
    assert 'total_entries_count' in result

    # Check if chat history is updated
    assert len(watson_foundation_model.chat_history) == 2
    assert watson_foundation_model.chat_history[-2] == {"role": "human", "content": test_input}
    assert watson_foundation_model.chat_history[-1] == {"role": "ai", "content": expected_output}

def test_inference_api_failure_foundation(watson_foundation_model):
    watson_foundation_model.model_inference.generate_text.side_effect = Exception("API request failed")
    
    with pytest.raises(ModelError, match="An unexpected error occurred during inference"):
        watson_foundation_model.inference({"payload": "Test input"})

def test_inference_api_failure_embedding(watson_embedding_model):
    watson_embedding_model.embeddings.embed_query.side_effect = Exception("API request failed")
    
    with pytest.raises(ModelError, match="An unexpected error occurred during inference"):
        watson_embedding_model.inference({"payload": "Test input"})

def test_clear_chat_history(watson_foundation_model):
    watson_foundation_model.chat_history = [{"role": "human", "content": "Hello"}, {"role": "ai", "content": "Hi there!"}]
    watson_foundation_model.clear_chat_history()
    assert watson_foundation_model.chat_history == []