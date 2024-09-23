# backend/tests/unit/models/watson_model/test_watson_model_init.py

import pytest
from unittest.mock import patch, MagicMock
from backend.models.watson_model import WatsonModel

def test_watson_model_init_foundation():
    model_id = "ibm/granite-13b-instruct-v1"
    model = WatsonModel(model_id)
    
    assert model.model_id == model_id
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

def test_watson_model_init_embedding():
    model_id = "ibm/slate-30m-english-rtrvr"
    model = WatsonModel(model_id)
    
    assert model.model_id == model_id
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

@patch('backend.models.watson_model.get_projects')
def test_select_project_success(mock_get_projects):
    mock_get_projects.return_value = [{"id": "project1", "name": "Test Project"}]
    model = WatsonModel("test_model")
    
    with patch('backend.models.watson_model.watson_settings') as mock_settings:
        result = model.select_project()
    
    assert result is True
    assert model.project_id == "project1"
    mock_settings.set.assert_called_once_with("USER_PROJECT_ID", "project1")

@patch('backend.models.watson_model.get_projects')
def test_select_project_no_projects(mock_get_projects):
    mock_get_projects.return_value = []
    model = WatsonModel("test_model")
    
    result = model.select_project()
    
    assert result is False
    assert model.project_id is None