

class Playground:
    def __init__(self, ModelControl):
        self.model_control = ModelControl
        self.playground_id = None
        self.desciption = None
        self.models = []
        self.chain = []
        

    def load_chain(self):
        for model_id in self.chain:
            self.model_control.load_model(model_id)
            
    def inference(self, payload: str):
        input = payload
        for model in self.chain:
            input = model.inference(input)
        return input