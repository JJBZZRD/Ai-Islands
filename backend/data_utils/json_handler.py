import json
import logging
from typing import Any, Dict
from backend.core.exceptions import FileReadError, FileWriteError

logger = logging.getLogger(__name__)

class JSONHandler:
    """
    JSONHandler class provides static methods to read, write, and update JSON files.
    It handles exceptions and logs relevant information during file operations.
    """

    @staticmethod
    def read_json(file_path: str) -> Dict[str, Any]:
        """
        Reads a JSON file and returns its content as a dictionary.

        Args:
            file_path (str): The path to the JSON file.

        Returns:
            Dict[str, Any]: The content of the JSON file.

        Raises:
            FileReadError: If the file is not found, cannot be decoded, or any other error occurs.
        """
        try:
            logger.info(f"Attempting to read JSON file at: {file_path}")
            with open(file_path, 'r') as f:
                data = json.load(f)
                logger.info(f"Successfully read JSON file at: {file_path}")
                return data
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise FileReadError(f"Error JSON file not found: {file_path}")
        except TypeError as e:
            logger.error(f"Error decoding JSON file: {e}")
            raise FileReadError(f"Error decoding JSON file: {file_path}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise FileReadError(f"Unexpected error reading JSON file {file_path}: {e}")

    @staticmethod
    def write_json(file_path: str, data: Dict[str, Any]) -> bool:
        """
        Writes a dictionary to a JSON file.

        Args:
            file_path (str): The path to the JSON file.
            data (Dict[str, Any]): The data to write to the JSON file.

        Returns:
            bool: True if the operation is successful.

        Raises:
            FileWriteError: If the file cannot be written, encoded, or any other error occurs.
        """
        try:
            logger.info(f"Attempting to write JSON file at: {file_path}")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
                logger.info(f"Successfully wrote JSON file at: {file_path}")
            return True
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise FileWriteError(f"Error JSON file not found: {file_path}")
        except TypeError as e:
            logger.error(f"Error encoding JSON file: {e}")
            raise FileWriteError(f"Error encoding JSON file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error writing JSON file: {e}")
            raise FileWriteError(f"Error writing JSON file {file_path}: {e}")
