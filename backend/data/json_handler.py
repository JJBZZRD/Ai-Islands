import json
from typing import Any, Dict, List
from core.exceptions import FileReadError, FileWriteError

class JSONHandler:
    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise FileReadError(f"Error reading JSON file {file_path}: {str(e)}")

    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any]) -> None:
        try:
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
        except IOError as e:
            raise FileWriteError(f"Error writing to JSON file {file_path}: {str(e)}")

    @staticmethod
    def update_json(file_path: str, update_data: Dict[str, Any]) -> None:
        try:
            current_data = JSONHandler.read_json(file_path)
            current_data.update(update_data)
            JSONHandler.write_json(file_path, current_data)
        except (FileReadError, FileWriteError) as e:
            raise e

    @staticmethod
    def append_to_json_list(file_path: str, new_item: Any) -> None:
        try:
            current_data = JSONHandler.read_json(file_path)
            if not isinstance(current_data, list):
                raise ValueError("JSON file does not contain a list")
            current_data.append(new_item)
            JSONHandler.write_json(file_path, current_data)
        except (FileReadError, FileWriteError, ValueError) as e:
            raise e
