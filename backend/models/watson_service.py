import json
import logging
import os
from dotenv import load_dotenv
from .base_model import BaseModel
from backend.utils.ibm_cloud_account_auth import Authentication, ResourceService, AccountInfo
from ibm_watson import NaturalLanguageUnderstandingV1, TextToSpeechV1, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from pydub import AudioSegment
from backend.utils.watson_settings_manager import watson_settings

logger = logging.getLogger(__name__)

LIBRARY_PATH = "data/library.json"

class WatsonService(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        self.account_info = AccountInfo()
        self.nlu = None
        self.text_to_speech = None
        self.speech_to_text = None

    @staticmethod
    def download(model_id: str, model_info: dict):
        try:
            logger.info(f"Attempting to download Watson service: {model_id}")
            logger.info(f"Original model info: {json.dumps(model_info, indent=2)}")

            # Check if the required service is available in the account
            account_info = AccountInfo()
            resources = account_info.get_resource_list()

            # Output resource list to JSON file
            resource_list_path = os.path.join('data', 'downloads', 'watson', 'resource_list.json')
            with open(resource_list_path, 'w') as f:
                json.dump(resources, f, indent=4)
            logger.info(f"Resource list saved to {resource_list_path}")

            service_name = model_id.split('/')[-1]  # Extract service name from model_id
            service_available = False

            for resource in resources:
                resource_name = resource['name']
                if check_service(resource_name, service_name):
                    service_available = True
                    logger.info(f"Matched service: {resource_name}")
                    break

            if not service_available:
                logger.error(f"The required service '{service_name}' is not available in the account.")
                logger.error(f"Available services: {[resource['name'] for resource in resources]}")
                return None

            # Create directory for the service
            service_dir = os.path.join('data', 'downloads', 'watson', model_id)
            os.makedirs(service_dir, exist_ok=True)

            # Save original model info to model_info.json in the service directory
            with open(os.path.join(service_dir, 'model_info.json'), 'w') as f:
                json.dump(model_info, f, indent=4)

            # Create the new entry for library.json
            logger.info(f"Creating library entry for Watson service {model_id}")

            new_entry = model_info.copy()
            new_entry.update({
                "base_model": model_id,
                "dir": service_dir,
                "is_customised": False
            })

            logger.info(f"New library entry: {json.dumps(new_entry, indent=2)}")
            return new_entry
        except Exception as e:
            logger.error(f"Error adding Watson service {model_id}: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def load(self, device: str, model_info: dict):
        try:
            # Validate API key
            api_key = watson_settings.get("IBM_CLOUD_API_KEY")
            if not api_key:
                logger.error("IBM_CLOUD_API_KEY not found in settings")
                return False

            valid = self.account_info.auth._validate_api_key(api_key)
            if not valid:
                logger.error("Invalid IBM Cloud API key")
                return False

            config = model_info.get("config", {})
            service_name = config.get("service_name")

            if not service_name:
                logger.error(f"Service name not found for model ID: {self.model_id}")
                return False

            if "natural-language-understanding" in service_name.lower():
                self.nlu = self._init_nlu_service()
                if self.nlu:
                    self.nlu_config = config.get("features", {})
                return self.nlu is not None
            elif "text-to-speech" in service_name.lower():
                self.text_to_speech = self._init_text_to_speech_service()
                if self.text_to_speech:
                    self.tts_config = config
                return self.text_to_speech is not None
            elif "speech-to-text" in service_name.lower():
                self.speech_to_text = self._init_speech_to_text_service()
                if self.speech_to_text:
                    self.stt_config = config
                return self.speech_to_text is not None
            else:
                logger.error(f"Unknown service name: {service_name}")
                return False

        except Exception as e:
            logger.error(f"Error loading Watson service: {str(e)}")
            return False

    def _init_nlu_service(self):
        try:
            iam_token = self.account_info.get_iam_token()
            credentials = self.account_info.get_service_credentials(iam_token, "Natural Language Understanding")
            if credentials:
                authenticator = IAMAuthenticator(credentials['apikey'])
                nlu = NaturalLanguageUnderstandingV1(version='2021-08-01', authenticator=authenticator)
                nlu.set_service_url(credentials['url'])
                return nlu
            else:
                raise Exception("Failed to retrieve or create NLU service credentials.")
        except Exception as e:
            logger.error(f"Error initializing NLU service: {str(e)}")
            return None

    def _init_text_to_speech_service(self):
        try:
            iam_token = self.account_info.get_iam_token()
            credentials = self.account_info.get_service_credentials(iam_token, "Text to Speech")
            if credentials:
                authenticator = IAMAuthenticator(credentials['apikey'])
                text_to_speech = TextToSpeechV1(authenticator=authenticator)
                text_to_speech.set_service_url(credentials['url'])
                return text_to_speech
            else:
                raise Exception("Failed to retrieve or create Text to Speech service credentials.")
        except Exception as e:
            logger.error(f"Error initializing Text to Speech service: {str(e)}")
            return None

    def _init_speech_to_text_service(self):
        try:
            iam_token = self.account_info.get_iam_token()
            credentials = self.account_info.get_service_credentials(iam_token, "Speech to Text")
            if credentials:
                authenticator = IAMAuthenticator(credentials['apikey'])
                speech_to_text = SpeechToTextV1(authenticator=authenticator)
                speech_to_text.set_service_url(credentials['url'])
                return speech_to_text
            else:
                raise Exception("Failed to retrieve or create Speech to Text service credentials.")
        except Exception as e:
            logger.error(f"Error initializing Speech to Text service: {str(e)}")
            return None
    
    def inference(self, data: dict):
        try:
            if self.nlu:
                text = data.get('payload')
                analysis_type = data.get('analysis_type', 'all')
                if not text:
                    raise ValueError("Text is required for NLU analysis")
                return self.analyze_text(text, analysis_type)
            elif self.text_to_speech:
                text = data.get('payload')
                voice = data.get('voice', self.tts_config.get('voice'))
                accept = data.get('accept', 'audio/wav')
                pitch = str(data.get('pitch', self.tts_config.get('pitch', 0)))
                speed = str(data.get('speed', self.tts_config.get('speed', 0)))
                if not text:
                    raise ValueError("Text is required for text-to-speech synthesis")
                return self.synthesize_text(text, voice, accept, pitch, speed)
            elif self.speech_to_text:
                file_path = data.get('file_path')
                if not file_path:
                    raise ValueError("File path is required for speech-to-text transcription")
                return self.transcribe_audio(file_path)
            else:
                raise ValueError("No Watson service has been initialized")
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            return {"error": str(e)}

    # NLU service method
    def analyze_text(self, text, analysis_type):
        if self.nlu is None:
            logger.error("NLU service is not initialized.")
            return None

        features = {}
        if analysis_type == 'all':
            for feature, enabled in self.nlu_config.items():
                if enabled:
                    features[feature] = {}
        elif analysis_type in self.nlu_config and self.nlu_config[analysis_type]:
            features[analysis_type] = {}
        else:
            logger.error(f"Invalid analysis type: {analysis_type}")
            return None

        if not features:
            logger.error("No features enabled for analysis.")
            return None

        try:
            response = self.nlu.analyze(text=text, features=features).get_result()
            return response
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return None

    # Text to Speech service method
    def synthesize_text(self, text, voice=None, accept='audio/wav', pitch=None, speed=None):
        if self.text_to_speech is None:
            logger.error("Text to Speech service is not initialized.")
            return {"error": "Text to Speech service is not initialized."}

        try:
            voice = voice or self.tts_config.get('voice', 'en-US_AllisonV3Voice')
            pitch = pitch or self.tts_config.get('pitch', '0')
            speed = speed or self.tts_config.get('speed', '0')

            ssml_text = f"<prosody pitch='{pitch}%' rate='{speed}%'>{text}</prosody>"
            response = self.text_to_speech.synthesize(
                ssml_text,
                voice=voice,
                accept=accept
            ).get_result().content

            model_dir = os.path.join('data', 'downloads', 'watson', self.model_id)
            audio_path = os.path.join(model_dir, "output.wav")

            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            with open(audio_path, "wb") as audio_file:
                audio_file.write(response)

            return {
                "status": "success",
                "audio_path": audio_path,
                "voice": voice,
                "pitch": pitch,
                "speed": speed
            }
        except Exception as e:
            logger.error(f"Error synthesizing text: {str(e)}")
            return {"error": f"Error synthesizing text: {str(e)}"}
    
    # Text to Speech service method
    def list_voices(self):
        if self.text_to_speech is None:
            logger.error("Text to Speech service is not initialized.")
            return []

        try:
            voices = self.text_to_speech.list_voices().get_result()
            return [voice['name'] for voice in voices['voices']]
        except Exception as e:
            logger.error(f"Error listing voices: {str(e)}")
            return []
        
    # Audio to Text service method
    def transcribe_audio(self, file_path):
        if self.speech_to_text is None:
            logger.error("Speech to Text service is not initialized.")
            return {"error": "Speech to Text service is not initialized."}

        try:
            # Use the model from the config, or default to 'en-US_BroadbandModel'
            model = self.stt_config.get('model', 'en-US_BroadbandModel')
            content_type = self.stt_config.get('content_type', 'audio/wav')

            # Convert audio to WAV if it's not already
            if not file_path.endswith('.wav'):
                audio = AudioSegment.from_file(file_path)
                wav_path = file_path.rsplit('.', 1)[0] + '.wav'
                audio.export(wav_path, format='wav')
                file_path = wav_path

            with open(file_path, 'rb') as audio_file:
                response = self.speech_to_text.recognize(
                    audio=audio_file,
                    content_type=content_type,
                    model=model
                ).get_result()

            transcriptions = response['results']
            transcription_text = " ".join([result['alternatives'][0]['transcript'] for result in transcriptions])

            return {
                "status": "success",
                "transcription": transcription_text,
                "model": model
            }
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return {"error": f"Error transcribing audio: {str(e)}"}
    
    # Speech to Text service method
    def list_stt_models(self):
        if self.speech_to_text is None:
            logger.error("Speech to Text service is not initialized.")
            return []
        try:
            models = self.speech_to_text.list_models().get_result()
            return [model['name'] for model in models['models']]
        except Exception as e:
            logger.error(f"Error listing STT models: {str(e)}")
            return []
    
    

    



# ------------- LOCAL METHODS -------------

def check_service(resource_name, service_keyword):
    resource_name_normalized = resource_name.lower().replace(' ', '').replace('-', '')
    service_keyword_normalized = service_keyword.lower().replace(' ', '').replace('-', '')
    return service_keyword_normalized in resource_name_normalized