# Ai-Islands

## Model Index Example

### Transformer Model (Hugging Face)
Below is an example of transformer model in model_index.json
```json
{
  "model_name_from_huggingface": {
    "is_online": false,
    "model_source": "transformers",
    "model_class": "TransformerModel",
    "tags": [
      "text-generation",
      "text-generation-inference"
      "more tags ..."
    ],
    "pipeline_tag": "pipeline task",
    "model_card_url": "url to the source",
    "requirements":{
      "required_classes":{
        "model": "AutoModelForSpeechSeq2Seq (required AutoModel class to load the model if any)",
        "tokenizer": "AutoTokenizer (required AutoTokenizer class to load the tokenizer if any)",
        "processor": "AutoProcessor (required AutoProcessor class to load the processor if any)"
      }
    },
    "config": {
      "model_config": {
        "use_cache": true,
        "more_config": "these configs will be passed into AutoModel.from_pretrained()"
      },
      "tokenizer_config": {
        "do_lower_case": false,
        "more_config": "these configs will be passed into AutoTokenizer.from_pretrained()"
      },
      "processor_config": {
        "more_config": "these configs will be passed into AutoProcessor.from_pretrained()"
      },
      "pipeline_config": {
        "max_length": 50,
        "more_config": "these configs will be passed into pipeline()"
      }
    }
  }
}
```

## Known Issues

### Transformer model - Reranker Model
Reranker model "jinaai/jina-reranker-v2-base-multilingual" requires `trust_remote_code=True` in order to work. 
During download and loading phases, it will need to run some remote code on the local computer in a child process 
(this is the action set by the model developer and thus cannot be changed). 
However, this behaviour leads to an unexpected error with fastapi development mode. 
This issue occurs ONLY in development mode but not in production mode. 
Thus, it works with `fastapi run backend/api/main.py` but not with `fastapi dev backend/api/main.py`. 
Ben: I have tried so many ways to fix the issue but it just could not work with fastapi dev. 
Good news is that it works fine with fastapi run somehow :).
