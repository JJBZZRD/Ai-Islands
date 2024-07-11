from core.config import MODEL_INDEX_PATH
from core.logging import logger
from data_utils.json_handler import JSONHandler


def main():

    try:
        model_index = JSONHandler.read_json(MODEL_INDEX_PATH)
    except Exception as e:
        logger.error(f"Error loading model index: {e}")
        return

    logger.info("Available Models:")
    for model in model_index:
        logger.info(f"Model ID: {model['Model ID']}, Source: {', '.join(model['Model Source'])}")

    model_id = input("Enter the Model ID to load: ")
    if model_id in [model['Model ID'] for model in model_index]:
        try:
            logger.info(f"Started loading model {model_id} in a separate process.")
        except Exception as e:
            logger.error(f"Error starting model process: {e}")
    else:
        logger.warning("Invalid Model ID")

if __name__ == "__main__":
    main()
