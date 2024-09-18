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
            "playground1": Playground("playground1", "Test playground 1"),
            "playground2": Playground("playground2", "Test playground 2"),
        }
        pc.playgrounds["playground1"].models = {"model1": {"input": "text", "output": "text"}}
        pc.playgrounds["playground2"].models = {"model2": {"input": "image", "output": "text"}}
        pc.playgrounds["playground1"].chain = ["model1"]
        pc.playgrounds["playground2"].chain = ["model2"]
        return pc

def test_list_playgrounds_returns_dict(playground_control):
    result = playground_control.list_playgrounds()
    assert isinstance(result, dict)

def test_list_playgrounds_correct_keys(playground_control):
    result = playground_control.list_playgrounds()
    assert set(result.keys()) == {"playground1", "playground2"}

def test_list_playgrounds_content(playground_control):
    result = playground_control.list_playgrounds()
    assert "playground1" in result
    assert "playground2" in result
    assert result["playground1"]["description"] == "Test playground 1"
    assert result["playground1"]["models"] == {"model1": {"input": "text", "output": "text"}}
    assert result["playground1"]["chain"] == ["model1"]
    assert result["playground2"]["description"] == "Test playground 2"
    assert result["playground2"]["models"] == {"model2": {"input": "image", "output": "text"}}
    assert result["playground2"]["chain"] == ["model2"]

def test_list_playgrounds_empty(playground_control):
    playground_control.playgrounds = {}
    result = playground_control.list_playgrounds()
    assert result == {}

def test_list_playgrounds_to_dict_called(playground_control):
    with patch.object(Playground, 'to_dict') as mock_to_dict:
        mock_to_dict.return_value = {"mocked": "data"}
        result = playground_control.list_playgrounds()
    assert mock_to_dict.call_count == 2
    assert all(playground["mocked"] == "data" for playground in result.values())

@patch('backend.controlers.playground_control.logger')
def test_list_playgrounds_no_logging(mock_logger, playground_control):
    playground_control.list_playgrounds()
    mock_logger.info.assert_not_called()
    mock_logger.error.assert_not_called()

def test_list_playgrounds_does_not_modify_original(playground_control):
    original_playgrounds = playground_control.playgrounds.copy()
    playground_control.list_playgrounds()
    assert playground_control.playgrounds == original_playgrounds

def test_list_playgrounds_deep_copy(playground_control):
    result = playground_control.list_playgrounds()
    # Modify the result
    result["playground1"]["description"] = "Modified description"
    # Check that the original playground is not modified
    assert playground_control.playgrounds["playground1"].description == "Test playground 1"