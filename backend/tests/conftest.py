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

# watsonx.ai models
@pytest.fixture
def watson_foundation_model_info():
    return {
        "is_online": True,
        "model_source": "IBM",
        "model_class": "WatsonModel",
        "mapping": {
            "input": "text",
            "output": "text"
        },
        "tags": [
            "text-generation",
            "question-answering",
            "summarization",
            "classification",
            "generation",
            "extraction"
        ],
        "pipeline_tag": "text-generation",
        "model_card_url": "https://www.ibm.com/products/watsonx-ai/foundation-models",
        "model_desc": "The Granite model series is a family of IBM-trained, dense decoder-only models, which are particularly well-suited for generative tasks.",
        "model_detail": "Granite models are designed to be used for a wide range of generative and non-generative tasks with appropriate prompt engineering. They employ a GPT-style decoder-only architecture, with additional innovations from IBM Research and the open community.",
        "config": {
            "prompt": {
                "system_prompt": "You are a helpful AI assistant.",
                "example_conversation": ""
            },
            "parameters": {
                "temperature": 0.7,
                "top_p": 1.0,
                "top_k": 50,
                "max_new_tokens": 1000,
                "min_new_tokens": 1,
                "repetition_penalty": 1.0,
                "random_seed": 42,
                "stop_sequences": [
                    "Human:",
                    "AI:",
                    "<|endoftext|>"
                ]
            },
            "rag_settings": {
                "use_dataset": False,
                "dataset_name": None,
                "similarity_threshold": 0.5,
                "use_chunking": False
            },
            "chat_history": False
        },
        "auth_token": None,
        "base_model": "ibm/granite-13b-instruct-v1",
        "dir": "data\\downloads\\watson\\ibm/granite-13b-instruct-v1",
        "is_customised": False
    }

# watsonx.ai embedding models
@pytest.fixture
def watson_embedding_model_info():
    return {
        "is_online": True,
        "model_source": "IBM",
        "model_class": "WatsonModel",
        "mapping": {
            "input": "text",
            "output": "text"
        },
        "tags": [
            "embedding",
            "text-embedding",
            "semantic-search",
            "document-comparison",
            "retrieval-augmented-generation"
        ],
        "pipeline_tag": "feature-extraction",
        "model_card_url": "https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/fm-models-embed.html?context=wx",
        "model_desc": "The slate-30m-english-rtrvr is a distilled version of the slate-125m-english-rtrvr, provided by IBM. It's trained to maximize cosine similarity between two text inputs for later similarity evaluation.",
        "model_detail": "This embedding model has 6 layers, is faster than slate-125m-english-rtrvr, and is fine-tuned for sentence retrieval-based tasks. It generates 384-dimensional embeddings with a 512 token input limit.",
        "config": {
            "embedding_dimensions": 130,
            "max_input_tokens": 512,
            "supported_languages": [
                "English"
            ]
        },
        "auth_token": None,
        "base_model": "ibm/slate-30m-english-rtrvr",
        "dir": "data\\downloads\\watson\\ibm/slate-30m-english-rtrvr",
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