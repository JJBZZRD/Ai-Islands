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
            "existing_playground": Playground("existing_playground", "Test playground"),
        }
        pc.playgrounds["existing_playground"].models = {"model1": {"input": "text", "output": "text"}}
        pc.playgrounds["existing_playground"].chain = ["model1"]
        return pc

def test_get_playground_info_existing(playground_control):
    result = playground_control.get_playground_info("existing_playground")
    assert isinstance(result, dict)
    assert result["description"] == "Test playground"
    assert result["models"] == {"model1": {"input": "text", "output": "text"}}
    assert result["chain"] == ["model1"]

def test_get_playground_info_nonexistent(playground_control):
    result = playground_control.get_playground_info("nonexistent_playground")
    assert result == {}

@patch('backend.controlers.playground_control.logger')
def test_get_playground_info_logging_existing(mock_logger, playground_control):
    playground_control.get_playground_info("existing_playground")
    mock_logger.info.assert_not_called()

@patch('backend.controlers.playground_control.logger')
def test_get_playground_info_logging_nonexistent(mock_logger, playground_control):
    playground_control.get_playground_info("nonexistent_playground")
    mock_logger.info.assert_called_with("Playground nonexistent_playground not found")

def test_get_playground_info_to_dict_called(playground_control):
    with patch.object(Playground, 'to_dict') as mock_to_dict:
        mock_to_dict.return_value = {"mocked": "data"}
        result = playground_control.get_playground_info("existing_playground")
    mock_to_dict.assert_called_once()
    assert result == {"mocked": "data"}

def test_get_playground_info_does_not_modify_original(playground_control):
    original_playground = playground_control.playgrounds["existing_playground"]
    result = playground_control.get_playground_info("existing_playground")
    result["description"] = "Modified description"
    assert playground_control.playgrounds["existing_playground"].description == "Test playground"

def test_get_playground_info_returns_copy(playground_control):
    result1 = playground_control.get_playground_info("existing_playground")
    result2 = playground_control.get_playground_info("existing_playground")
    assert result1 is not result2

def test_get_playground_info_empty_playground(playground_control):
    playground_control.playgrounds["empty_playground"] = Playground("empty_playground", "")
    result = playground_control.get_playground_info("empty_playground")
    assert result["description"] == ""
    assert result["models"] == {}
    assert result["chain"] == []