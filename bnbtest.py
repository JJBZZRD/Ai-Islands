import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
from accelerate import Accelerator
import os
import tkinter as tk
from tkinter import scrolledtext, ttk
import gc

class SettingsWindow:
    def __init__(self, master, chat_interface):
        self.window = tk.Toplevel(master)
        self.window.title("Settings")
        self.chat_interface = chat_interface

        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # BNB Config
        bnb_frame = ttk.Frame(notebook)
        notebook.add(bnb_frame, text="BNB Config")
        self.load_in_4bit = tk.BooleanVar(value=True)
        self.bnb_4bit_use_double_quant = tk.BooleanVar(value=True)
        self.bnb_4bit_quant_type = tk.StringVar(value="nf4")
        self.bnb_4bit_compute_dtype = tk.StringVar(value="bfloat16")

        ttk.Checkbutton(bnb_frame, text="Load in 4-bit", variable=self.load_in_4bit).pack(anchor=tk.W)
        ttk.Checkbutton(bnb_frame, text="Use double quant", variable=self.bnb_4bit_use_double_quant).pack(anchor=tk.W)
        ttk.Label(bnb_frame, text="Quant type:").pack(anchor=tk.W)
        ttk.Entry(bnb_frame, textvariable=self.bnb_4bit_quant_type).pack(fill=tk.X)
        ttk.Label(bnb_frame, text="Compute dtype:").pack(anchor=tk.W)
        ttk.Entry(bnb_frame, textvariable=self.bnb_4bit_compute_dtype).pack(fill=tk.X)

        # Pipeline Parameters
        pipeline_frame = ttk.Frame(notebook)
        notebook.add(pipeline_frame, text="Pipeline")
        self.max_new_tokens = tk.IntVar(value=100)
        self.num_return_sequences = tk.IntVar(value=1)

        ttk.Label(pipeline_frame, text="Max new tokens:").pack(anchor=tk.W)
        ttk.Entry(pipeline_frame, textvariable=self.max_new_tokens).pack(fill=tk.X)
        ttk.Label(pipeline_frame, text="Num return sequences:").pack(anchor=tk.W)
        ttk.Entry(pipeline_frame, textvariable=self.num_return_sequences).pack(fill=tk.X)

        # Model Parameters
        model_frame = ttk.Frame(notebook)
        notebook.add(model_frame, text="Model")
        self.model_name = tk.StringVar(value="meta-llama/Meta-Llama-3.1-8B-Instruct")
        self.cache_dir = tk.StringVar(value="data/downloads/transformers/meta-llama/Meta-Llama-3.1-8B-Instruct")

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
        self.system_prompt = tk.StringVar(value="You are a helpful AI assistant.")
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

        self.messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]

        self.model = None
        self.tokenizer = None
        self.text_generation_pipeline = None
        self.accelerator = None

        # Default settings
        self.settings = {
            "bnb_config": {
                "load_in_4bit": True,
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_compute_dtype": torch.bfloat16
            },
            "pipeline": {
                "max_new_tokens": 100,
                "num_return_sequences": 1
            },
            "model": {
                "name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "cache_dir": "data/downloads/transformers/meta-llama/Meta-Llama-3.1-8B-Instruct"
            },
            "system_prompt": "You are a helpful AI assistant."
        }

    def open_settings(self):
        SettingsWindow(self.master, self)

    def update_settings(self, settings_window):
        self.settings["bnb_config"]["load_in_4bit"] = settings_window.load_in_4bit.get()
        self.settings["bnb_config"]["bnb_4bit_use_double_quant"] = settings_window.bnb_4bit_use_double_quant.get()
        self.settings["bnb_config"]["bnb_4bit_quant_type"] = settings_window.bnb_4bit_quant_type.get()
        self.settings["bnb_config"]["bnb_4bit_compute_dtype"] = getattr(torch, settings_window.bnb_4bit_compute_dtype.get())
        self.settings["pipeline"]["max_new_tokens"] = settings_window.max_new_tokens.get()
        self.settings["pipeline"]["num_return_sequences"] = settings_window.num_return_sequences.get()
        self.settings["model"]["name"] = settings_window.model_name.get()
        self.settings["model"]["cache_dir"] = settings_window.cache_dir.get()
        self.settings["system_prompt"] = settings_window.system_prompt.get()

        self.messages[0] = {"role": "system", "content": self.settings["system_prompt"]}
        self.update_chat_history("Settings updated. Please reload the model for changes to take effect.\n")

    def load_model(self):
        USE_CPU = False
        self.accelerator = Accelerator(cpu=USE_CPU)

        if not os.path.exists(self.settings["model"]["cache_dir"]):
            self.update_chat_history("Error: Cache directory not found.\n")
            return

        bnb_config = BitsAndBytesConfig(**self.settings["bnb_config"])

        self.model = AutoModelForCausalLM.from_pretrained(
            self.settings["model"]["name"],
            cache_dir=self.settings["model"]["cache_dir"],
            local_files_only=True,
            quantization_config=bnb_config,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.settings["model"]["name"],
            cache_dir=self.settings["model"]["cache_dir"],
            local_files_only=True
        )

        self.model = self.accelerator.prepare(self.model)

        self.text_generation_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer
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

        result = self.text_generation_pipeline(
            self.messages,
            max_new_tokens=100,
            num_return_sequences=1
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

# Create and run the Tkinter application
root = tk.Tk()
chat_interface = ChatInterface(root)
root.mainloop()

# Print the device being used (this will only be seen in the console)
print(f"Using device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")