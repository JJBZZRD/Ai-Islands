import json
import logging
import os
from .base_model import BaseModel
from backend.utils.ibm_cloud_account_auth import Authentication, ResourceService, AccountInfo
from ibm_watson import NaturalLanguageUnderstandingV1, TextToSpeechV1, SpeechToTextV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from pydub import AudioSegment

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
            resource_list_path = os.path.join('data', 'resource_list.json')
            with open(resource_list_path, 'w') as f:
                json.dump(resources, f, indent=4)
            logger.info(f"Resource list saved to {resource_list_path}")

            service_name = model_id.split('/')[-1]  # Extract service name from model_id
            service_available = False

            for resource in resources:
                resource_name = resource['name']
                if check_service(resource_name, service_name):
                    service_available = True
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
                "dir": service_dir,
                "is_customised": False,
                "config": {
                    "service_name": service_name,
                }
            })

            logger.info(f"New library entry: {json.dumps(new_entry, indent=2)}")
            return new_entry
        except Exception as e:
            logger.error(f"Error adding Watson service {model_id}: {str(e)}")
            logger.exception("Full traceback:")
            return None

    def load(self, model_path: str, device: str, required_classes=None, pipeline_tag: str = None):
        try:
            # Load the model info from the library
            with open(LIBRARY_PATH, "r") as file:
                library = json.load(file)
                model_info = library.get(self.model_id, {})
                service_name = model_info.get("config", {}).get("service_name")

            if not service_name:
                logger.error(f"Service name not found for model ID: {self.model_id}")
                return False

            if service_name == "natural-language-understanding":
                self.nlu = self._init_nlu_service()
                return self.nlu is not None
            elif service_name == "text-to-speech":
                self.text_to_speech = self._init_text_to_speech_service()
                return self.text_to_speech is not None
            elif service_name == "speech-to-text":
                self.speech_to_text = self._init_speech_to_text_service()
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

    def analyze_text(self, text, analysis_type):
        if self.nlu is None:
            logger.error("NLU service is not initialized.")
            return None

        features = {analysis_type: {}}
        if analysis_type == 'all':
            features = {
                'sentiment': {}, 'emotion': {}, 'entities': {}, 'keywords': {},
                'categories': {}, 'concepts': {}, 'relations': {}, 'semantic_roles': {}
            }
        try:
            response = self.nlu.analyze(text=text, features=features).get_result()
            return response
        except Exception as e:
            logger.error(f"Error analyzing text: {str(e)}")
            return None

    def synthesize_text(self, text, voice='en-US_AllisonV3Voice', accept='audio/wav', pitch='0', speed='0'):
        if self.text_to_speech is None:
            logger.error("Text to Speech service is not initialized.")
            return None

        try:
            ssml_text = f"<prosody pitch='{pitch}%' rate='{speed}%'>{text}</prosody>"
            response = self.text_to_speech.synthesize(
                ssml_text,
                voice=voice,
                accept=accept
            ).get_result().content

            audio_path = "temp/output.wav"
            with open(audio_path, "wb") as audio_file:
                audio_file.write(response)

            return audio_path
        except Exception as e:
            logger.error(f"Error synthesizing text: {str(e)}")
            return None

    def transcribe_audio(self, file_path):
        if self.speech_to_text is None:
            logger.error("Speech to Text service is not initialized.")
            return None

        try:
            if not file_path.endswith('.wav'):
                audio = AudioSegment.from_file(file_path)
                wav_path = file_path.rsplit('.', 1)[0] + '.wav'
                audio.export(wav_path, format='wav')
                file_path = wav_path

            with open(file_path, 'rb') as audio_file:
                response = self.speech_to_text.recognize(
                    audio=audio_file,
                    content_type='audio/wav'
                ).get_result()

            transcriptions = response['results']
            transcription_text = " ".join([result['alternatives'][0]['transcript'] for result in transcriptions])

            return transcription_text
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return None

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

    def inference(self, data: dict):
        # This method should be implemented based on the specific use case
        pass

    def process_request(self, payload: dict):
        # This method should be implemented based on the specific use case
        pass

    def predict(self, text: str):
        # This method should be implemented based on the specific use case
        pass


# ------------- LOCAL METHODS -------------

def check_service(resource_name, service_keyword):
    return service_keyword.lower().replace(' ', '') in resource_name.lower().replace(' ', '')