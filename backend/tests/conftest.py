"""
Module: conftest

This module contains shared fixtures for pytest, used across multiple test modules to set up 
common test environments and dependencies. Specifically, it provides a fixture to initialize 
an instance of the `ModelControl` class.
"""

import pytest

from ..controlers.model_control import ModelControl
from ..models import TransformerModel
from ..controlers.library_control import LibraryControl
from ..data_utils.json_handler import JSONHandler
from ..core.config import CONFIG_PATH


@pytest.fixture(scope="function")
def transformer_model_class():
    yield TransformerModel

@pytest.fixture(scope="function")
def model_control():
    yield ModelControl()

@pytest.fixture(scope="function")
def library_control():
    yield LibraryControl()

@pytest.fixture(scope="session")
def model_control_session():
    yield ModelControl()

@pytest.fixture(scope="function")
def model_id():
    yield "cardiffnlp/twitter-roberta-base-sentiment-latest"

@pytest.fixture(scope="function")
def model_id_list():
    yield ["cardiffnlp/twitter-roberta-base-sentiment-latest", "microsoft/speecht5_tts"]

@pytest.fixture(scope="function")
def playground_id():
    yield "testing_playground"

@pytest.fixture(scope="session")
def hardware_preference():
    config = JSONHandler.read_json(CONFIG_PATH)
    pref = config.get("hardware", "cpu")
    yield pref
