import pytest
import copy
from backend.data_utils.json_handler import JSONHandler
from backend.core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH, PLAYGROUND_JSON_PATH

def pytest_collection_modifyitems(items):
    for item in items:
        if "/unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

# Store original data
original_model_index = JSONHandler.read_json(MODEL_INDEX_PATH)
original_downloaded_models = JSONHandler.read_json(DOWNLOADED_MODELS_PATH)
original_playground_data = JSONHandler.read_json(PLAYGROUND_JSON_PATH)

@pytest.fixture(autouse=True)
def reset_application_data():
    # Setup: Nothing to do, original data is already stored
    yield
    # Teardown: Reset all data to original state
    JSONHandler.write_json(MODEL_INDEX_PATH, copy.deepcopy(original_model_index))
    JSONHandler.write_json(DOWNLOADED_MODELS_PATH, copy.deepcopy(original_downloaded_models))
    JSONHandler.write_json(PLAYGROUND_JSON_PATH, copy.deepcopy(original_playground_data))

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


@pytest.fixture
def mock_playground_data():
    return {
        "test_playground": {
            "description": "Test playground",
            "models": {
                "model1": {
                    "input": "text",
                    "output": "text",
                    "pipeline_tag": "text-generation",
                    "is_online": False
                },
                "model2": {
                    "input": "text",
                    "output": "text",
                    "pipeline_tag": "text-classification",
                    "is_online": False
                },
                "model3": {
                    "input": "image",
                    "output": "text",
                    "pipeline_tag": "image-to-text",
                    "is_online": False
                }
            },
            "chain": [],
            "active_chain": False
        },
        "empty_playground": {
            "description": "Empty playground",
            "models": {},
            "chain": [],
            "active_chain": False
        }
    }

