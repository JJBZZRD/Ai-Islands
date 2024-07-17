"""
Module: test_api_model

This module contains unit tests for the FastAPI application, designed to validate various API endpoints 
and ensure the application behaves as expected when handling HTTP requests.
"""



from fastapi.testclient import TestClient

from ..api.main import app

client = TestClient(app)


def test_download_model():
    model_id = "ibm/granite-13b-chat-v2"
    response = client.post(f"/download-model?model_id={model_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Model {model_id} downloaded successfully"}