import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Scale, IntVar
from threading import Thread
from transformers import pipeline, AutoTokenizer, TextIteratorStreamer, StoppingCriteria, StoppingCriteriaList
import torch

class StoppingCriteriaSub(StoppingCriteria):
    def __init__(self, stops = [], encounters=1):
        super().__init__()
        self.stops = [stop.to("cuda") if torch.cuda.is_available() else stop for stop in stops]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            if torch.all((stop == input_ids[0][-len(stop):])).item():
                return True
        return False

class LlamaGUI:
    def __init__(self, master):
        self.master = master
        master.title("Language Model Interaction")
        master.geometry("800x600")

        self.pipeline = None
        self.tokenizer = None
        self.chat_history = []
        self.raw_output = []

        self.model_var = tk.StringVar(value="meta-llama/Meta-Llama-3-8B-Instruct")
        self.system_prompt = self.get_system_prompt()

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both')

        # Create main chat tab
        self.chat_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_tab, text='Chat')

        # Create raw output tab
        self.raw_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.raw_tab, text='Raw Output')

        # Main chat tab contents
        self.prompt_label = tk.Label(self.chat_tab, text="Enter your message:")
        self.prompt_label.pack(pady=5)

        self.user_input = scrolledtext.ScrolledText(self.chat_tab, height=3)
        self.user_input.pack(pady=5, padx=10, fill=tk.X)

        self.max_length_var = IntVar(value=200)
        self.max_length_label = tk.Label(self.chat_tab, text="Max output length:")
        self.max_length_label.pack(pady=5)
        self.max_length_scale = Scale(self.chat_tab, from_=50, to=1000, orient=tk.HORIZONTAL, 
                                      variable=self.max_length_var, length=200)
        self.max_length_scale.pack(pady=5)

        self.submit_button = tk.Button(self.chat_tab, text="Submit", command=self.on_submit)
        self.submit_button.pack(pady=5)

        self.chat_display = scrolledtext.ScrolledText(self.chat_tab, height=20, state='disabled')
        self.chat_display.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        self.chat_display.tag_configure("user", foreground="blue")
        self.chat_display.tag_configure("assistant", foreground="green")

        # Raw output tab contents
        self.raw_display = scrolledtext.ScrolledText(self.raw_tab, height=30, state='disabled')
        self.raw_display.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # Common elements
        self.model_label = tk.Label(master, text="Select Model:")
        self.model_label.pack(pady=5)
        self.model_menu = tk.OptionMenu(master, self.model_var, 
                                        "meta-llama/Meta-Llama-3-8B-Instruct", 
                                        "nomic-ai/gpt4all-j",
                                        command=self.update_system_prompt)
        self.model_menu.pack(pady=5)

        self.use_history_var = tk.BooleanVar(value=True)
        self.use_history_check = tk.Checkbutton(master, text="Use Chat History", 
                                                variable=self.use_history_var)
        self.use_history_check.pack(pady=5)

        self.load_model_button = tk.Button(master, text="Load Model", command=self.load_model_thread)
        self.load_model_button.pack(pady=5)

        self.status_label = tk.Label(master, text="Model not loaded")
        self.status_label.pack(pady=5)

    def get_system_prompt(self):
        if self.model_var.get() == "meta-llama/Meta-Llama-3-8B-Instruct":
            return "You are a helpful AI assistant. Respond to the user's messages in a friendly and informative manner. Do not pretend to be the user or continue the conversation as both parties. Your responses should be direct and relevant to the user's most recent message. Do not use emojis."
        elif self.model_var.get() == "nomic-ai/gpt4all-j":
            return "You are GPT4All-J, an AI assistant trained by Nomic AI. Provide helpful, ethical, and honest responses. Focus on the user's most recent message and avoid continuing the conversation as both parties. Be concise and informative in your replies."
        else:
            return "You are a helpful AI assistant. Respond to the user's messages in a friendly and informative manner."

    def update_system_prompt(self, *args):
        self.system_prompt = self.get_system_prompt()

    def load_model_thread(self):
        Thread(target=self.load_model).start()

    def load_model(self):
        try:
            self.status_label.config(text="Loading model...")
            self.master.update()

            model_id = self.model_var.get()
            model_dir = os.path.join('data', 'downloads', 'transformers', model_id)

            if not os.path.exists(model_dir):
                raise FileNotFoundError(f"Model directory not found: {model_dir}")

            self.pipeline = pipeline(
                "text-generation",
                model=model_id,
                tokenizer=model_id,
                device_map="auto",
                model_kwargs={"cache_dir": model_dir, "local_files_only": True},
                torch_dtype="auto"
            )

            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=model_dir,
                local_files_only=True
            )

            self.status_label.config(text="Model loaded successfully")
            self.load_model_button.config(state=tk.DISABLED)
        except Exception as e:
            self.status_label.config(text="Error loading model")
            messagebox.showerror("Error", f"Failed to load model: {str(e)}")

    def on_submit(self):
        if not self.pipeline:
            messagebox.showwarning("Warning", "Please load the model first.")
            return

        user_message = self.user_input.get("1.0", tk.END).strip()
        if not user_message:
            messagebox.showwarning("Warning", "Please enter a message.")
            return

        if self.use_history_var.get():
            self.chat_history.append(f"User: {user_message}")
            self.update_chat_display()
        else:
            self.update_chat_display(f"User: {user_message}")
        self.raw_output.append(f"User: {user_message}")
        self.update_raw_display(f"User: {user_message}\n")
        self.user_input.delete("1.0", tk.END)

        Thread(target=self.generate_response, args=(user_message,)).start()

    def generate_response(self, user_message):
        try:
            max_length = self.max_length_var.get()
            
            if self.use_history_var.get():
                full_prompt = f"{self.system_prompt}\n\n"
                for message in self.chat_history[-5:]:
                    full_prompt += message + "\n"
                full_prompt += f"Assistant: "
            else:
                full_prompt = f"{self.system_prompt}\n\nUser: {user_message}\nAssistant: "

            stop_words = ["User:", "Human:", "Assistant:"]
            stop_ids = [self.tokenizer(stop_word, return_tensors='pt')['input_ids'].squeeze() for stop_word in stop_words]
            stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_ids)])

            streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
            
            generation_kwargs = dict(
                max_new_tokens=max_length,
                do_sample=True,
                top_p=0.95,
                top_k=50,
                repetition_penalty=1.2,
                stopping_criteria=stopping_criteria,
                streamer=streamer,
            )

            thread = Thread(target=self.pipeline, kwargs=dict(text_inputs=full_prompt, **generation_kwargs))
            thread.start()

            generated_response = ""
            for new_text in streamer:
                generated_response += new_text
                cleaned_response = self.clean_response(generated_response)
                if self.use_history_var.get():
                    self.chat_history[-1] = f"Assistant: {cleaned_response}"
                    self.update_chat_display()
                else:
                    self.update_chat_display(cleaned_response)
                self.update_raw_display(generated_response)

            final_response = self.clean_response(generated_response)
            if self.use_history_var.get():
                self.chat_history[-1] = f"Assistant: {final_response}"
            self.update_chat_display(final_response)
            self.raw_output.append(f"Assistant: {generated_response}")
            self.update_raw_display(generated_response)

        except Exception as e:
            error_message = f"Error: {str(e)}"
            if self.use_history_var.get():
                self.chat_history.append(error_message)
            self.update_chat_display(error_message)
            self.raw_output.append(error_message)
            self.update_raw_display(error_message)

    def clean_response(self, response):
        # Remove any text after "User:", "Human:", or "Assistant:"
        stop_words = ["User:", "Human:", "Assistant:"]
        for word in stop_words:
            response = response.split(word)[0]
        
        # Remove any incomplete sentences at the end
        sentences = response.split('.')
        if len(sentences) > 1:
            response = '.'.join(sentences[:-1]) + '.'
        
        return response.strip()

    def update_chat_display(self, single_response=None):
        self.chat_display.config(state='normal')
        self.chat_display.delete("1.0", tk.END)
        if self.use_history_var.get():
            for message in self.chat_history:
                if message.startswith("User:"):
                    self.chat_display.insert(tk.END, message + "\n\n", "user")
                elif message.startswith("Assistant:"):
                    self.chat_display.insert(tk.END, message + "\n\n", "assistant")
                else:
                    self.chat_display.insert(tk.END, message + "\n\n")
        else:
            if single_response:
                self.chat_display.insert(tk.END, single_response + "\n\n", "assistant")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def update_raw_display(self, new_text):
        self.raw_display.config(state='normal')
        self.raw_display.insert(tk.END, new_text + "\n\n")
        self.raw_display.config(state='disabled')
        self.raw_display.see(tk.END)

def main():
    root = tk.Tk()
    gui = LlamaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()