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
        self.metadata_file = Path("data") / "metadata.json"
        if not self.metadata_file.exists():
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, 'w') as f:
                json.dump({}, f)

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

            # Update metadata
            self.update_dataset_metadata(dataset_name, {"default": False, "chunked": False})

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

    def update_dataset_metadata(self, dataset_name: str, processing_info: dict):
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if dataset_name not in metadata:
            metadata[dataset_name] = {}

        metadata[dataset_name].update(processing_info)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def get_dataset_metadata(self, dataset_name: str):
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        if dataset_name not in metadata:
            raise FileNotFoundError(f"Metadata not found for dataset: {dataset_name}")
        
        return metadata[dataset_name]

    def check_rag_settings_feasibility(self, dataset_name: str, use_chunking: bool):
        try:
            metadata = self.get_dataset_metadata(dataset_name)
            if use_chunking and not metadata.get('chunked', False):
                return False, "Chunked processing is requested but the dataset has not been processed with chunking."
            elif not use_chunking and not metadata.get('default', False):
                return False, "Default processing is requested but the dataset has not been processed without chunking."
            return True, None
        except FileNotFoundError:
            return False, f"Dataset {dataset_name} not found or has not been processed."

    def get_datasets_tracker_info(self):
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
            
            processed_datasets = {
                name: info for name, info in metadata.items() 
                if info.get('default', False) or info.get('chunked', False)
            }
            
            return {"datasets": processed_datasets}
        except Exception as e:
            logger.error(f"Error getting datasets with processing info: {str(e)}")
            raise
    
    # def get_dataset_report(self, dataset_name: str, processing_type: str):
    #     logger.info(f"Retrieving report for dataset: {dataset_name}, processing type: {processing_type}")
    #     dataset_dir = Path("Datasets") / dataset_name
    #     processing_dir = dataset_dir / processing_type
    #     report_path = processing_dir / f"{dataset_name}_processing_report.html"

    #     if not report_path.exists():
    #         logger.error(f"Report not found for dataset: {dataset_name}, processing type: {processing_type}")
    #         return None

    #     with open(report_path, 'r', encoding='utf-8') as f:
    #         report_content = f.read()

    #     return report_content

    def get_dataset_report(self, dataset_name: str, processing_type: str):
        logger.info(f"Retrieving report for dataset: {dataset_name}, processing type: {processing_type}")
        dataset_dir = Path(DATASETS_DIR) / dataset_name
        processing_dir = dataset_dir / processing_type
        report_path = processing_dir / f"{dataset_name}_processing_report.html"

        if not report_path.exists():
            logger.error(f"Report not found for dataset: {dataset_name}, processing type: {processing_type}")
            return None

        return report_path