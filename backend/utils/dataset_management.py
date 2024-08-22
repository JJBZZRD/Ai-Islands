import logging
import shutil
from pathlib import Path
import json
from backend.core.config import DATASETS_DIR
from backend.utils.file_type_manager import FileTypeManager

logger = logging.getLogger(__name__)

class DatasetFileManagement:
    def __init__(self):
        self.file_type_manager = FileTypeManager()

    def upload_dataset(self, file_path: str):
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            dataset_name = source_path.stem
            dataset_folder = Path(DATASETS_DIR) / dataset_name
            dataset_folder.mkdir(parents=True, exist_ok=True)

            destination_path = dataset_folder / source_path.name
            shutil.copy2(source_path, destination_path)

            return {"message": f"Dataset uploaded successfully to {destination_path}"}
        except Exception as e:
            logger.error(f"Error uploading dataset: {str(e)}")
            raise

    def preview_dataset(self, dataset_name: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name
            
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

            for file in dataset_path.iterdir():
                if file.is_file():
                    preview_content = self.file_type_manager.read_file(file)
                    file_type = file.suffix.lower()
                    if file_type == '.csv' and preview_content:
                        # Preserve CSV formatting without processing
                        preview_content = preview_content[:10]
                    return {
                        "file_type": file_type,
                        "content": preview_content[:10] if isinstance(preview_content, list) else [preview_content[:1000]]
                    }

            raise FileNotFoundError(f"No files found in dataset directory: {dataset_path}")
        except Exception as e:
            logger.error(f"Error previewing dataset: {str(e)}")
            raise

    def get_dataset_processing_status(self, dataset_name: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_name}")

            default_processed = (dataset_path / "default").exists()
            chunked_processed = (dataset_path / "chunked").exists()

            return {
                "default_processed": default_processed,
                "chunked_processed": chunked_processed
            }
        except Exception as e:
            logger.error(f"Error getting dataset processing status: {str(e)}")
            raise

    def delete_dataset(self, dataset_name: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name
            if not dataset_path.exists():
                raise FileNotFoundError(f"Dataset not found: {dataset_name}")

            shutil.rmtree(dataset_path)
            return {"message": f"Dataset {dataset_name} deleted successfully"}
        except Exception as e:
            logger.error(f"Error deleting dataset: {str(e)}")
            raise

    def get_dataset_processing_info(self, dataset_name: str, processing_type: str):
        try:
            dataset_path = Path(DATASETS_DIR) / dataset_name / processing_type
            info_file = dataset_path / "embedding_model_info.json"
            
            if not info_file.exists():
                raise FileNotFoundError(f"Processing info not found for {dataset_name} ({processing_type})")

            with open(info_file, 'r') as f:
                info = json.load(f)

            if processing_type == "chunked" and "chunking_settings" in info:
                chunk_method = info["chunking_settings"].get("chunk_method", "")
                if chunk_method in ["fixed_length", "sentence", "paragraph"]:
                    info["chunking_settings"] = {
                        "use_chunking": True,
                        "chunk_method": chunk_method,
                        "chunk_size": info["chunking_settings"].get("chunk_size", 1000),
                        "chunk_overlap": info["chunking_settings"].get("chunk_overlap", 100),
                    }
                elif chunk_method == "csv_row":
                    info["chunking_settings"] = {
                        "use_chunking": True,
                        "chunk_method": "csv_row",
                        "rows_per_chunk": info["chunking_settings"].get("rows_per_chunk", 1),
                        "csv_columns": info["chunking_settings"].get("csv_columns", []),
                    }

            return info
        except Exception as e:
            logger.error(f"Error getting dataset processing info: {str(e)}")
            raise

    def list_datasets_names(self):
        try:
            datasets_dir = Path(DATASETS_DIR)
            datasets = [d.name for d in datasets_dir.iterdir() if d.is_dir()]
            logger.info(f"Found {len(datasets)} datasets")
            return {"datasets": datasets}
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return {"datasets": []}

    def list_datasets(self):
        try:
            datasets_dir = Path(DATASETS_DIR)
            datasets = []
            for d in datasets_dir.iterdir():
                if d.is_dir():
                    for file in d.iterdir():
                        if file.is_file():
                            datasets.append(f"{d.name}{file.suffix}")
                            break  # Assume one file per dataset
            logger.info(f"Found {len(datasets)} datasets")
            return {"datasets": datasets}
        except Exception as e:
            logger.error(f"Error listing datasets: {e}")
            return {"datasets": []}