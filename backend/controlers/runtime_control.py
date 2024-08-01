from backend.data_utils import JSONHandler
from backend.core.config import RUNTIME_DATA_PATH
import logging


logger = logging.getLogger(__name__)


class RuntimeControl:
    
    @staticmethod
    def initialise_runtime_data():
        empty_runtime_data = {
            "playground": {}
        }
        JSONHandler.write_json(RUNTIME_DATA_PATH, empty_runtime_data)
        logger.info("Runtime data is initialised")
        return True
    
    @staticmethod
    def get_runtime_data(info_type: str):
        runtime_data = JSONHandler.read_json(RUNTIME_DATA_PATH)
        logger.info(f"Successfully retrieved runtime data")
        target_data = runtime_data[info_type]
        logger.info(f"Runtime data of {info_type} is retrieved")
        return target_data
    
    @staticmethod
    def update_runtime_data(info_type: str, data: dict):

        runtime_data = JSONHandler.read_json(RUNTIME_DATA_PATH)

        runtime_data[info_type] = data

        JSONHandler.write_json(RUNTIME_DATA_PATH, runtime_data)
        logger.info(f"Runtime data of {info_type} is updated")
        return True
        