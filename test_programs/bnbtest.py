import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
from accelerate import Accelerator
import os
import tkinter as tk
from tkinter import scrolledtext, ttk
import gc
from backend.core.exceptions import FileReadError, FileWriteError
from backend.data_utils.json_handler import JSONHandler

class SettingsWindow:
    def __init__(self, master, chat_interface):
        self.window = tk.Toplevel(master)
        self.window.title("Settings")
        self.chat_interface = chat_interface

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Quantization frame
        quant_frame = ttk.Frame(notebook)
        notebook.add(quant_frame, text="Quantization")
        self.quant_mode = tk.StringVar(value=chat_interface.settings["quantization_config"].get("current_mode", "4-bit"))
        ttk.Label(quant_frame, text="Quantization mode:").pack(anchor=tk.W)
        ttk.Radiobutton(quant_frame, text="4-bit", variable=self.quant_mode, value="4-bit").pack(anchor=tk.W)
        ttk.Radiobutton(quant_frame, text="8-bit", variable=self.quant_mode, value="8-bit").pack(anchor=tk.W)

        # Pipeline Parameters
        pipeline_frame = ttk.Frame(notebook)
        notebook.add(pipeline_frame, text="Pipeline")
        self.max_length = tk.IntVar(value=chat_interface.settings["pipeline_config"]["max_length"])
        self.max_new_tokens = tk.IntVar(value=chat_interface.settings["pipeline_config"]["max_new_tokens"])
        self.num_beams = tk.IntVar(value=chat_interface.settings["pipeline_config"]["num_beams"])
        self.use_cache = tk.BooleanVar(value=chat_interface.settings["pipeline_config"]["use_cache"])

        ttk.Label(pipeline_frame, text="Max length:").pack(anchor=tk.W)
        ttk.Entry(pipeline_frame, textvariable=self.max_length).pack(fill=tk.X)
        ttk.Label(pipeline_frame, text="Max new tokens:").pack(anchor=tk.W)
        ttk.Entry(pipeline_frame, textvariable=self.max_new_tokens).pack(fill=tk.X)
        ttk.Label(pipeline_frame, text="Num beams:").pack(anchor=tk.W)
        ttk.Entry(pipeline_frame, textvariable=self.num_beams).pack(fill=tk.X)
        ttk.Checkbutton(pipeline_frame, text="Use cache", variable=self.use_cache).pack(anchor=tk.W)

        # Model Parameters
        model_frame = ttk.Frame(notebook)
        notebook.add(model_frame, text="Model")
        self.model_name = tk.StringVar(value=chat_interface.settings["model"]["name"])
        self.cache_dir = tk.StringVar(value=chat_interface.settings["model"]["cache_dir"])

        ttk.Label(model_frame, text="Model name:").pack(anchor=tk.W)
        ttk.Entry(model_frame, textvariable=self.model_name).pack(fill=tk.X)
        ttk.Label(model_frame, text="Cache directory:").pack(anchor=tk.W)
        ttk.Entry(model_frame, textvariable=self.cache_dir).pack(fill=tk.X)

        # Tokenizer Parameters
        tokenizer_frame = ttk.Frame(notebook)
        notebook.add(tokenizer_frame, text="Tokenizer")
        # Add tokenizer-specific parameters here if needed

        # System Prompt
        system_frame = ttk.Frame(notebook)
        notebook.add(system_frame, text="System Prompt")
        self.system_prompt = tk.StringVar(value=chat_interface.settings["system_prompt"])
        ttk.Label(system_frame, text="System prompt:").pack(anchor=tk.W)
        ttk.Entry(system_frame, textvariable=self.system_prompt).pack(fill=tk.X)

        # Save Button
        ttk.Button(self.window, text="Save", command=self.save_settings).pack(pady=10)

    def save_settings(self):
        self.chat_interface.update_settings(self)
        self.window.destroy()

