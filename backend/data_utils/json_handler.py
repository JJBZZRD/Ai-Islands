"""import json
from typing import Any, Dict, List
from core.exceptions import FileReadError, FileWriteError
from core.config import MODEL_INDEX_PATH, DOWNLOADED_MODELS_PATH

class JSONHandler:
    def read_json(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileReadError(f"Error reading JSON file {file_path}")
        except json.JSONDecodeError as e:
            raise FileReadError(f"Error decoding JSON file {file_path}: {e}")

    def write_json(self, file_path, data):
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            raise FileWriteError(f"Error writing JSON file {file_path}: {e}")

    def update_json(file_path: str, update_data: Dict[str, Any]) -> None:
        try:
            current_data = JSONHandler.read_json(file_path)
            current_data.update(update_data)
            JSONHandler.write_json(file_path, current_data)
        except (FileReadError, FileWriteError) as e:
            raise e

    def append_to_json_list(file_path: str, new_item: Any) -> None:
        try:
            current_data = JSONHandler.read_json(file_path)
            if not isinstance(current_data, list):
                raise ValueError("JSON file does not contain a list")
            current_data.append(new_item)
            JSONHandler.write_json(file_path, current_data)
        except (FileReadError, FileWriteError, ValueError) as e:
            raise e"""
import json
from typing import Any, Dict
from backend.core.exceptions import FileReadError, FileWriteError

class JSONHandler:
    def read_json(self, file_path):
        try:
            print(f"Attempting to read JSON file at: {file_path}")
            with open(file_path, 'r') as f:
                data = json.load(f)
                print(f"Successfully read JSON file at: {file_path}")
                return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            raise FileReadError(f"Error reading JSON file {file_path}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON file: {e}")
            raise FileReadError(f"Error decoding JSON file {file_path}: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise FileReadError(f"Unexpected error reading JSON file {file_path}: {e}")

    def write_json(self, file_path, data):
        try:
            print(f"Attempting to write JSON file at: {file_path}")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
                print(f"Successfully wrote JSON file at: {file_path}")
        except Exception as e:
            print(f"Error writing JSON file: {e}")
            raise FileWriteError(f"Error writing JSON file {file_path}: {e}")

    def update_json(self, file_path: str, update_data: Dict[str, Any]) -> None:
        try:
            current_data = self.read_json(file_path)
            current_data.update(update_data)
            self.write_json(file_path, current_data)
        except (FileReadError, FileWriteError) as e:
            print(f"Error updating JSON file: {e}")
            raise e

    def append_to_json_list(self, file_path: str, new_item: Any) -> None:
        try:
            current_data = self.read_json(file_path)
            if not isinstance(current_data, list):
                raise ValueError("JSON file does not contain a list")
            current_data.append(new_item)
            self.write_json(file_path, current_data)
        except (FileReadError, FileWriteError, ValueError) as e:
            print(f"Error appending to JSON list: {e}")
            raise e
