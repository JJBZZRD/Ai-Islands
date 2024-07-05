from models.transformer_model import TransformerModel
from models.utlralytics_model import UltralyticsModel
from models.watson_model import WatsonModel
import multiprocessing
import json
from data_utils.json_handler import JSONHandler

# TODO: figure out the child process handling and the required imports

class ModelControl:
    def __init__(self):
        self.models = []
        self.json_handler = JSONHandler()

    # this should create an instance of the asscoiated model class in a child process and call the download method 
    # from said instance.
    # It needs to take the model_id and the required imports as arguments. A utility function could be used to process
    # json data.
    # Once the download is complete, the child process should terminate.
    def download_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        if model_info.get('is_online', False):
            print(f"Model {model_id} is online and does not require downloading.")
            return True

        def download_process(model_class, model_id):
            model = model_class()
            model.download(model_id)

        model_class = self._get_model_class(model_info['model_source'])
        process = multiprocessing.Process(target=download_process, args=(model_class, model_id))
        process.start()
        process.join()
        return True

    # this should create an instance of the asscoiated model class in a child process and call the load method 
    # from said instance.
    # It needs to take the model_id and the required imports as arguments.
    # A utility function could be used to process json data.
    def load_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        def load_process(model_class, model_id):
            model = model_class()
            model.load(model_id)
            return model

        model_class = self._get_model_class(model_info['model_source'])
        process = multiprocessing.Process(target=load_process, args=(model_class, model_id))
        process.start()
        self.models.append({'model_id': model_id, 'process': process})
        return True

    # This should unload the model from the self.models list if it present by killing the child process and removing it from the list.
    # It needs to take the model_id as an argument.
    def unload_model(self, model_id: str):
        for model in self.models:
            if model['model_id'] == model_id:
                model['process'].terminate()
                self.models.remove(model)
                return True
        return False
    
    # This should return a list of all the models that are currently loaded.
    # It needs to return the list of model_ids
    def list_active_models(self):
        return [model['model_id'] for model in self.models]

    # This should delete the model from the download folder and the model library.
    def delete_model(self, model_id: str):
        model_info = self._get_model_info(model_id)
        if not model_info:
            return False

        # Remove from downloaded models
        downloaded_models = self.json_handler.read_json('data/downloaded_models.json')
        downloaded_models = [model for model in downloaded_models if model['model_id'] != model_id]
        self.json_handler.write_json('data/downloaded_models.json', downloaded_models)

        # Remove from model library
        library = self.json_handler.read_json('data/library.json')
        library = [model for model in library if model['model_id'] != model_id]
        self.json_handler.write_json('data/library.json', library)

        return True

    def _get_model_info(self, model_id: str):
        model_index = self.json_handler.read_json('data/model_index.json')
        return next((model for model in model_index if model['model_id'] == model_id), None)

    def _get_model_class(self, model_source: str):
        if model_source == 'transformers':
            return TransformerModel
        elif model_source == 'ultralytics':
            return UltralyticsModel
        elif model_source == 'watson':
            return WatsonModel
        else:
            raise ValueError(f"Unknown model source: {model_source}")
