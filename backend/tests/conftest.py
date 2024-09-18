import pytest

@pytest.fixture
def model_info():
    return {
        "is_online": False,
        "model_source": "transformers",
        "model_class": "TransformerModel",
        "mapping": {
            "input": "text",
            "output": "text"
        },
        "pipeline_tag": "text-generation",
        "requirements": {
            "required_classes": {
                "model": "AutoModelForCausalLM",
                "tokenizer": "AutoTokenizer"
            },
            "requires_auth": False
        },
        "config": {
            "model_config": {
                "torch_dtype": "auto"
            },
            "tokenizer_config": {},
            "pipeline_config": {
                "max_length": 512,
                "max_new_tokens": 1000,
                "num_beams": 2,
                "use_cache": True,
                "temperature": 0.6,
                "top_k": 40,
                "top_p": 0.92,
                "repetition_penalty": 1.2,
                "length_penalty": 1.2
            }
        },
        "base_model": "Qwen/Qwen2-0.5B-Instruct",
        "dir": "data/downloads/transformers/Qwen/Qwen2-0.5B-Instruct",
        "is_customised": False
    }

@pytest.fixture
def mock_library_entry(model_info):
    return {
        "Qwen/Qwen2-0.5B-Instruct": model_info
    }

@pytest.fixture
def gpu_device():
    import torch
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")