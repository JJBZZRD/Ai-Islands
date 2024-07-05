import importlib
import os
from transformers import AutoModelForCausalLM, AutoTokenizer

class TransformerModel:
    def __init__(self, class_names, model_name=None):
        self.classes = self._import_classes(class_names)
        self.model = None
        self.tokenizer = None
        self.model_path = None

    def _import_classes(self, class_names):
        imported_classes = {}
        for class_name in class_names:
            module_name, class_name = class_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            imported_classes[class_name] = getattr(module, class_name)
        return imported_classes

    def _initialize_model(self, model_name):
        if model_name not in self.classes:
            raise ValueError(f"Model name '{model_name}' not found in imported classes.")
        return self.classes[model_name]()

    def download(self, model_id: str):
        try:
            # Download the model and tokenizer
            self.model = AutoModelForCausalLM.from_pretrained(model_id)
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            
            # Save the model and tokenizer locally
            self.model_path = os.path.join('data', 'downloaded_models', model_id)
            self.model.save_pretrained(self.model_path)
            self.tokenizer.save_pretrained(self.model_path)
            
            print(f"Model {model_id} downloaded and saved to {self.model_path}")
        except Exception as e:
            print(f"Error downloading model {model_id}: {str(e)}")

    def load(self, model_id: str):
        try:
            self.model_path = os.path.join('data', 'downloaded_models', model_id)
            
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model directory not found: {self.model_path}")
            
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            print(f"Model {model_id} loaded from {self.model_path}")
        except Exception as e:
            print(f"Error loading model {model_id}: {str(e)}")

    def generate(self, prompt: str, max_length: int = 50):
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model or tokenizer not loaded. Please load a model first.")
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt")
            outputs = self.model.generate(**inputs, max_length=max_length)
            return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            print(f"Error during text generation: {str(e)}")
            return None