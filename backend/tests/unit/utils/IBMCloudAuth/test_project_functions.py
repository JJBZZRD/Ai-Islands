import pytest
from unittest.mock import patch, MagicMock
from backend.utils.ibm_cloud_account_auth import get_projects, select_project

@patch('backend.utils.ibm_cloud_account_auth.Authentication')
@patch('backend.utils.ibm_cloud_account_auth.AccountInfo')
def test_get_projects_success(mock_account_info, mock_auth):
    mock_auth.return_value.get_iam_token.return_value = 'fake_token'
    mock_account_info.return_value.list_projects.return_value = [
        {"metadata": {"guid": "project1"}, "entity": {"name": "Project 1"}},
        {"metadata": {"guid": "project2"}, "entity": {"name": "Project 2"}}
    ]
    
    projects = get_projects()
    
    assert len(projects) == 2
    assert projects[0] == {"id": "project1", "name": "Project 1"}
    assert projects[1] == {"id": "project2", "name": "Project 2"}

def test_select_project():
    result = select_project("project1")
    assert result == {"status": "Project selected", "project_id": "project1"}

@patch('backend.utils.ibm_cloud_account_auth.logger')
def test_select_project_error(mock_logger):
    result = select_project("invalid_project")
    assert result["status"] == "Error"
    mock_logger.error.assert_called_once()