import os
import shutil
import numpy as np
from datasets import load_dataset
from transformers import DataCollatorWithPadding, Trainer, TrainingArguments
import evaluate
from backend.core.config import ROOT_DIR
from backend.utils.helpers import get_next_suffix
from backend.models.transformer_model import TransformerModel
import sys
import json
import torch

def train_transformer(transformer_model, dataset_path, tokenizer_args, training_args, trained_model_dir):
    dataset = load_dataset('csv', data_files=dataset_path)
    dataset = dataset["train"]

    model = transformer_model.pipeline_args.get("model")
    tokenizer = transformer_model.pipeline_args.get("tokenizer")
    
    def _preprocess_function(data_entry):
        tokenizer_params = {
            "padding": "max_length",
            "truncation": True,
            "max_length": 128
        }
        tokenizer_params.update(tokenizer_args)
        return tokenizer(data_entry['text'], **tokenizer_params)

    dataset = dataset.map(_preprocess_function)
    dataset = dataset.train_test_split(test_size=0.2)

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    accuracy = evaluate.load("accuracy")

    def compute_metrics(eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        return accuracy.compute(predictions=predictions, references=labels)

    suffix = get_next_suffix(model_id)
    trained_model_dir = os.path.join(f"{transformer_model.model_dir}_{suffix}")
    temp_output_dir = os.path.join(ROOT_DIR, "temp")

    os.makedirs(temp_output_dir, exist_ok=True)

    default_training_args = {
        "output_dir": temp_output_dir,
        "save_only_model": True,
        "learning_rate": 1e-7,
        "num_train_epochs": 5,
        "weight_decay": 0.01,
        "eval_strategy": "epoch",
        "save_strategy": "epoch",
        "save_total_limit": 3,
        "load_best_model_at_end": True
    }

    default_training_args.update(training_args)
    training_args = TrainingArguments(**default_training_args)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model(trained_model_dir)

    shutil.rmtree(temp_output_dir, ignore_errors=True)

if __name__ == "__main__":

    
    with open("data/temp_train_args.json", 'r') as f:
        args = json.load(f)
    
    model_id = args.pop('model_id')
    hardware_preference = args.pop('hardware_preference')
    model_info = args.pop('model_info')
    
    device = torch.device("cuda" if hardware_preference == "gpu" and torch.cuda.is_available() else "cpu")
    
    transformer_model = TransformerModel(model_id=model_id)
    transformer_model.load(device=device, model_info=model_info)
    
    train_transformer(transformer_model, **args)
    print("=====training complete=====")

    # Delete the temp_train_args.json file
    os.remove("data/temp_train_args.json")
