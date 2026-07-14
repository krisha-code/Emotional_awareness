"""
backend/ml/text/train_bert.py

Optional fine-tuning script. For the demo, `emotion_model.py` uses the
pretrained bhadresh-savani/distilbert-base-uncased-emotion checkpoint
directly with no training needed. Run this only if fine-tuning on a
custom/labeled dataset that better matches the shared 7-class taxonomy
(joy, sadness, anger, fear, disgust, surprise, neutral).

Usage:
    python ml/text/train_bert.py \
        --model distilbert-base-uncased \
        --dataset-path ml/text/data/custom_emotion.csv \
        --output-path ml/text/models/distilbert_emotion \
        --epochs 3 --batch-size 16

Expected CSV columns: `text`, `label` (label must be one of EMOTION_LABELS
in emotion_model.py).
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from emotion_model import EMOTION_LABELS  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune DistilBERT on the shared emotion taxonomy")
    parser.add_argument("--model", default="distilbert-base-uncased")
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--output-path", default="ml/text/models/distilbert_emotion")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        import pandas as pd
        import torch
        from datasets import Dataset
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        logger.error(
            "Missing training dependencies (%s). Install with: "
            "pip install torch transformers datasets pandas",
            exc,
        )
        sys.exit(1)

    label2id = {lbl: i for i, lbl in enumerate(EMOTION_LABELS)}
    id2label = {i: lbl for lbl, i in label2id.items()}

    df = pd.read_csv(args.dataset_path)
    unknown = set(df["label"].unique()) - set(label2id)
    if unknown:
        raise ValueError(
            f"Dataset contains labels outside the shared taxonomy: {unknown}. "
            f"Expected one of {EMOTION_LABELS}."
        )
    df["label_id"] = df["label"].map(label2id)

    dataset = Dataset.from_pandas(df[["text", "label_id"]])
    dataset = dataset.rename_column("label_id", "label")
    dataset = dataset.train_test_split(test_size=0.1, seed=42)

    tokenizer = AutoTokenizer.from_pretrained(args.model)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

    dataset = dataset.map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=len(EMOTION_LABELS),
        id2label=id2label,
        label2id=label2id,
    )

    training_args = TrainingArguments(
        output_dir=args.output_path,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.lr,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=20,
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.output_path)
    tokenizer.save_pretrained(args.output_path)
    logger.info("Saved fine-tuned model to %s", args.output_path)


if __name__ == "__main__":
    main()
