"""
Module: conftest

This module contains shared fixtures for pytest, used across multiple test modules to set up 
common test environments and dependencies. Specifically, it provides a fixture to initialize 
an instance of the `ModelControl` class.
"""


import pytest
import logging
import warnings
from pydantic import ConfigDict
from ..controlers.model_control import ModelControl
import matplotlib

def pytest_configure(config):
    # Disable all logging
    logging.disable(logging.CRITICAL)

    # Ignore all warnings
    warnings.simplefilter("ignore")

    # Suppress Pydantic warnings about namespace conflicts
    from pydantic import BaseModel
    BaseModel.model_config = ConfigDict(protected_namespaces=())

@pytest.fixture(scope="session", autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)

@pytest.fixture
def model_control():
    return ModelControl()

@pytest.fixture(scope="session", autouse=True)
def set_matplotlib_backend():
    matplotlib.use('Agg')
