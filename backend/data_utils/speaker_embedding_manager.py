import torch
import json
from backend.core.config import SPEAKER_EMBEDDING_PATH, SPEAKER_EMBEDDING_DEFAULT_PATH
import logging


logger = logging.getLogger(__name__)

class SpeakerEmbeddingManager:

    @staticmethod
    def get_speaker_embedding(speaker_embedding_config: str | list, default_embedding_config: str) -> torch.Tensor:

        # if array is given, use the speaker embedding
        if speaker_embedding_config and isinstance(speaker_embedding_config, list):
            try:
                return torch.tensor(speaker_embedding_config).unsqueeze(0)
            except Exception as e:
                logger.error(f"Error while converting speaker embedding to tensor: {e}")

        # if str is given, search for the speaker embedding in the json file using the key
        elif speaker_embedding_config and isinstance(speaker_embedding_config, str):
            try:
                with open(SPEAKER_EMBEDDING_PATH, "r") as f:
                    speaker_embedding_dict = json.load(f)
                speaker_embedding = speaker_embedding_dict[speaker_embedding_config]
                return torch.tensor(speaker_embedding).unsqueeze(0)
            except KeyError:
                logger.error(f"Speaker embedding not found for the key: {speaker_embedding_config}")

        # if nothing is given, use the default speaker      
        try:
            with open(SPEAKER_EMBEDDING_PATH, "r") as f:
                speaker_embedding_dict = json.load(f)
            speaker_embedding = speaker_embedding_dict[default_embedding_config]
            return torch.tensor(speaker_embedding).unsqueeze(0)
        except Exception as e:
            logger.error(f"Error while loading default speaker embedding: {e}")
            raise e
        
    @staticmethod
    def add_speaker_embedding(embedding_id: str, embedding: list[float]):
        with open(SPEAKER_EMBEDDING_PATH, "r") as f:
            speaker_embedding_dict = json.load(f)
        speaker_embedding_dict.update({embedding_id: embedding})
        with open(SPEAKER_EMBEDDING_PATH, "w") as f:
            json.dump(speaker_embedding_dict, f, indent=4)
        return True
        
    @staticmethod
    def remove_speaker_embedding(embedding_id: str):
        with open(SPEAKER_EMBEDDING_PATH, "r") as f:
            speaker_embedding_dict = json.load(f)
        res = speaker_embedding_dict.pop(embedding_id, False)
        if res:
            with open(SPEAKER_EMBEDDING_PATH, "w") as f:
                json.dump(speaker_embedding_dict, f, indent=4) 
            return True
        else:
            raise KeyError(f"Speaker Embedding {embedding_id} is not found.")
        
    @staticmethod
    def list_speaker_embedding():
        with open(SPEAKER_EMBEDDING_PATH, "r") as f:
            speaker_embedding_dict = json.load(f)
        return speaker_embedding_dict

    @staticmethod
    def reset_speaker_embedding():
        with open(SPEAKER_EMBEDDING_DEFAULT_PATH, "r") as f:
            speaker_embedding_dict = json.load(f)
        with open(SPEAKER_EMBEDDING_PATH, "w") as f:
            json.dump(speaker_embedding_dict, f, indent=4)
        return speaker_embedding_dict
    
    @staticmethod
    def configure_speaker_embeddings(embeddings = dict[str, list[float]]):
        with open(SPEAKER_EMBEDDING_PATH, "w") as f:
            json.dump(embeddings, f, indent=4)
        return True 
