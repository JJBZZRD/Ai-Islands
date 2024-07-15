from abc import ABC, abstractmethod

class BaseModel(ABC):
    
    @abstractmethod
    def download(self, *args):
        pass
    
    @abstractmethod
    def load(self, *args):
        pass
