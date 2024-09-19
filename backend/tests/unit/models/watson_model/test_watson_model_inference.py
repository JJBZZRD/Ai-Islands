import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_model import WatsonModel
from backend.core.exceptions import ModelError

@pytest.fixture
def watson_foundation_model():
    model = WatsonModel("ibm/granite-13b-instruct-v1")
    model.model_inference = MagicMock()
    model.is_loaded = True
    model.config = {
        "parameters": {
            "temperature": 0.7,
            "top_p": 1.0,
            "top_k": 50,
            "max_new_tokens": 1000,
            "min_new_tokens": 1,
            "repetition_penalty": 1.0,
            "random_seed": 42,
            "stop_sequences": ["Human:", "AI:", "<|endoftext|>"]
        },
        "prompt": {
            "system_prompt": "You are a helpful AI assistant.",
            "example_conversation": ""
        },
        "chat_history": False
    }
    return model

@pytest.fixture
def watson_embedding_model():
    model = WatsonModel("ibm/slate-30m-english-rtrvr")
    model.embeddings = MagicMock()
    model.is_loaded = True
    model.config = {
        "embedding_dimensions": 130,
        "max_input_tokens": 512,
        "supported_languages": ["English"]
    }
    return model

def test_inference_success_foundation(watson_foundation_model):
    test_input = "Hello, how are you?"
    test_data = {"payload": test_input}
    expected_output = "I'm an AI assistant. How can I help you today?"
    
    watson_foundation_model.model_inference.generate_text.return_value = expected_output
    
    result = watson_foundation_model.inference(test_data)
    
    assert result == expected_output
    watson_foundation_model.model_inference.generate_text.assert_called_once()

def test_inference_success_embedding(watson_embedding_model):
    test_input = "Hello, how are you?"
    test_data = {"payload": test_input}
    expected_output = {'dimensions': 130, 'embedding': [0.1, 0.2, 0.3]}  # Example embedding output
    
    watson_embedding_model.embeddings.embed.return_value = expected_output
    
    result = watson_embedding_model.inference(test_data)
    
    assert result == expected_output
    watson_embedding_model.embeddings.embed.assert_called_once()

def test_inference_with_chat_history(watson_foundation_model):
    watson_foundation_model.config['chat_history'] = True
    test_input = "What's the weather like?"
    test_data = {"payload": test_input}
    expected_output = "I'm sorry, I don't have real-time weather information. Is there anything else I can help you with?"
    
    watson_foundation_model.model_inference.generate_text.return_value = expected_output
    
    result = watson_foundation_model.inference(test_data)
    
    assert result == expected_output
    assert watson_foundation_model.chat_history == [
        {"role": "human", "content": test_input},
        {"role": "ai", "content": expected_output}
    ]

@patch.object(WatsonModel, 'model_inference')
def test_inference_api_failure_foundation(mock_model_inference, watson_foundation_model):
    mock_model_inference.generate_text.side_effect = Exception("API request failed")
    
    with pytest.raises(ModelError, match="An unexpected error occurred during inference"):
        watson_foundation_model.inference({"payload": "Test input"})

@patch.object(WatsonModel, 'embeddings')
def test_inference_api_failure_embedding(mock_embeddings, watson_embedding_model):
    mock_embeddings.embed.side_effect = Exception("API request failed")
    
    with pytest.raises(ModelError, match="An unexpected error occurred during inference"):
        watson_embedding_model.inference({"payload": "Test input"})

def test_clear_chat_history(watson_foundation_model):
    watson_foundation_model.chat_history = [{"role": "human", "content": "Hello"}, {"role": "ai", "content": "Hi there!"}]
    watson_foundation_model.clear_chat_history()
    assert watson_foundation_model.chat_history == []