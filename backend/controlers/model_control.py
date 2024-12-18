import gc
import importlib
import logging
import multiprocessing
import os
import shutil
from backend.utils.process_vis_out import process_vision_output
from PIL import Image
import time
import subprocess

import torch

from backend.controlers.library_control import LibraryControl
from backend.controlers.runtime_control import RuntimeControl
from backend.core.exceptions import ModelError, ModelNotAvailableError
from backend.settings.settings_service import SettingsService
from backend.utils.helpers import install_packages, execute_script

import psutil
import GPUtil

logger = logging.getLogger(__name__)
class ModelControl:
    
    def __init__(self):
        """
        Initializes the ModelControl instance.
        Sets up the hardware preference, initializes the library control, and prepares the models dictionary.
        """
        self.models = {}
        settings_service = SettingsService()
        self.hardware_preference = settings_service.get_hardware_preference()  # Default will be CPU
        self.library_control = LibraryControl()
        
    @staticmethod
    def _download_process(conn, model_class, model_id, model_info, library_control):
        """
        Static method to handle the download process of a model in a separate process.
        
        Args:
            conn (multiprocessing.Connection): Connection object for inter-process communication.
            model_class (class): The class of the model to be downloaded.
            model_id (str): The ID of the model to be downloaded.
            model_info (dict): Information about the model.
            library_control (LibraryControl): Instance of LibraryControl to update the model library.
        """
        logger.info(f"Starting download for model {model_id}")
        start_time = time.time()
        try:
            # Call the corresponding model to download the model
            new_entry = model_class.download(model_id, model_info)
            # Update the library with the new entry
            library_control.update_library(model_id, new_entry)
            end_time = time.time()
            logger.info(f"Completed download for model {model_id} in {end_time - start_time:.2f} seconds")
            # Send success message to parent process
            conn.send("success")
        except ModelError as e:
            logger.error(f"Chile process _download_process get an error: {str(e)}")
            # Send error message to parent process
            conn.send({"error": e})

    @staticmethod
    def _load_process(model_class, conn, model_id, device, model_info, lock):
        """
        Static method to handle the loading process of a model in a separate process.
        
        Args:
            model_class (class): The class of the model to be loaded.
            conn (multiprocessing.Connection): Connection object for inter-process communication.
            model_id (str): The ID of the model to be loaded.
            device (torch.device): The device to load the model on (CPU or GPU).
            model_info (dict): Information about the model.
            lock (multiprocessing.Lock): Lock to ensure that only one request is processed at a time.
        """
        # instantiate the model class with model_id
        model = model_class(model_id=model_id)
        try:
            model.load(device=device, model_info=model_info)
            conn.send("Model loaded")
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {str(e)}")
            # Send error message to parent process
            conn.send(f"error: Failed to load model {model_id}: {str(e)}")
            return

        # A loop to keep the process alive
        while True:
            try:
                req = conn.recv()  # This will block until a message is received
                
                if req == "terminate":
                    conn.send("Terminating")
                    break
                elif isinstance(req, dict) and req.get("task") in ["inference", "train"]:
                    with lock:  # Use a context manager for the lock
                        if req["task"] == "inference":
                            logger.info(f"Running control inference for model {model_id}")
                            result = model.inference(req["data"])
                        conn.send(result)
                else:
                    logger.warning(f"Received unknown request: {req}")
                    conn.send({"error": "Unknown request"})
            except Exception as e:
                logger.error(f"Error in load process: {str(e)}")
                conn.send({"error": str(e)})

    def _download_model(self, model_id: str, auth_token: str = None):
        """
        Downloads a model by its ID and updates the model library.
        
        Args:
            model_id (str): The ID of the model to be downloaded.
            auth_token (str, optional): Authentication token for downloading the model. Defaults to None.
        
        Returns:
            dict: A message indicating the success of the download.
        
        Raises:
            ModelError: If there is an error during the download process.
            ValueError: If there is an error updating the library.
        """
        try:
            # Retrieve model info from the index
            model_info = self._get_model_info(model_id, "index")
            model_info.update({"auth_token": auth_token})

            # Install required packages
            install_packages(model_info.get('requirements', {}).get('required_packages', []))
            
            # Get the model class            
            model_class = self._get_model_class(model_id, "index")

            # Create a pipe for communication between parent and child processes
            parent_conn, child_conn = multiprocessing.Pipe()
            process = multiprocessing.Process(target=self._download_process, args=(child_conn, model_class, model_id, model_info, self.library_control))
            process.start()
            process.join()
            
            response = parent_conn.recv()
            if isinstance(response, dict) and "error" in response:
                if isinstance(response["error"], ModelNotAvailableError):
                    raise ModelNotAvailableError(f"Model {model_id} is currently not available in the repository. Please try again later.")
                else:
                    raise ModelError(str(response["error"]))
            
            logger.info(f"Model {model_id} downloaded successfully")
            # Check if the download was successful
            is_library_updated = self.library_control.get_model_info_library(model_id) is not None
            if is_library_updated:
                return {"message": f"Model {model_id} downloaded successfully"}
            else:
                raise ValueError(f"Failed to update library.json for model_id: {model_id}")
        except ModelNotAvailableError as e:
            logger.error(str(e))
            raise e
        except ModelError as e:
            logger.error(str(e))
            raise e
        except ValueError as e:
            logger.error(str(e))
            raise e
    
    def download_model(self, model_id: str, auth_token: str = None):
        args = ["-at", auth_token] if auth_token else []
        execute_script("backend/utils/model_download.py", model_id, *args)
        
        download_log = RuntimeControl.get_runtime_data("download_log")
        if "success" in download_log:
            return {"message": download_log["success"]}
        elif "error" in download_log:
            error_info = download_log["error"]
            if "error name" in error_info and "error message" in error_info:
                raise ModelError(f"Error: {error_info['error message']}")
            else:
                raise ModelError("Unexpected Error occured during model download") 


    def load_model(self, model_id: str):
        """
        Loads a model by its ID and starts a process for it.
        
        Args:
            model_id (str): The ID of the model to be loaded.
        
        Returns:
            bool: True if the model is loaded successfully, False otherwise.
        
        Raises:
            ModelError: If there is an error during the loading process.
            ValueError: If there is an error retrieving model information or class.
        """
        try:
            if self.is_model_loaded(model_id):
                logger.info(f"Model {model_id} is already loaded")
                return True
            
            model_info = self._get_model_info(model_id)
            logger.debug(f"Fetched model info: {model_info}")

            model_class = self._get_model_class(model_id, "library")
            model_dir = model_info['dir']
            is_online = model_info.get('is_online', False)
            base_model = model_info['base_model']

            if not os.path.exists(model_dir) and not is_online:
                logger.error(f"Model directory not found: {model_dir}")
                raise FileNotFoundError(f"Model directory not found: {model_dir}")

            device = torch.device("cuda" if self.hardware_preference == "gpu" and torch.cuda.is_available() else "cpu")
            logger.debug(f"Using device: {device}")

            lock = multiprocessing.Lock()
            parent_conn, child_conn = multiprocessing.Pipe()
            process = multiprocessing.Process(target=self._load_process, args=(model_class, child_conn, base_model, device, model_info, lock))
            process.start()

            response = parent_conn.recv()
            logger.debug(f"Received response from load process: {response}")

            if response == "Model loaded":
                self.models[model_id] = {'process': process, 'conn': parent_conn, 'model': model_class, 'pid': process.pid}
                logger.info(f"Model {model_id} loaded and process started.")
                return True
            elif isinstance(response, dict) and "error" in response:
                logger.error(f"Failed to load model {model_id}. Error: {response['error']}")
                raise ModelError(f"Failed to load model {model_id}. Error: {response['error']}")
            else:
                logger.error(f"Failed to load model {model_id}. Unexpected response: {response}")
                raise ModelError(f"Failed to load model {model_id}. Unexpected response: {response}")
        except ValueError as e:
            logger.error(str(e))
            raise e

    def unload_model(self, model_id: str):
        """
        Unloads a model by its ID and terminates its process.
        
        Args:
            model_id (str): The ID of the model to be unloaded.
        
        Returns:
            bool: True if the model is unloaded successfully, False otherwise.
        
        Raises:
            ModelError: If the model is active in a chain.
            KeyError: If the model is not found in active models.
        """
        if model_id in self.models:
            runtime_data = RuntimeControl.get_runtime_data("playground")
            
            if runtime_data.get(model_id) and len(runtime_data[model_id]) != 0:
                logger.info(f"Model {model_id} is active in a chain. Please stop the chain first.")
                raise ModelError(f"Model {model_id} is active in a chain. Please stop the chain first.")
        
            conn = self.models[model_id]['conn']
            conn.send("terminate")
            self.models[model_id]['process'].join()
            del self.models[model_id]
            gc.collect()
            logger.info(f"Model {model_id} unloaded and memory freed.")
            return True
        logger.error(f"Model {model_id} not found in active models.")
        return KeyError(f"Model {model_id} not found in active models.")
    
    def is_model_loaded(self, model_id: str):
        """
        Checks if a model is loaded.
        
        Args:
            model_id (str): The ID of the model to check.
        
        Returns:
            bool: True if the model is loaded, False otherwise.
        """
        return model_id in self.models
        
    def list_active_models(self):
        """
        Unloads a model by its ID and terminates its process.
        
        Args:
            model_id (str): The ID of the model to be unloaded.
        
        Returns:
            bool: True if the model is unloaded successfully, False otherwise.
        """
        active_models_info = [{"model_id": model, "process_alive": self.models[model]['process'].is_alive()} for model in self.models]
        logger.debug(f"Active models: {active_models_info}")
        return active_models_info
    
    def delete_model(self, model_id: str):
        
        try:
            model_info = self._get_model_info(model_id)
            base_model = model_info['base_model']
            
            if base_model == model_id:
                models_using_base = self.library_control.get_models_by_base_model(base_model)
                # Loop through models using the base model and delete them
                for dependent_model_id in models_using_base:
                    if self.is_model_loaded(dependent_model_id):
                        self.unload_model(dependent_model_id)
                        
                    self.library_control.delete_model(dependent_model_id)
                    logger.info(f"Deleted dependent model: {dependent_model_id}")
                
                model_dir = model_info['dir']
                if os.path.exists(model_dir):
                    shutil.rmtree(model_dir)
                    logger.info(f"Model {model_id} directory deleted")

                return {"message": f"Model {model_id} and its dependent models deleted"}
            else:
                if self.is_model_loaded(model_id):
                    self.unload_model(model_id)
                self.library_control.delete_model(model_id)
                return {"message": f"Model {model_id} deleted"}
        except ValueError as e:
            logger.error(str(e))
            return {"error": str(e)}

    def inference(self, inference_request):
        """
        Performs inference using a loaded model.
        
        Args:
            inference_request (dict): The inference request containing model ID and data.
        
        Returns:
            dict: The inference result.
        
        Raises:
            KeyError: If the model is not loaded.
            
        """
        try:
            model_id = inference_request['model_id']
        except KeyError:
            return {"error": f"Model {inference_request['model_id']} is not loaded. Please load the model first"}
        
        active_model = self.get_active_model(model_id)
        conn = active_model['conn']
        # Send the request to the child process
        req = inference_request
        req['task'] = "inference"
        conn.send(req)
        # Receive the response from the child process
        response = conn.recv()
        # Check if the response contains an error. If there is an error, raise it
        if "error" in response:
            raise ModelError(response["error"])
        
        return response
        
    def process_image(self, image_path, output, task):
        try:
            logger.info(f"Image path: {image_path}")
            logger.info(f"Output type: {type(output)}")
            logger.info(f"Output content: {output}")
            logger.info(f"Task: {task}")

            if not isinstance(output, (dict, list)):
                raise ValueError(f"Expected output to be dict or list, got {type(output)}")

            with Image.open(image_path) as img:
                processed_output = process_vision_output(img, output, task)
            
            return processed_output
        except Exception as e:
            logger.error(f"Error in process_image: {str(e)}")
            logger.error(f"Image path: {image_path}")
            logger.error(f"Output: {output}")
            logger.error(f"Task: {task}")
            raise ValueError(f"Error processing image: {str(e)}")
        
    
    def train_model(self, train_request):
        """
        Trains a loaded model.
        
        Args:
            train_request (dict): The training request containing model ID and training data.
        
        Returns:
            dict: The training result.
        
        Raises:
            KeyError: If the model is not loaded.
        """
        logger.info("train request:", train_request)
        model_id = train_request['model_id']
        data = train_request["data"]
        model_info = self._get_model_info(model_id)
        data["model_info"] = model_info
        data["hardware_preference"] = self.hardware_preference
        model_class = self._get_model_class(model_id, "library") 
        model = model_class(model_id=model_id) 

        result = model.train(data)
        
        logger.info("print result from train")
        logger.info(result)
        if "error" not in result:
            new_model_info = result["data"]["new_model_info"]
            new_model_id = new_model_info["model_id"]
        
            # Get the original model info
            original_model_info = self._get_model_info(model_id)
        
            # Create a new entry by copying the original model info and updating with new info
            updated_model_info = original_model_info.copy()
            updated_model_info.update(new_model_info)
        
            # Ensure that these fields are correctly set for the new model
            updated_model_info["base_model"] = new_model_id  
        
            # Add the new model to the library
            self.library_control.add_fine_tuned_model(updated_model_info)
            logger.info(f"New fine-tuned model {new_model_id} added to library")
        return result["data"], result["message"]
    
    def reset_model_config(self, model_id: str):
        try:
            reset_config = self.library_control.reset_model_config(model_id)

            if reset_config:
                if self.is_model_loaded(model_id):
                    self.unload_model(model_id)
                    self.load_model(model_id)

            return {"message": f"Model {model_id} configuration reset in library"}
        except KeyError:
            return {"error": f"Model {model_id} not found in library"}

    def configure_model(self, configure_request):
        """
        Configures a model with new settings.
        
        Args:
            configure_request (dict): The configuration request containing model ID and configuration data.
        
        Returns:
            dict: The updated configuration.
        
        Raises:
            KeyError: If the model is not found in the library.
        """
        try:
            model_id = configure_request['model_id']
            config_data = configure_request['data']
            
            updated_config = self.library_control.update_model_config(model_id, config_data)
            
            if updated_config:
                if self.is_model_loaded(model_id):
                    self.unload_model(model_id)
                    self.load_model(model_id)
                    
                return {"message": f"Model {model_id} configuration updated in library"}
            else:
                return {"error": f"Failed to update configuration for model {model_id}"}
            
        except KeyError:
            return {"error": f"Model {configure_request['model_id']} not found in library"}
    
    def get_active_model(self, model_id: str):
        """
        Retrieves an active model by its ID.
        
        Args:
            model_id (str): The ID of the model to retrieve.
        
        Returns:
            dict: The active model's information.
        
        Raises:
            KeyError: If the model is not found in active models.
        """
        if model_id in self.models:
            return self.models[model_id]
        logger.error(f"Model {model_id} not found in active models.")
        raise KeyError(f"Model {model_id} not found in active models. Please load it in memory first.")
    
    def _get_model_info(self, model_id: str, source: str = "library"):
        """
        Retrieves model information from the specified source.
        
        Args:
            model_id (str): The ID of the model.
            source (str): The source to retrieve model information from ("library" or "index").
        
        Returns:
            dict: The model information.
        
        Raises:
            ValueError: If the model information is not found or the source is invalid.
        """
        if source == "library":
            model_info = self.library_control.get_model_info_library(model_id)
        elif source == "index":
            model_info = self.library_control.get_model_info_index(model_id)
        else:
            raise ValueError(f"Invalid source: {source}. Use 'library' or 'index'.")

        if not model_info:
            logger.error(f"Model info not found for {model_id} in {source}")
            raise ValueError(f"Model info not found for {model_id} in {source}")

        return model_info
    
    def _get_model_class(self, model_id: str, source: str):
        """
        Retrieves the model class from the specified source.
        
        Args:
            model_id (str): The ID of the model.
            source (str): The source to retrieve the model class from ("library" or "index").
        
        Returns:
            class: The model class.
        
        Raises:
            ValueError: If the model class is not specified or cannot be loaded.
        """
        model_info = self._get_model_info(model_id, source)
    
        model_class_name = model_info.get('model_class')
        if not model_class_name:
            raise ValueError(f"Model class not specified for {model_id}")
        try:
            module = importlib.import_module('backend.models')
            model_class = getattr(module, model_class_name)
            return model_class
        except (ImportError, AttributeError) as e:
            error_string = str(e)
            logger.error(f"Failed to load model class {model_class_name}: {error_string}")
            raise ValueError(f"Failed to load model class {model_class_name}: {error_string}")

    def get_model_hardware_usage(self, model_id: str):
        if model_id in self.models:
            pid = self.models[model_id]['pid']
            logger.debug(f"Getting hardware usage for model {model_id} with PID: {pid}")
            try:
                process = psutil.Process(pid)
                cpu_percent = process.cpu_percent(interval=1)
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                
                logger.debug(f"CPU usage: {cpu_percent}%, Memory usage: {memory_percent}%")
                
                gpu_usage = None
                gpu_percent = None
                gpu_utilization = None
                if torch.cuda.is_available():
                    logger.debug("CUDA is available, fetching GPU information")
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        gpu_usage = gpu.memoryUsed
                        gpu_total = gpu.memoryTotal
                        gpu_percent = (gpu_usage / gpu_total) * 100 if gpu_total > 0 else 0
                        
                        logger.debug(f"GPU memory usage: {gpu_usage}MB, GPU memory percent: {gpu_percent}%")
                        
                        try:
                            # Get overall GPU utilization
                            result = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], 
                                                    capture_output=True, text=True, check=True)
                            overall_gpu_utilization = int(result.stdout.strip())
                            logger.debug(f"Overall GPU utilization: {overall_gpu_utilization}%")
                            
                            # Get list of processes using GPU
                            result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader,nounits'], 
                                                    capture_output=True, text=True, check=True)
                            gpu_pids = [int(line.strip()) for line in result.stdout.split('\n') if line.strip()]
                            logger.debug(f"PIDs using GPU: {gpu_pids}")
                            
                            if pid in gpu_pids:
                                # If our process is using the GPU, assume it's responsible for the utilization
                                gpu_utilization = overall_gpu_utilization
                                logger.debug(f"PID {pid} found in GPU processes. Assigned utilization: {gpu_utilization}%")
                            else:
                                logger.debug(f"PID {pid} not found in GPU processes")
                                gpu_utilization = 0
                        except subprocess.CalledProcessError as e:
                            logger.error(f"Error running nvidia-smi: {str(e)}")
                            logger.error(f"nvidia-smi stderr output: {e.stderr}")
                            logger.error(f"nvidia-smi return code: {e.returncode}")
                            gpu_utilization = None
                        except FileNotFoundError:
                            logger.error("nvidia-smi command not found. Make sure NVIDIA drivers are installed and nvidia-smi is in the system PATH.")
                            gpu_utilization = None
                        except Exception as e:
                            logger.error(f"Unexpected error when running nvidia-smi: {str(e)}")
                            gpu_utilization = None
                    else:
                        logger.debug("No GPUs found by GPUtil")
                else:
                    logger.debug("CUDA is not available")
                
                result = {
                    'cpu_percent': round(cpu_percent, 2),
                    'memory_used_mb': round(memory_info.rss / (1024 * 1024), 2),  # Convert to MB
                    'memory_percent': round(memory_percent, 2),
                    'gpu_memory_used_mb': round(gpu_usage, 2) if gpu_usage is not None else None,
                    'gpu_memory_percent': round(gpu_percent, 2) if gpu_percent is not None else None,
                    'gpu_utilization_percent': round(gpu_utilization, 2) if gpu_utilization is not None else None
                }
                
                logger.debug(f"Hardware usage result: {result}")
                return result
            except psutil.NoSuchProcess:
                logger.error(f"No process found with PID: {pid}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in get_model_hardware_usage: {str(e)}")
                return None
        else:
            logger.error(f"Model {model_id} not found in active models.")
            return None
