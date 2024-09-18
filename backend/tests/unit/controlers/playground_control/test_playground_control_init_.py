import pytest
from unittest.mock import patch, MagicMock, mock_open, call
from backend.controlers.playground_control import PlaygroundControl
from backend.core.exceptions import FileReadError, FileWriteError
from backend.core.config import PLAYGROUND_JSON_PATH

@pytest.fixture
def mock_model_control():
    return MagicMock()

@patch('backend.controlers.playground_control.LibraryControl')
def test_playground_control_init(mock_library_control, mock_model_control):
    with patch.object(PlaygroundControl, '_initialise_playground_data_directory') as mock_init_dir:
        with patch.object(PlaygroundControl, '_initialise_all_playgrounds') as mock_init_all:
            playground_control = PlaygroundControl(mock_model_control)

    assert playground_control.model_control == mock_model_control
    assert isinstance(playground_control.library_control, MagicMock)
    assert playground_control.playgrounds == {}
    mock_init_dir.assert_called_once()
    mock_init_all.assert_called_once()

@patch('os.path.exists')
@patch('json.dump')
@patch('backend.controlers.playground_control.JSONHandler.read_json')
def test_initialise_playground_data_directory_new_file(mock_read_json, mock_json_dump, mock_exists):
    mock_exists.return_value = False
    mock_read_json.side_effect = [FileReadError("Empty file"), {}]
    
    with patch('builtins.open', mock_open()) as mock_file:
        with patch.object(PlaygroundControl, '_initialise_all_playgrounds'):
            playground_control = PlaygroundControl(MagicMock())
            result = playground_control._initialise_playground_data_directory()

    assert result == True
    assert mock_file.call_count == 2
    mock_file.assert_any_call(PLAYGROUND_JSON_PATH, "w")
    assert mock_json_dump.call_count == 2
    mock_json_dump.assert_has_calls([call({}, mock_file()), call({}, mock_file())], any_order=True)

@patch('os.path.exists')
def test_initialise_playground_data_directory_existing_file(mock_exists):
    mock_exists.return_value = True
    
    result = PlaygroundControl(MagicMock())._initialise_playground_data_directory()
    
    assert result == True

@patch('backend.controlers.playground_control.JSONHandler.read_json')
def test_initialise_all_playgrounds_success(mock_read_json):
    mock_read_json.return_value = {
        "playground1": {"description": "Test 1"},
        "playground2": {"description": "Test 2"}
    }
    
    playground_control = PlaygroundControl(MagicMock())
    with patch.object(playground_control, '_initialise_playground') as mock_init_playground:
        result = playground_control._initialise_all_playgrounds()
    
    assert result == {"status": "success", "message": "Playgrounds initialised"}
    assert mock_init_playground.call_count == 2

@patch('backend.controlers.playground_control.JSONHandler.read_json')
def test_initialise_all_playgrounds_file_read_error(mock_read_json):
    mock_read_json.side_effect = FileReadError("Error reading file")
    
    with pytest.raises(FileReadError, match="Error reading file"):
        PlaygroundControl(MagicMock())

@patch('backend.controlers.playground_control.JSONHandler.read_json')
def test_initialise_playground_success(mock_read_json):
    mock_read_json.return_value = {
        "playground1": {
            "description": "Test playground",
            "models": {"model1": {}},
            "chain": ["model1"]
        }
    }
    
    playground_control = PlaygroundControl(MagicMock())
    result = playground_control._initialise_playground("playground1")
    
    assert result == True
    assert "playground1" in playground_control.playgrounds
    assert playground_control.playgrounds["playground1"].description == "Test playground"
    assert playground_control.playgrounds["playground1"].models == {"model1": {}}
    assert playground_control.playgrounds["playground1"].chain == ["model1"]

@patch('backend.controlers.playground_control.JSONHandler.read_json')
def test_initialise_playground_file_read_error(mock_read_json):
    mock_read_json.side_effect = FileReadError("Error reading file")
    
    with pytest.raises(FileReadError, match="Error reading file"):
        PlaygroundControl(MagicMock())

@patch('backend.controlers.playground_control.logger')
def test_initialise_playground_logging(mock_logger):
    playground_control = PlaygroundControl(MagicMock())
    with patch.object(playground_control, '_get_playground_json_data', return_value={"description": "Test"}):
        playground_control._initialise_playground("playground1")
    
    mock_logger.error.assert_not_called()