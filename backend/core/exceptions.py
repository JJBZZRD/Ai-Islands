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