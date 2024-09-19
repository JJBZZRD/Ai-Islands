import pytest
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH

@pytest.fixture
def model_info_library():
    library = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
    return library["Qwen/Qwen2-0.5B-Instruct"]

@pytest.fixture
def model_info_index():
    model_index = JSONHandler.read_json(MODEL_INDEX_PATH)
    return model_index["Qwen/Qwen2-0.5B-Instruct"]

@pytest.fixture
def mock_library_entry(model_info_library):
    return {
        "Qwen/Qwen2-0.5B-Instruct": model_info_library
    }

@pytest.fixture
def mock_index_entry(model_info_index):
    return {
        "Qwen/Qwen2-0.5B-Instruct": model_info_index
    }

@pytest.fixture
def gpu_device():
    import torch
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")