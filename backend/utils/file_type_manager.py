from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
import pandas as pd
import docx
import logging

logger = logging.getLogger(__name__)

class FileHandler(ABC):
    @abstractmethod
    def read_file(self, file_path: Path) -> List[str]:
        pass

class CSVHandler(FileHandler):
    def read_file(self, file_path: Path) -> List[str]:
        df = pd.read_csv(file_path)
        return df.apply(lambda row: ' '.join([f"{col}: {val}" for col, val in row.items()]), axis=1).tolist()

class TXTHandler(FileHandler):
    def read_file(self, file_path: Path) -> List[str]:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [file.read()]

class DOCXHandler(FileHandler):
    def read_file(self, file_path: Path) -> List[str]:
        doc = docx.Document(file_path)
        return ['\n'.join([paragraph.text for paragraph in doc.paragraphs])]

class FileTypeManager:
    def __init__(self):
        self.handlers = {
            'csv': CSVHandler(),
            'txt': TXTHandler(),
            'md': TXTHandler(),
            'docx': DOCXHandler(),
            'doc': DOCXHandler(),
        }

    def get_handler(self, file_extension: str) -> FileHandler:
        handler = self.handlers.get(file_extension.lower())
        if not handler:
            raise ValueError(f"Unsupported file type: {file_extension}")
        return handler

    def read_file(self, file_path: Path) -> List[str]:
        file_extension = file_path.suffix[1:].lower()
        handler = self.get_handler(file_extension)
        return handler.read_file(file_path)