

class Playground:
    def __init__(self, ModelControl):
        self.model_control = ModelControl
        self.playground_id = None
        self.desciption = None
        self.models = []
        self.chain = []
        

    def load_playground(self, playground_id: str, playground_info: dict):
        self.playground_id = playground_id
        self.description = playground_info.get("description", "")
        self.models = playground_info.get("models", [])
        self.chain = playground_info.get("chain", [])
    
    def load_playground_chain(self):
        for model_id in self.chain:
            self.model_control.load_model(model_id)
        return True
    
    
    def unload_model(self, model_id: str):
        return self.model_control.unload_model(model_id)
    
    def inference(self, payload: str):
        input = payload
        for model in self.chain:
            input = model.inference(input)
        return input
    
    # def stop_playground_chain(self):
    #     for model_id in self.chain:
    #         result = self.model_control.unload_model(model_id)
    #         result = result and True
    #     return result