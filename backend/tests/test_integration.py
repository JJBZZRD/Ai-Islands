
def test_download_model_integration(model_control_session, model_id):
    result = model_control_session._download_model(model_id)
    assert result == {"message": f"Model {model_id} downloaded successfully"}
    
def test_load_model_integration(model_control_session, model_id):
    result = model_control_session.load_model(model_id)
    assert result is True
    assert model_id in model_control_session.models

def test_active_models_integration(model_control_session, model_id):
    active_models = model_control_session.list_active_models()
    assert model_id in [model["model_id"] for model in active_models]

def test_inference_integration(model_control_session, model_id):
    inference_request = {
        "model_id": model_id, 
        "data": {
            "payload": "this is positive"
        }
    }

    result = model_control_session.inference(inference_request)
    assert "label" in result[0].keys()
    assert "score" in result[0].keys()

def test_unload_model_integration(model_control_session, model_id):
    result = model_control_session.unload_model(model_id)
    assert result is True
    assert model_id not in model_control_session.models