class ChatInterface:
    def __init__(self, master):
        self.master = master
        master.title("Llama Chatbot")

        self.chat_history = scrolledtext.ScrolledText(master, state='disabled', height=20, width=60)
        self.chat_history.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

        self.user_input = tk.Entry(master, width=50)
        self.user_input.grid(row=1, column=0, padx=10, pady=10)

        self.send_button = tk.Button(master, text="Send", command=self.send_message, state=tk.DISABLED)
        self.send_button.grid(row=1, column=1, padx=10, pady=10)

        self.load_button = tk.Button(master, text="Load Model", command=self.load_model)
        self.load_button.grid(row=2, column=0, padx=10, pady=10)

        self.unload_button = tk.Button(master, text="Unload Model", command=self.unload_model, state=tk.DISABLED)
        self.unload_button.grid(row=2, column=1, padx=10, pady=10)

        self.settings_button = tk.Button(master, text="Settings", command=self.open_settings)
        self.settings_button.grid(row=2, column=2, padx=10, pady=10)

        self.json_handler = JSONHandler()
        self.config_file = "test_programs/bnbtest_library.json"
        self.load_settings_from_json()

        self.model = None
        self.tokenizer = None
        self.text_generation_pipeline = None
        self.accelerator = None

    def load_settings_from_json(self):
        try:
            config = self.json_handler.read_json(self.config_file)
            model_config = config["meta-llama/Meta-Llama-3.1-8B-Instruct"]["config"]
            
            self.settings = {
                "model_config": model_config["model_config"],
                "tokenizer_config": model_config["tokenizer_config"],
                "processor_config": model_config["processor_config"],
                "pipeline_config": model_config["pipeline_config"],
                "device_config": model_config["device_config"],
                "quantization_config": model_config["quantization_config"],
                "quantization_config_options": model_config["quantization_config_options"],
                "auth_token": model_config["auth_token"],
                "system_prompt": model_config["system_prompt"],
                "model": {
                    "name": config["meta-llama/Meta-Llama-3.1-8B-Instruct"]["base_model"],
                    "cache_dir": config["meta-llama/Meta-Llama-3.1-8B-Instruct"]["dir"]
                }
            }
            
            self.messages = [
                {"role": "system", "content": self.settings["system_prompt"]}
            ]
            
        except FileReadError as e:
            print(f"Error loading settings: {e}")
            self.update_chat_history("Error loading settings. Please check the configuration file.\n")

    def save_settings_to_json(self):
        try:
            config = self.json_handler.read_json(self.config_file)
            model_config = config["meta-llama/Meta-Llama-3.1-8B-Instruct"]["config"]
            
            model_config.update(self.settings)
            model_config.pop("model", None)  # Remove the 'model' key from the config
            
            config["meta-llama/Meta-Llama-3.1-8B-Instruct"]["base_model"] = self.settings["model"]["name"]
            config["meta-llama/Meta-Llama-3.1-8B-Instruct"]["dir"] = self.settings["model"]["cache_dir"]
            
            self.json_handler.write_json(self.config_file, config)
        except (FileReadError, FileWriteError) as e:
            print(f"Error saving settings: {e}")
            self.update_chat_history("Error saving settings. Changes may not persist.\n")

    def set_quantization_mode(self, mode):
        self.settings["quantization_config"]["current_mode"] = mode
        self.save_settings_to_json()
        self.update_chat_history(f"Quantization mode set to {mode} and saved. Please reload the model for changes to take effect.\n")

    def load_model(self):
        USE_CPU = self.settings["device_config"]["device"] == "cpu"
        self.accelerator = Accelerator(cpu=USE_CPU)

        if not os.path.exists(self.settings["model"]["cache_dir"]):
            self.update_chat_history("Error: Cache directory not found.\n")
            return

        current_mode = self.settings["quantization_config"].get("current_mode", "4-bit")
        bnb_config = BitsAndBytesConfig(**self.settings["quantization_config"])

        self.model = AutoModelForCausalLM.from_pretrained(
            self.settings["model"]["name"],
            cache_dir=self.settings["model"]["cache_dir"],
            local_files_only=True,
            quantization_config=bnb_config,
            **self.settings["model_config"]
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.settings["model"]["name"],
            cache_dir=self.settings["model"]["cache_dir"],
            local_files_only=True,
            **self.settings["tokenizer_config"]
        )

        self.model = self.accelerator.prepare(self.model)

        self.text_generation_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            **self.settings["pipeline_config"]
        )

        self.send_button.config(state=tk.NORMAL)
        self.load_button.config(state=tk.DISABLED)
        self.unload_button.config(state=tk.NORMAL)
        self.update_chat_history("Model loaded successfully.\n")

    def unload_model(self):
        if self.text_generation_pipeline:
            del self.text_generation_pipeline
        if self.model:
            self.model.cpu()
            del self.model
        if self.tokenizer:
            del self.tokenizer
        if self.accelerator:
            del self.accelerator

        self.text_generation_pipeline = None
        self.model = None
        self.tokenizer = None
        self.accelerator = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        gc.collect()

        self.send_button.config(state=tk.DISABLED)
        self.load_button.config(state=tk.NORMAL)
        self.unload_button.config(state=tk.DISABLED)
        self.update_chat_history("Model unloaded.\n")

        # Print current GPU memory usage
        if torch.cuda.is_available():
            print(f"Current GPU memory allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
            print(f"Current GPU memory reserved: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")

    def send_message(self):
        user_message = self.user_input.get()
        self.user_input.delete(0, tk.END)

        self.messages.append({"role": "user", "content": user_message})
        self.update_chat_history(f"You: {user_message}\n")

        if self.text_generation_pipeline is None:
            self.update_chat_history("Error: Model not loaded.\n")
            return

        # Use the settings from pipeline_config
        max_new_tokens = self.settings["pipeline_config"]["max_new_tokens"]
        
        result = self.text_generation_pipeline(
            self.messages
        )

        print("Raw model output:", result)  # Print raw output for debugging

        ai_message = result[0]["generated_text"][-1].get("content")
        self.messages.append({"role": "assistant", "content": ai_message})
        self.update_chat_history(f"AI: {ai_message}\n\n")

    def update_chat_history(self, message):
        self.chat_history.configure(state='normal')
        self.chat_history.insert(tk.END, message)
        self.chat_history.configure(state='disabled')
        self.chat_history.see(tk.END)

    def open_settings(self):
        SettingsWindow(self.master, self)

    def update_settings(self, settings_window):
        # Update quantization settings
        quant_mode = settings_window.quant_mode.get()
        self.settings["quantization_config"] = self.settings["quantization_config_options"][quant_mode].copy()
        self.settings["quantization_config"]["current_mode"] = quant_mode

        # Update pipeline settings
        self.settings["pipeline_config"]["max_length"] = settings_window.max_length.get()
        self.settings["pipeline_config"]["max_new_tokens"] = settings_window.max_new_tokens.get()
        self.settings["pipeline_config"]["num_beams"] = settings_window.num_beams.get()
        self.settings["pipeline_config"]["use_cache"] = settings_window.use_cache.get()

        self.settings["model"]["name"] = settings_window.model_name.get()
        self.settings["model"]["cache_dir"] = settings_window.cache_dir.get()
        self.settings["system_prompt"] = settings_window.system_prompt.get()

        self.save_settings_to_json()
        self.update_chat_history("Settings updated and saved. Please reload the model for changes to take effect.\n")

# Create and run the Tkinter application
root = tk.Tk()
chat_interface = ChatInterface(root)
root.mainloop()

# Print the device being used (this will only be seen in the console)
print(f"Using device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")