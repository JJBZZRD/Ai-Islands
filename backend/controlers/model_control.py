from models.transformer_model import TransformerModel
from models.utlralytics_model import UltralyticsModel
from models.watson_model import WatsonModel

# TODO: figure out the child process handling and the required imports

class ModelControl:
    def __init__(self):
        self.models = []

    def download_model(self, model_id: str):
        # this should create an instance of the asscoiated model class in a child process and call the download method 
        # from said instance.
        # It needs to take the model_id and the required imports as arguments. A utility function could be used to process
        # json data.
        pass

    def load_model(self, model_id: str):
        # this should create an instance of the asscoiated model class in a child process and call the load method 
        # from said instance.
        # It needs to take the model_id and the required imports as arguments.
        # A utility function could be used to process json data.
        pass

    def unload_model(self, model_id: str):
        # This should unload the model from the self.models list if it present by killing the child process and removing it from the list.
        # It needs to take the model_id as an argument.
        pass
    
    def list_active_models(self):
        # This should return a list of all the models that are currently loaded.
        # It needs to return the list of model_ids
        pass

    def delete_model(self, model_id: str):
        # This should delete the model from the download folder and the model library.
        pass