"""
Module: conftest

This module contains shared fixtures for pytest, used across multiple test modules to set up 
common test environments and dependencies. Specifically, it provides a fixture to initialize 
an instance of the `ModelControl` class.
"""


import pytest

from ..controlers.model_control import ModelControl

@pytest.fixture
def model_control():
    return ModelControl()
