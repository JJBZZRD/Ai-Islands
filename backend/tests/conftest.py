"""
Module: conftest

This module contains shared fixtures for pytest, used across multiple test modules to set up 
common test environments and dependencies. Specifically, it provides a fixture to initialize 
an instance of the `ModelControl` class.
"""


import pytest

from ..controlers.model_control import ModelControl

@pytest.fixture(scope="function")
def model_control():
    yield ModelControl()

@pytest.fixture(scope="session")
def model_control_session():
    yield ModelControl()

@pytest.fixture(scope="function")
def model_id():
    yield "cardiffnlp/twitter-roberta-base-sentiment-latest"

@pytest.fixture(scope="function")
def playground_id():
    yield "testing_playground"
