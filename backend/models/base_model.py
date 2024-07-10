class BaseModel:
    def load(self, model_path: str):
        raise NotImplementedError("Load method not implemented")

    def process_request(self, request_payload: dict):
        raise NotImplementedError("process_request method not implemented")
