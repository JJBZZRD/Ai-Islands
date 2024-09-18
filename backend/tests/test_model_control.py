"""
Module: model_control_tests

This module contains unit test functions designed to validate the functionality of various methods 
in the `model_control` class or module. The primary goal of these tests is to ensure that models 
are correctly loaded, managed, and terminated by `model_control`.

Additional test functions can be added to this module to further validate other aspects of the `model_control` 
class or module, ensuring comprehensive testing coverage and robust model management functionality.
"""

def test_model_control_download_model(model_control, model_id):
    response = model_control.download_model(model_id)
    assert response["message"] == f"Model {model_id} downloaded successfully"

def test_model_load_model(model_control, model_id):
    response = model_control.load_model(model_id)
    assert response is True
    assert model_id in model_control.models

def test_model_unload_model(model_control, model_id):
    model_control.load_model(model_id)
    response = model_control.unload_model(model_id)
    assert response is True
    assert model_id not in model_control.models

def test_model_is_model_loaded(model_control, model_id):
    model_control.load_model(model_id)
    assert model_control.is_model_loaded(model_id) is True
    model_control.unload_model(model_id)
    assert model_control.is_model_loaded(model_id) is False

def test_model_list_active_models(model_control, model_id):
    model_control.load_model(model_id)
    active_models = model_control.list_active_models()
    assert any(model['model_id'] == model_id for model in active_models)
    model_control.unload_model(model_id)

def test_model_delete_model(model_control, model_id):
    response = model_control.delete_model(model_id)
    assert response["message"] == f"Model {model_id} and its dependent models deleted"
    assert model_id not in model_control.models

    # reinstall the model
    model_control.download_model(model_id)
