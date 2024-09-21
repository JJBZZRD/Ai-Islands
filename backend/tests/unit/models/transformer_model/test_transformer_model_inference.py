import pytest
from unittest.mock import patch, MagicMock
from backend.models.transformer_model import TransformerModel
import copy

@pytest.fixture
def transformer_model(model_info_library):
    model = TransformerModel(model_id="Qwen/Qwen2-0.5B-Instruct")
    model.config = copy.deepcopy(model_info_library['config']) 
    model.pipeline = MagicMock()
    model.pipeline.task = model_info_library.get('pipeline_tag')
    model.model_instance_data = []
    return model

def test_inference_text_generation_without_chat_history(transformer_model):
    test_input = "Hello, how are you?"
    test_data = {
        "payload": test_input,
        "pipeline_config": {"max_length": 100}
    }

    mock_output = [{"generated_text": [{"content": "I'm doing well, thank you for asking!"}]}]
    transformer_model.pipeline.return_value = mock_output

    with patch.object(transformer_model, 'config', {
        'user_prompt': {"role": "user", "content": "[USER]"},
        'chat_history': False
    }):
        output = transformer_model.inference(test_data)

    expected_input = [{"role": "user", "content": "Hello, how are you?"}]
    transformer_model.pipeline.assert_called_once_with(expected_input, max_length=100)
    assert output == "I'm doing well, thank you for asking!"

def test_inference_text_generation_with_chat_history(transformer_model):

    test_input = "Hello, how are you?"
    test_data = {
        "payload": test_input,
        "pipeline_config": {"max_length": 100}
    }

    mock_output = [{"generated_text": [{"content": "I'm doing well, thank you for asking!"}]}]

    def pipeline_side_effect(input_data, **kwargs):
        # Make a deep copy of input_data to capture it
        transformer_model.captured_input_data = copy.deepcopy(input_data)
        return copy.deepcopy(mock_output)

    transformer_model.pipeline.side_effect = pipeline_side_effect

    with patch.object(transformer_model, 'config', copy.deepcopy({
        'user_prompt': {"role": "user", "content": "[USER]"},
        'chat_history': True
    })):
        output = transformer_model.inference(test_data)

    # Expected input should only contain the user's message
    expected_input = [{"role": "user", "content": "Hello, how are you?"}]

    # Retrieve the actual input data captured during the pipeline call
    input_data = transformer_model.captured_input_data

    assert input_data == expected_input, f"Expected input {expected_input}, but got {input_data}"
    assert output == "I'm doing well, thank you for asking!"
    assert transformer_model.model_instance_data == [
        {"role": "user", "content": "Hello, how are you?"},
        {"content": "I'm doing well, thank you for asking!"}
    ]



def test_inference_with_rag(transformer_model):
    test_input = "What is the capital of France?"
    test_data = {
        "payload": test_input,
        "pipeline_config": {"max_length": 100}
    }

    rag_settings = {
        "use_dataset": True,
        "dataset_name": "test_dataset",
        "similarity_threshold": 0.5,
        "use_chunking": False
    }
    relevant_entries = ["Paris is the capital of France."]

    with patch.object(transformer_model, 'config', {
        'rag_settings': rag_settings,
        'user_prompt': {"role": "user", "content": "[USER]"},
        'chat_history': False
    }), \
    patch('backend.models.transformer_model.DatasetManagement') as mock_dataset_management:
        mock_dataset_management.return_value.find_relevant_entries.return_value = relevant_entries
        transformer_model.dataset_management = mock_dataset_management.return_value

        mock_output = [{"generated_text": [{"content": "The capital of France is Paris."}]}]
        transformer_model.pipeline.return_value = mock_output

        output = transformer_model.inference(test_data)

    expected_input = [{
        "role": "user",
        "content": "Relevant information:\n- Paris is the capital of France.\n\nWhat is the capital of France?"
    }]
    transformer_model.pipeline.assert_called_once_with(expected_input, max_length=100)
    assert output == "The capital of France is Paris."

    mock_dataset_management.return_value.find_relevant_entries.assert_called_once_with(
        test_input,
        "test_dataset",
        use_chunking=False,
        similarity_threshold=0.5
    )
