from abc import ABC, abstractmethod

class BaseModel(ABC):
    
    @staticmethod
    @abstractmethod
    def download(self, *args):
        pass
    
    @abstractmethod
    def load(self, *args):
        pass
    
    @abstractmethod
    def inference(self, *args):
        pass
