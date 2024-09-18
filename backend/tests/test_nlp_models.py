def test_sentiment_analysis_model(transformer_model_class, library_control, hardware_preference):
    model_id = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    model_info = library_control.get_model_info_index(model_id)

    transformer_model_class.download(model_id, model_info)
    
    model = transformer_model_class(model_id)
    res = model.load(hardware_preference, model_info)
    assert res is True
    
    data = {"payload": "I like cats!"}
    result = model.inference(data)
    assert result[0]["label"] == "positive"
    assert isinstance(result[0]["score"], float), "The score is not a float"

def test_reranker_model(transformer_model_class, library_control, hardware_preference):
    model_id = "BAAI/bge-reranker-v2-m3"
    model_info = library_control.get_model_info_index(model_id)

    transformer_model_class.download(model_id, model_info)
    
    model = transformer_model_class(model_id)
    res = model.load(hardware_preference, model_info)
    assert res is True
    
    data = {
        "payload": [
            {"text": "What is AI islands?", "text_pair": "it is an island"},
            {"text": "What is AI islands?", "text_pair": "it is a desktop application for offline ML models"}
        ]
    }
    result = model.inference(data)
    assert len(result) == 2
    assert result[0].get("label") is not None
    assert isinstance(result[0]["score"], float), "The score is not a float"
    assert isinstance(result[1]["score"], float), "The score is not a float"

def test_zero_shot_classification_model(transformer_model_class, library_control, hardware_preference):
    model_id = "facebook/bart-large-mnli"
    model_info = library_control.get_model_info_index(model_id)

    transformer_model_class.download(model_id, model_info)
    
    model = transformer_model_class(model_id)
    res = model.load(hardware_preference, model_info)
    assert res is True
    
    candidate_labels = ["physics", "technology", "cat"]
    data = {
        "payload": "Apple just announced the newest iPhone X",
        "pipeline_config": {
            "candidate_labels": candidate_labels
        }
    }
    result = model.inference(data)
    assert result.get("sequence") == "Apple just announced the newest iPhone X" 
    assert len(result.get("labels")) == 3
    assert all(item in result.get("labels") for item in candidate_labels)
    assert isinstance(result["scores"][0], float), "The score is not a float"

def test_translation_model(transformer_model_class, library_control, hardware_preference):
    model_id = "facebook/nllb-200-distilled-600M"
    model_info = library_control.get_model_info_index(model_id)

    transformer_model_class.download(model_id, model_info)
    
    model = transformer_model_class(model_id)
    res = model.load(hardware_preference, model_info)
    assert res is True
    
    data = {
        "payload": "i like cats",
        "pipeline_config": {
            "tgt_lang": "zho_Hant"
        }
    }
    result = model.inference(data)
    assert result[0].get("translation_text") is not None
    assert isinstance(result[0]["translation_text"], str)
    
def test_tts_model(transformer_model_class, library_control, hardware_preference):
    model_id = "microsoft/speecht5_tts"
    model_info = library_control.get_model_info_index(model_id)

    transformer_model_class.download(model_id, model_info)
    
    model = transformer_model_class(model_id)
    res = model.load(hardware_preference, model_info)
    assert res is True
    
    data = {
        "payload": "I am hungry",
        "speaker_embedding_config": "female_1"
    }
    result = model.inference(data)
    assert result.get("audio_content") is not None
    assert isinstance(result["audio_content"], str)
    assert result.get("audio_url") is not None
    
def test_stt_model(transformer_model_class, library_control, hardware_preference):
    model_id = "openai/whisper-large-v3"
    model_info = library_control.get_model_info_index(model_id)

    transformer_model_class.download(model_id, model_info)
    
    model = transformer_model_class(model_id)
    res = model.load(hardware_preference, model_info)
    assert res is True
    
    data = {
        "payload": "data\\testing_data\\sample1.flac"
    }
    result = model.inference(data)
    assert result.get("text") is not None
    assert isinstance(result["text"], str)
