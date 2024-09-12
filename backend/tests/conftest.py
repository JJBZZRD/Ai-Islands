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
import os

def pytest_configure(config):
    # Disable all loggers
    logging.getLogger().setLevel(logging.ERROR)
    
    # Specifically disable loggers for noisy modules
    for logger_name in ['faiss', 'ibm_watsonx_ai', 'sentence_transformers', 'backend']:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Disable IBM Watson logging
    os.environ['DISABLE_WATSON_LOGGING'] = 'true'

@pytest.fixture(autouse=True)
def disable_logging():
    # This will disable logging for the duration of each test
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)

@pytest.fixture
def model_control():
    return ModelControl()

@pytest.fixture(scope="session", autouse=True)
def set_matplotlib_backend():
    matplotlib.use('Agg')
