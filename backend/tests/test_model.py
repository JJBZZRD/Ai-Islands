"""
Module: model_control_tests

This module contains unit test functions designed to validate the functionality of various methods 
in the `model_control` class or module. The primary goal of these tests is to ensure that models 
are correctly loaded, managed, and terminated by `model_control`.

Additional test functions can be added to this module to further validate other aspects of the `model_control` 
class or module, ensuring comprehensive testing coverage and robust model management functionality.
"""


def test_model_load_model(model_control):
    model_id = "ibm/granite-13b-chat-v2"
    assert model_control.load_model(model_id) is True
    assert model_id in model_control.models
    conn = model_control.models[model_id]['conn']
    conn.send("terminate")
    model_control.models[model_id]['process'].join()
    