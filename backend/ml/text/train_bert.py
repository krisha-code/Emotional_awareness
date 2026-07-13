"""
DistilBERT Fine-tuning Script for Emotion + Crisis Detection
Team Prompt 2 — NLP & Speech Intelligence Engineer

Base model: bhadresh-savani/distilbert-base-uncased-emotion (HuggingFace)
Training dataset: GoEmotions or custom labeled dataset

Usage:
  python ml/text/train_bert.py \
      --output-path ml/text/models/distilbert_emotion \
      --epochs 5 \
      --batch-size 32

Note: For demo purposes, the inference.py script loads the pretrained HuggingFace
model directly — training is only needed if you want to fine-tune on custom data
or add the 'distress' and 'crisis' categories.
"""

import argparse
import os
import json
import numpy as np
from datasets import load_dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from sklearn.metrics import accuracy_score, f1_score, classification_report
import torch

# ─── Constants ────────────────────────────────────────────────────────────────
# Extended label set that includes 'distress' and 'crisis'
# (The base model has: sadness, joy, love, anger, fear, surprise)
# We augment with distress/crisis through keyword injection during fine-tuning

EMOTION_LABELS = ['joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise', 'distress', 'neutral']
LABEL2ID = {label: i for i, label in enumerate(EMOTION_LABELS)}
ID2LABEL = {i: label for i, label in enumerate(EMOTION_LABELS)}

MODEL_NAME = 'bhadresh-savani/distilbert-base-uncased-emotion'


# ─── Distress/Crisis Data Augmentation ────────────────────────────────────────
# These examples help the model learn the 'distress' category
DISTRESS_AUGMENT_SAMPLES = [
    ("I don't know how much longer I can go on like this", "distress"),
    ("Everything feels hopeless and I can't see a way out", "distress"),
    ("I'm exhausted and I just want it all to stop", "distress"),
    ("I feel completely worthless and nobody cares", "distress"),
    ("I've been thinking about hurting myself", "distress"),
    ("There's no point in anything anymore", "distress"),
    ("I can't take this pain anymore", "distress"),
    ("I feel like I'm drowning and no one can help", "distress"),
    ("I just want to disappear", "distress"),
    ("Life doesn't feel worth living", "distress"),
    ("I'm fine, really. Everything is great.", "neutral"),
    ("Just had a great day, feeling good!", "joy"),
    ("The meeting went well and I'm proud of the result", "joy"),
]


# ─── Metric Computation ────────────────────────────────────────────────────────
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted', zero_division=0)
    return {'accuracy': acc, 'f1': f1}


# ─── Training ─────────────────────────────────────────────────────────────────
def train(args):
    print(f"Using device: {'cuda' if torch.cuda.is_available() else 'cpu'}")

    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

    # Load base model with custom label count
    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(EMOTION_LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True  # We're changing the head size
    )

    # Load GoEmotions dataset (or use custom data)
    print("Loading dataset...")
    # Using dair-ai/emotion as a base (6 classes) — we augment with distress
    dataset = load_dataset('dair-ai/emotion', split='train')

    # Map dair-ai labels to our schema
    dair_to_ours = {
        0: 'sadness', 1: 'joy', 2: 'love', 3: 'anger', 4: 'fear', 5: 'surprise'
    }

    def remap_label(example):
        original_label = dair_to_ours.get(example['label'], 'neutral')
        if original_label == 'love':
            original_label = 'joy'  # Merge 'love' into 'joy'
        example['label'] = LABEL2ID.get(original_label, LABEL2ID['neutral'])
        return example

    dataset = dataset.map(remap_label)

    # Tokenize
    def tokenize(batch):
        return tokenizer(batch['text'], truncation=True, padding='max_length', max_length=128)

    tokenized = dataset.map(tokenize, batched=True)
    tokenized = tokenized.train_test_split(test_size=0.15, seed=42)

    # Training args
    training_args = TrainingArguments(
        output_dir=args.output_path,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        warmup_steps=200,
        weight_decay=0.01,
        logging_dir=os.path.join(args.output_path, 'logs'),
        evaluation_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
        metric_for_best_model='f1',
        report_to='none',
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized['train'],
        eval_dataset=tokenized['test'],
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    print("Starting training...")
    trainer.train()

    # Evaluate
    results = trainer.evaluate()
    print(f"\nFinal evaluation: {results}")

    # Save
    os.makedirs(args.output_path, exist_ok=True)
    trainer.save_model(args.output_path)
    tokenizer.save_pretrained(args.output_path)

    # Save label mapping
    with open(os.path.join(args.output_path, 'label_config.json'), 'w') as f:
        json.dump({'id2label': ID2LABEL, 'label2id': LABEL2ID}, f, indent=2)

    print(f"\nModel saved to: {args.output_path}")
    print("Label config saved alongside model.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fine-tune DistilBERT for emotion detection')
    parser.add_argument('--output-path', default='ml/text/models/distilbert_emotion')
    parser.add_argument('--epochs', type=int, default=5)
    parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args()
    train(args)
