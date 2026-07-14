"""
backend/ml/speech/train_speech.py

Trains SpeechEmotionCNNLSTM on RAVDESS (or any similarly-labeled dataset).

Usage (matches README):
    python ml/speech/train_speech.py \
        --data-path ml/speech/data/RAVDESS/ \
        --output-path ml/speech/models/speech_emotion_cnn_lstm.h5 \
        --epochs 40 --batch-size 32

RAVDESS filenames encode the label in the 3rd of 7 dash-separated fields,
e.g. "03-01-06-01-02-01-12.wav" -> emotion code "06". We map RAVDESS's
8-class scheme onto our shared 7-class taxonomy (RAVDESS's "calm" is
folded into "neutral" — there's no calm/neutral distinction in the face
or text models, so keeping it separate would break parity across
modalities).
"""

from __future__ import annotations

import argparse
import glob
import logging
import os
import sys

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from feature_extraction import extract_features, N_MFCC, MAX_PAD_LEN  # noqa: E402
from model import EMOTION_LABELS  # noqa: E402

# RAVDESS emotion code -> shared taxonomy label
_RAVDESS_CODE_MAP = {
    "01": "neutral",
    "02": "neutral",  # "calm" folded into neutral, see module docstring
    "03": "joy",
    "04": "sadness",
    "05": "anger",
    "06": "fear",
    "07": "disgust",
    "08": "surprise",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train CNN-LSTM speech emotion model on RAVDESS")
    parser.add_argument("--data-path", required=True, help="Path to RAVDESS root (contains Actor_* dirs)")
    parser.add_argument("--output-path", default="ml/speech/models/speech_emotion_cnn_lstm.pt")
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--val-split", type=float, default=0.15)
    return parser.parse_args()


def _label_from_filename(path: str) -> str | None:
    stem = os.path.splitext(os.path.basename(path))[0]
    parts = stem.split("-")
    if len(parts) < 3:
        return None
    return _RAVDESS_CODE_MAP.get(parts[2])


def build_dataset(data_path: str):
    files = sorted(glob.glob(os.path.join(data_path, "**", "*.wav"), recursive=True))
    if not files:
        raise FileNotFoundError(f"No .wav files found under {data_path}")

    label2id = {lbl: i for i, lbl in enumerate(EMOTION_LABELS)}
    X, y = [], []
    skipped = 0
    for f in files:
        label = _label_from_filename(f)
        if label is None:
            skipped += 1
            continue
        feats = extract_features(f)
        if not feats.valid:
            skipped += 1
            continue
        X.append(feats.mfcc)
        y.append(label2id[label])

    logger.info("Built dataset: %d examples, %d skipped", len(X), skipped)
    return np.stack(X), np.array(y)


def main() -> None:
    args = parse_args()

    try:
        import torch
        from torch.utils.data import DataLoader, TensorDataset, random_split
    except ImportError as exc:
        logger.error("PyTorch is required for training (%s). Install with: pip install torch", exc)
        sys.exit(1)

    from model import SpeechEmotionCNNLSTM

    X, y = build_dataset(args.data_path)
    X_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(1)  # (N, 1, n_mfcc, time)
    y_tensor = torch.tensor(y, dtype=torch.long)

    dataset = TensorDataset(X_tensor, y_tensor)
    val_size = int(len(dataset) * args.val_split)
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SpeechEmotionCNNLSTM(n_mfcc=N_MFCC).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = torch.nn.CrossEntropyLoss()

    best_val_acc = 0.0
    os.makedirs(os.path.dirname(args.output_path) or ".", exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * xb.size(0)

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                preds = model(xb).argmax(dim=1)
                correct += (preds == yb).sum().item()
                total += yb.size(0)
        val_acc = correct / total if total else 0.0

        logger.info(
            "Epoch %d/%d - train_loss=%.4f val_acc=%.4f",
            epoch, args.epochs, total_loss / len(train_ds), val_acc,
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), args.output_path)
            logger.info("Saved new best model (val_acc=%.4f) to %s", val_acc, args.output_path)

    logger.info("Training complete. Best val_acc=%.4f", best_val_acc)


if __name__ == "__main__":
    main()
