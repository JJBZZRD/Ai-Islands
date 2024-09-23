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

def test_watson_model_init():
    foundation_model = WatsonModel("ibm/granite-13b-instruct-v1")
    embedding_model = WatsonModel("ibm/slate-30m-english-rtrvr")

    for model in [foundation_model, embedding_model]:
        assert model.config is None
        assert model.auth is None
        assert model.resource_service is None
        assert model.account_info is None
        assert model.model_inference is None
        assert model.embeddings is None
        assert model.is_loaded is False
        assert model.api_key is None
        assert model.project_id is None
        assert model.chat_history == []

    assert foundation_model.model_id == "ibm/granite-13b-instruct-v1"
    assert embedding_model.model_id == "ibm/slate-30m-english-rtrvr"

@patch('backend.models.watson_model.Authentication')
@patch('backend.models.watson_model.AccountInfo')
@patch('backend.models.watson_model.ModelInference')
@patch('backend.models.watson_model.WatsonxEmbeddings')
def test_watson_model_load_success(mock_embeddings, mock_model_inference, mock_account_info, mock_auth, watson_foundation_model, watson_embedding_model, watson_foundation_model_info, watson_embedding_model_info):
    mock_auth.return_value.validate_api_key.return_value = True
    mock_auth.return_value.validate_project.return_value = True
    mock_account_info.return_value.get_service_credentials.return_value = {"url": "test_url", "apikey": "test_apikey"}

    with patch('backend.models.watson_model.watson_settings') as mock_settings:
        mock_settings.get.side_effect = ["fake_api_key", "fake_project_id", "fake_url", "fake_api_key", "fake_project_id", "fake_url"]
        
        # Test loading foundation model
        result_foundation = watson_foundation_model.load("cpu", watson_foundation_model_info)
        assert result_foundation is True
        assert watson_foundation_model.is_loaded is True
        mock_model_inference.assert_called_once()
        mock_embeddings.assert_not_called()
        
        # Reset mocks for embedding test
        mock_model_inference.reset_mock()
        mock_embeddings.reset_mock()
        
        # Test loading embedding model
        result_embedding = watson_embedding_model.load("cpu", watson_embedding_model_info)
        assert result_embedding is True
        assert watson_embedding_model.is_loaded is True
        mock_embeddings.assert_called_once()
        mock_model_inference.assert_not_called()

    # Common assertions
    assert watson_foundation_model.api_key == "fake_api_key"
    assert watson_foundation_model.project_id == "fake_project_id"
    assert watson_embedding_model.api_key == "fake_api_key"
    assert watson_embedding_model.project_id == "fake_project_id"

@patch('backend.models.watson_model.Authentication')
def test_watson_model_load_invalid_api_key(mock_auth, watson_foundation_model, watson_foundation_model_info):
    mock_auth.return_value.validate_api_key.return_value = False

    with pytest.raises(ModelError, match="Invalid IBM API key"):
        watson_foundation_model.load("cpu", watson_foundation_model_info)

@patch('backend.models.watson_model.Authentication')
def test_watson_model_load_invalid_project(mock_auth, watson_foundation_model, watson_foundation_model_info):
    mock_auth.return_value.validate_api_key.return_value = True
    mock_auth.return_value.validate_project.return_value = False

    with pytest.raises(ModelError, match="Invalid project ID"):
        watson_foundation_model.load("cpu", watson_foundation_model_info)

@patch('backend.models.watson_model.get_projects')
@patch('backend.models.watson_model.watson_settings')
def test_select_project_success(mock_settings, mock_get_projects, watson_foundation_model):
    mock_get_projects.return_value = [{"id": "project1", "name": "Test Project"}]
    
    result = watson_foundation_model.select_project()
    
    assert result is True
    assert watson_foundation_model.project_id == "project1"
    mock_settings.set.assert_called_once_with("USER_PROJECT_ID", "project1")

def test_watson_model_load_success(watson_foundation_model, watson_embedding_model):
    assert watson_foundation_model.is_loaded is True
    assert watson_foundation_model.model_inference is not None
    assert watson_embedding_model.is_loaded is True
    assert watson_embedding_model.embeddings is not None

    assert watson_foundation_model.api_key == "fake_api_key"
    assert watson_foundation_model.project_id == "fake_project_id"
    assert watson_embedding_model.api_key == "fake_api_key"
    assert watson_embedding_model.project_id == "fake_project_id"