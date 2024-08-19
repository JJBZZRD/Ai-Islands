import os
from dotenv import load_dotenv, set_key, find_dotenv
from threading import Lock

class WatsonSettingsManager:
    _instance = None
    _lock = Lock()
    DEFAULT_LOCATION = "eu-gb"  # Default location placeholder
    DEFAULT_ENV_VARS = {
        'IBM_CLOUD_API_KEY': '',
        'IBM_CLOUD_MODELS_URL': f"https://{DEFAULT_LOCATION}.ml.cloud.ibm.com",
        'IBM_CLOUD_NLU_URL': f"https://api.{DEFAULT_LOCATION}.natural-language-understanding.watson.cloud.ibm.com",
        'IBM_CLOUD_TEXT_TO_SPEECH_URL': f"https://api.{DEFAULT_LOCATION}.text-to-speech.watson.cloud.ibm.com",
        'IBM_CLOUD_SPEECH_TO_TEXT_URL': f"https://api.{DEFAULT_LOCATION}.speech-to-text.watson.cloud.ibm.com",
        'IBM_CLOUD_PROJECTS_URL': f"https://api.{DEFAULT_LOCATION}.dataplatform.cloud.ibm.com",
        'USER_PROJECT_ID': ''
    }

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WatsonSettingsManager, cls).__new__(cls)
                cls._instance.env_file = find_dotenv()
                if not cls._instance.env_file:
                    cls._instance.create_default_env()
                cls._instance.reload()
            return cls._instance

    def create_default_env(self):
        self.env_file = '.env'
        with open(self.env_file, 'w') as f:
            for key, value in self.DEFAULT_ENV_VARS.items():
                f.write(f"{key}={value}\n")
        print(f"Created default .env file at {os.path.abspath(self.env_file)}")

    def reload(self):
        load_dotenv(self.env_file, override=True)

    def get(self, key: str, default: str = None) -> str:
        return os.getenv(key, default)

    def set(self, key: str, value: str):
        set_key(self.env_file, key, value)
        if value == "":
            os.environ[key] = ""
        else:
            os.environ[key] = value

    def update_location(self, new_location: str):
        location = new_location if new_location else self.DEFAULT_LOCATION
        base_urls = {
            'IBM_CLOUD_MODELS_URL': f"https://{location}.ml.cloud.ibm.com",
            'IBM_CLOUD_NLU_URL': f"https://api.{location}.natural-language-understanding.watson.cloud.ibm.com",
            'IBM_CLOUD_TEXT_TO_SPEECH_URL': f"https://api.{location}.text-to-speech.watson.cloud.ibm.com",
            'IBM_CLOUD_SPEECH_TO_TEXT_URL': f"https://api.{location}.speech-to-text.watson.cloud.ibm.com",
            'IBM_CLOUD_PROJECTS_URL': f"https://api.{location}.dataplatform.cloud.ibm.com"
        }
        for key, url in base_urls.items():
            self.set(key, url)

    def get_all_settings(self):
        return {
            'IBM_CLOUD_API_KEY': self.get('IBM_CLOUD_API_KEY'),
            'IBM_CLOUD_MODELS_URL': self.get('IBM_CLOUD_MODELS_URL'),
            'IBM_CLOUD_NLU_URL': self.get('IBM_CLOUD_NLU_URL'),
            'IBM_CLOUD_TEXT_TO_SPEECH_URL': self.get('IBM_CLOUD_TEXT_TO_SPEECH_URL'),
            'IBM_CLOUD_SPEECH_TO_TEXT_URL': self.get('IBM_CLOUD_SPEECH_TO_TEXT_URL'),
            'IBM_CLOUD_PROJECTS_URL': self.get('IBM_CLOUD_PROJECTS_URL'),
            'USER_PROJECT_ID': self.get('USER_PROJECT_ID')
        }

watson_settings = WatsonSettingsManager()