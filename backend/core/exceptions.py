class FileReadError(Exception):
    """Exception raised when a file cannot be read."""
    def __init__(self, message="File cannot be read"):
        self.message = message
        super().__init__(self.message)

class FileWriteError(Exception):
    """Exception raised when a file cannot be written."""
    def __init__(self, message="File cannot be written"):
        self.message = message
        super().__init__(self.message)

class ModelError(Exception):
    """Exception raised when there is an error with a model."""
    def __init__(self, message="Error with model"):
        self.message = message
        super().__init__(self.message)

class PlaygroundError(Exception):
    """Exception raised when there is an error with the playground."""
    def __init__(self, message="Error with playground"):
        self.message = message
        super().__init__(self.message)

class PlaygroundAlreadyExistsError(PlaygroundError):
    """Exception raised when a playground already exists."""
    def __init__(self, playground_id=""):
        self.message = f"Playground with ID {playground_id} already exists"
        super().__init__(self.message)

class ChainNotCompatibleError(PlaygroundError):
    """Exception raised when models in the chain are not compatible."""
    def __init__(self, message="Chain is not compatible"):
        self.message = message
        super().__init__(self.message)

class ModelNotAvailableError(ModelError):
    """Exception raised when a model is not currently available in repository (currently on maintenance or smth)."""
    def __init__(self, message="Model is not available"):
        self.message = message
        super().__init__(self.message)

