import pytest
from unittest.mock import patch, MagicMock
from backend.controlers.playground_control import PlaygroundControl
from backend.playground.playground import Playground

@pytest.fixture
def mock_model_control():
    return MagicMock()

@pytest.fixture
def playground_control(mock_model_control):
    with patch('backend.controlers.playground_control.LibraryControl'):
        pc = PlaygroundControl(mock_model_control)
        pc.playgrounds = {
            "test_playground": Playground("test_playground", "Test playground"),
        }
        pc.playgrounds["test_playground"].models = {
            "model1": {"input": "text", "output": "text"},
            "model2": {"input": "text", "output": "image"},
        }
        pc.playgrounds["test_playground"].chain = ["model1", "model2"]
        return pc

def test_inference_success(playground_control):
    inference_request = {
        "playground_id": "test_playground",
        "data": {"payload": "initial input"}
    }
    
    mock_results = [
        {"result": "intermediate output"},
        {"result": "final output"}
    ]
    playground_control.model_control.inference.side_effect = mock_results
    
    result = playground_control.inference(inference_request)
    
    assert result == {"result": "final output"}
    playground_control.model_control.inference.assert_any_call({
        "model_id": "model1",
        "data": {"payload": "initial input"},
        "playground_request": True
    })
    playground_control.model_control.inference.assert_any_call({
        "model_id": "model2",
        "data": {"payload": "{'result': 'intermediate output'}"},
        "playground_request": True
    })

def test_inference_nonexistent_playground(playground_control):
    inference_request = {
        "playground_id": "nonexistent_playground",
        "data": {"payload": "initial input"}
    }
    
    with pytest.raises(KeyError):
        playground_control.inference(inference_request)

def test_inference_empty_chain(playground_control):
    playground_control.playgrounds["test_playground"].chain = []
    inference_request = {
        "playground_id": "test_playground",
        "data": {"payload": "initial input"}
    }
    
    with pytest.raises(UnboundLocalError, match="cannot access local variable 'inference_result' where it is not associated with a value"):
        playground_control.inference(inference_request)
    
    playground_control.model_control.inference.assert_not_called()

def test_inference_single_model_chain(playground_control):
    playground_control.playgrounds["test_playground"].chain = ["model1"]
    inference_request = {
        "playground_id": "test_playground",
        "data": {"payload": "initial input"}
    }
    
    mock_result = {"result": "final output"}
    playground_control.model_control.inference.return_value = mock_result
    
    result = playground_control.inference(inference_request)
    
    assert result == {"result": "final output"}
    playground_control.model_control.inference.assert_called_once_with({
        "model_id": "model1",
        "data": {"payload": "initial input"},
        "playground_request": True
    })

@patch('builtins.print')
def test_inference_print_output(mock_print, playground_control):
    inference_request = {
        "playground_id": "test_playground",
        "data": {"payload": "initial input"}
    }
    
    mock_results = [
        {"result": "intermediate output"},
        {"result": "final output"}
    ]
    playground_control.model_control.inference.side_effect = mock_results
    
    playground_control.inference(inference_request)
    
    mock_print.assert_any_call("inference_result", {"result": "intermediate output"})
    mock_print.assert_any_call("inference_result", {"result": "final output"})

def test_inference_model_error(playground_control):
    inference_request = {
        "playground_id": "test_playground",
        "data": {"payload": "initial input"}
    }
    
    playground_control.model_control.inference.side_effect = Exception("Model error")
    
    with pytest.raises(Exception, match="Model error"):
        playground_control.inference(inference_request)

def test_inference_data_type_conversion(playground_control):
    inference_request = {
        "playground_id": "test_playground",
        "data": {"payload": "initial input"}
    }
    
    mock_results = [
        {"result": "intermediate output"},
        {"result": b"final output as bytes"}
    ]
    playground_control.model_control.inference.side_effect = mock_results
    
    result = playground_control.inference(inference_request)
    
    assert result == {"result": b"final output as bytes"}
    playground_control.model_control.inference.assert_any_call({
        "model_id": "model2",
        "data": {"payload": "{'result': 'intermediate output'}"},
        "playground_request": True
    })