"""
Example test for the APIs
"""



from fastapi.testclient import TestClient

from ..api.main import app

client = TestClient(app)


def test_download_model(model_id):
    response = client.post(f"model/download-model?model_id={model_id}")
    assert response.status_code == 200
    assert response.json() == {
    "message": f"Model {model_id} downloaded successfully",
    "data": {}
}