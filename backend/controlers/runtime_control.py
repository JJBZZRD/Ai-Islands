from backend.data_utils import JSONHandler
from backend.core.config import RUNTIME_DATA_PATH
from backend.core.exceptions import FileReadError, FileWriteError
import logging

logger = logging.getLogger(__name__)

class RuntimeControl:
    """
    The RuntimeControl class provides static methods to initialize, retrieve, and update runtime data.
    It uses JSONHandler for reading and writing JSON files and logs relevant information during operations.
    """

    @staticmethod
    def _initialise_runtime_data():
        """
        Initializes the runtime data with an empty structure.

        Returns:
            bool: True if the operation is successful.

        Raises:
            FileWriteError: If the file cannot be written.
        """
        empty_runtime_data = {
            "playground": {},
            "download_log": {}
        }
        try:
            JSONHandler.write_json(RUNTIME_DATA_PATH, empty_runtime_data)
            logger.info("Runtime data is initialised")
            return True
        except FileWriteError as e:
            logger.error(f"Error initializing runtime data: {e}")
            raise e

    @staticmethod
    def get_runtime_data(info_type: str):
        """
        Retrieves runtime data of a specific type.

        Args:
            info_type (str): The type of runtime data to retrieve.

        Returns:
            dict: The runtime data of the specified type.

        Raises:
            FileReadError: If the file cannot be read.
        """
        try:
            runtime_data = JSONHandler.read_json(RUNTIME_DATA_PATH)
            logger.info("Successfully retrieved runtime data")
            target_data = runtime_data[info_type]
            logger.info(f"Runtime data of {info_type} is retrieved")
            return target_data
        except FileReadError as e:
            logger.error(f"Error retrieving runtime data: {e}")
            raise e

    @staticmethod
    def update_runtime_data(info_type: str, data: dict):
        """
        Updates runtime data of a specific type.

        Args:
            info_type (str): The type of runtime data to update.
            data (dict): The new data to update.

        Returns:
            bool: True if the operation is successful.

        Raises:
            FileReadError: If the file cannot be read.
            FileWriteError: If the file cannot be written.
        """
        try:
            runtime_data = JSONHandler.read_json(RUNTIME_DATA_PATH)
            runtime_data[info_type] = data
            JSONHandler.write_json(RUNTIME_DATA_PATH, runtime_data)
            logger.info(f"Runtime data of {info_type} is updated")
            return True
        except (FileReadError, FileWriteError) as e:
            logger.error(f"Error updating runtime data: {e}")
            raise e
