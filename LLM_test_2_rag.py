import tkinter as tk
from tkinter import scrolledtext, messagebox, Scale, IntVar, BooleanVar, filedialog
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList
import torch
import os
import re
from threading import Thread
from accelerate import Accelerator
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import csv
import pandas as pd
from pathlib import Path
import pickle

class StoppingCriteriaSub(StoppingCriteria):
    def __init__(self, stops = [], encounters=1):
        super().__init__()
        self.stops = [stop.to("cuda") if torch.cuda.is_available() else stop for stop in stops]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            if torch.all((stop == input_ids[0][-len(stop):])).item():
                return True
        return False

class LLMApp:
    def __init__(self, master):
        self.master = master
        master.title("LLM Interaction with RAG")
        master.geometry("800x600")

        self.model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
        self.model_dir = os.path.normpath(os.path.join('data', 'downloads', 'transformers', self.model_id))
        self.pipeline = None
        self.tokenizer = None
        self.chat_history = []
        self.use_history = BooleanVar(value=False)
        self.accelerator = Accelerator()

        # Update RAG components
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.current_dataset = None

        self.system_prompt = """You are an advanced AI assistant with a vast knowledge base spanning various fields including science, history, literature, technology, and current events. Your primary goal is to provide accurate, helpful, and concise responses to user queries. Follow these guidelines:

1. Provide direct and relevant answers to the user's questions.
2. If a question is ambiguous or lacks context, ask for clarification before answering.
3. Use clear and concise language, avoiding unnecessary jargon unless the context requires it.
4. If you're unsure about an answer, state your uncertainty and provide the best information you can, along with suggestions for further research.
5. For factual questions, cite reputable sources when possible.
6. For opinion-based questions, provide a balanced view of different perspectives.
7. Avoid making definitive statements about current events or rapidly changing fields without acknowledging the potential for outdated information.
8. Respect ethical boundaries: do not provide information on illegal activities, and promote safety and well-being.
9. Tailor your language to be appropriate for all ages, unless specifically asked otherwise.
10. Be prepared to break down complex topics into simpler explanations if requested.
11. Encourage critical thinking by suggesting related topics or follow-up questions when appropriate.
12. When provided with context, use it to inform your answers, but also draw upon your general knowledge when appropriate.

Remember, your role is to assist and inform, not to make decisions for the user. Always encourage users to seek professional advice for medical, legal, or other specialized fields when necessary."""

        self.create_widgets()

    def create_widgets(self):
        # Input area
        self.input_label = tk.Label(self.master, text="Enter your prompt:")
        self.input_label.pack(pady=5)
        self.input_text = scrolledtext.ScrolledText(self.master, height=5)
        self.input_text.pack(pady=5, padx=10, fill=tk.X)

        # Max output length slider
        self.max_length_var = IntVar(value=200)
        self.max_length_label = tk.Label(self.master, text="Max output length:")
        self.max_length_label.pack(pady=5)
        self.max_length_scale = Scale(self.master, from_=50, to=1000, orient=tk.HORIZONTAL, 
                                      variable=self.max_length_var, length=200)
        self.max_length_scale.pack(pady=5)

        # Submit button
        self.submit_button = tk.Button(self.master, text="Generate", command=self.generate_text)
        self.submit_button.pack(pady=5)

        # Output area
        self.output_label = tk.Label(self.master, text="Generated text:")
        self.output_label.pack(pady=5)
        self.output_text = scrolledtext.ScrolledText(self.master, height=15)
        self.output_text.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # Load model button
        self.load_button = tk.Button(self.master, text="Load Model", command=self.load_model_thread)
        self.load_button.pack(pady=5)

        # Status label
        self.status_label = tk.Label(self.master, text="Model not loaded")
        self.status_label.pack(pady=5)

        # Add a checkbox for using chat history
        self.history_checkbox = tk.Checkbutton(self.master, text="Use Chat History", variable=self.use_history)
        self.history_checkbox.pack(pady=5)

        # Add a clear history button
        self.clear_history_button = tk.Button(self.master, text="Clear History", command=self.clear_history)
        self.clear_history_button.pack(pady=5)

        # Add a button to load CSV file
        self.load_csv_button = tk.Button(self.master, text="Load CSV", command=self.load_csv_file)
        self.load_csv_button.pack(pady=5)

        # Add a dropdown to select dataset
        self.dataset_var = tk.StringVar(self.master)
        self.dataset_dropdown = tk.OptionMenu(self.master, self.dataset_var, "")
        self.dataset_dropdown.pack(pady=5)
        self.update_dataset_dropdown()

    def update_dataset_dropdown(self):
        datasets = self.list_datasets()
        menu = self.dataset_dropdown["menu"]
        menu.delete(0, "end")
        for dataset in datasets:
            menu.add_command(label=dataset, command=lambda value=dataset: self.dataset_var.set(value))
        if datasets:
            self.dataset_var.set(datasets[0])
        self.current_dataset = self.dataset_var.get()

    def load_csv_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                result = self.process_dataset(file_path)
                messagebox.showinfo("Result", result["message"])
                self.update_dataset_dropdown()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")

    def process_dataset(self, file_path: str):
        try:
            filename = Path(file_path).stem
            dataset_dir = Path("Datasets") / filename
            dataset_dir.mkdir(parents=True, exist_ok=True)

            df = pd.read_csv(file_path)
           
            texts = df.apply(lambda row: ' '.join([f"{col}: {val}" for col, val in row.items()]), axis=1).tolist()

            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            faiss.normalize_L2(embeddings)

            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)

            faiss_index_path = dataset_dir / f"{filename}_faiss_index.bin"
            faiss.write_index(index, str(faiss_index_path))

            pickle_path = dataset_dir / f"{filename}.pkl"
            df.to_pickle(pickle_path)

            csv_path = dataset_dir / f"{filename}.csv"
            df.to_csv(csv_path, index=False)

            return {"message": "Dataset processed successfully"}

        except Exception as e:
            print(f"Error: {e}")
            return {"message": "Error processing dataset"}

    def list_datasets(self):
        try:
            datasets_dir = Path("Datasets")
            datasets = [d.name for d in datasets_dir.iterdir() if d.is_dir()]
            return datasets
        except Exception as e:
            print(f"Error: {e}")
            return []

    def find_relevant_entries(self, query, dataset_name, top_k=10):
        dataset_dir = Path("Datasets") / dataset_name
        faiss_index_path = dataset_dir / f"{dataset_name}_faiss_index.bin"
        pickle_path = dataset_dir / f"{dataset_name}.pkl"

        if not faiss_index_path.exists() or not pickle_path.exists():
            return []

        index = faiss.read_index(str(faiss_index_path))
        original_data = pd.read_pickle(pickle_path)

        query_vector = self.embedding_model.encode([query])
        faiss.normalize_L2(query_vector)
        _, I = index.search(query_vector, top_k)
       
        relevant_entries = original_data.iloc[I[0]].to_dict('records')
        return [self.format_entry(entry) for entry in relevant_entries]

    def format_entry(self, entry):
        return ', '.join([f"{key}: {value}" for key, value in entry.items()])

    def clear_history(self):
        self.chat_history.clear()
        messagebox.showinfo("History Cleared", "Chat history has been cleared.")

    def load_model_thread(self):
        Thread(target=self.load_model).start()

    def load_model(self):
        try:
            self.status_label.config(text="Loading model...")
            self.master.update()

            if not os.path.exists(self.model_dir):
                raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                cache_dir=self.model_dir,
                local_files_only=True,
                trust_remote_code=True
            )

            self.pipeline = pipeline(
                "text-generation",
                model=self.model_id,
                tokenizer=self.tokenizer,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
                model_kwargs={"cache_dir": self.model_dir, "local_files_only": True}
            )

            self.pipeline = self.accelerator.prepare(self.pipeline)

            self.status_label.config(text="Model loaded successfully")
            self.load_button.config(state=tk.DISABLED)
        except Exception as e:
            self.status_label.config(text="Error loading model")
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")

    def generate_text(self):
        if not self.pipeline:
            messagebox.showwarning("Warning", "Please load the model first.")
            return

        prompt = self.input_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Warning", "Please enter a prompt.")
            return

        try:
            max_length = self.max_length_var.get()
            
            # Retrieve relevant documents
            relevant_docs = self.find_relevant_entries(prompt, self.current_dataset)
            context = "\n".join(relevant_docs)

            if self.use_history.get():
                full_prompt = self.build_prompt_with_history(prompt, context)
            else:
                full_prompt = f"{self.system_prompt}\n\nContext:\n{context}\n\nHuman: {prompt}\n\nAssistant: Let me answer your question based on the given context and my knowledge:\n"

            print("Full prompt:", full_prompt)  # Debug print

            stop_words = ["Human:", "Assistant:"]
            stop_ids = [self.tokenizer(stop_word, return_tensors='pt')['input_ids'].squeeze() for stop_word in stop_words]
            stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_ids)])

            outputs = self.pipeline(
                full_prompt,
                max_new_tokens=max_length,
                do_sample=True,
                temperature=0.6,
                top_p=0.9,
                stopping_criteria=stopping_criteria,
            )

            print("Type of outputs:", type(outputs))
            print("Contents of outputs:", outputs)

            if isinstance(outputs, list) and len(outputs) > 0:
                if isinstance(outputs[0], dict) and 'generated_text' in outputs[0]:
                    generated_text = outputs[0]['generated_text']
                else:
                    generated_text = str(outputs[0])
            else:
                generated_text = str(outputs)

            print("Generated text:", generated_text)

            assistant_response = generated_text.split("Assistant: Let me answer your question based on the given context and my knowledge:")[-1].split("Human:")[0].strip()
            cleaned_response = self.clean_response(assistant_response)

            if self.use_history.get():
                self.chat_history.append(f"Human: {prompt}")
                self.chat_history.append(f"Assistant: {cleaned_response}")
                self.update_output_with_history()
            else:
                self.update_output(f"Human: {prompt}\n\nAssistant: {cleaned_response}")

        except Exception as e:
            error_message = f"Error: {str(e)}\nType: {type(e)}\nArgs: {e.args}"
            messagebox.showerror("Error", f"Failed to generate text: {error_message}")
            print(f"Error details: {error_message}")

    def clean_response(self, text):
        # Split the text into code and non-code parts
        parts = re.split(r'(```[\s\S]*?```)', text)
        
        cleaned_parts = []
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                # This is a code block, preserve its formatting
                cleaned_parts.append(part)
            else:
                # This is not a code block, clean it up
                lines = part.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line:
                        cleaned_lines.append(line)
                cleaned_parts.append(' '.join(cleaned_lines))
        
        # Join the parts back together
        cleaned_text = '\n\n'.join(cleaned_parts)
        
        # Remove any text after "Human:" if present
        if "Human:" in cleaned_text:
            cleaned_text = cleaned_text.split("Human:")[0]
        
        return cleaned_text.strip()

    def build_prompt_with_history(self, new_prompt, context):
        history_prompt = "\n\n".join(self.chat_history[-10:])  # Use last 10 messages
        return f"{self.system_prompt}\n\nContext:\n{context}\n\n{history_prompt}\n\nHuman: {new_prompt}\n\nAssistant: Let me answer your question based on the given context and my knowledge:\n"

    def update_output_with_history(self):
        full_history = "\n\n".join(self.chat_history)
        self.update_output(full_history)

    def update_output(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(tk.END)

def main():
    root = tk.Tk()
    app = LLMApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()