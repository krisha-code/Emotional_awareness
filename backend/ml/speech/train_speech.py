"""
Speech Emotion Recognition — CNN-LSTM Training Script
Team Prompt 2 — NLP & Speech Intelligence Engineer

Dataset: RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)
  https://zenodo.org/record/1188976

Features: MFCC (40 coefficients) + pitch contour + energy
Model: CNN layers → BiLSTM → Dense classification head

Usage:
  python ml/speech/train_speech.py \
      --data-path ml/speech/data/RAVDESS/ \
      --output-path ml/speech/models/speech_emotion_cnn_lstm.h5
"""

import argparse
import os
import glob
import numpy as np
import librosa
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
import matplotlib.pyplot as plt

# ─── Constants ────────────────────────────────────────────────────────────────
# RAVDESS emotion codes in filename (3rd segment):
# 01=neutral, 02=calm, 03=happy, 04=sad, 05=angry, 06=fearful, 07=disgusted, 08=surprised
RAVDESS_EMOTION_MAP = {
    '01': 'neutral', '02': 'calm', '03': 'happy', '04': 'sad',
    '05': 'angry', '06': 'fearful', '07': 'disgusted', '08': 'surprised'
}
EMOTION_LABELS = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised']

N_MFCC = 40        # Number of MFCC coefficients
MAX_PAD_LEN = 216  # Pad/truncate all features to this time dimension
SAMPLE_RATE = 22050


# ─── Feature Extraction ────────────────────────────────────────────────────────
def extract_features(file_path: str, max_pad_len: int = MAX_PAD_LEN) -> np.ndarray:
    """
    Extract MFCC + pitch + energy features from an audio file.
    Returns shape: (max_pad_len, N_MFCC + 2) — time steps × features
    """
    try:
        y, sr = librosa.load(file_path, sr=SAMPLE_RATE, duration=3.0)

        # MFCC
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC)  # (N_MFCC, time)

        # Pitch (fundamental frequency)
        f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        f0 = np.nan_to_num(f0)
        f0 = f0[np.newaxis, :]  # (1, time)

        # RMS energy
        rms = librosa.feature.rms(y=y)  # (1, time)

        # Combine: (N_MFCC + 2, time) → transpose to (time, N_MFCC + 2)
        combined = np.vstack([mfcc, f0, rms])  # (42, time)
        combined = combined.T  # (time, 42)

        # Pad or truncate to max_pad_len
        if combined.shape[0] < max_pad_len:
            pad_width = max_pad_len - combined.shape[0]
            combined = np.pad(combined, ((0, pad_width), (0, 0)), mode='constant')
        else:
            combined = combined[:max_pad_len, :]

        return combined

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return np.zeros((max_pad_len, N_MFCC + 2))


def extract_emotion_from_filename(filename: str) -> str | None:
    """
    RAVDESS filename format: 03-01-05-01-01-01-24.wav
    Position 2 (0-indexed) = emotion code
    """
    parts = os.path.basename(filename).replace('.wav', '').split('-')
    if len(parts) >= 3:
        return RAVDESS_EMOTION_MAP.get(parts[2])
    return None


# ─── Dataset Loading ───────────────────────────────────────────────────────────
def load_dataset(data_path: str):
    """Walk RAVDESS directory, extract features and labels."""
    audio_files = glob.glob(os.path.join(data_path, '**', '*.wav'), recursive=True)
    print(f"Found {len(audio_files)} audio files")

    features = []
    labels = []

    for i, fp in enumerate(audio_files):
        if i % 100 == 0:
            print(f"Processing {i}/{len(audio_files)}...")
        emotion = extract_emotion_from_filename(fp)
        if emotion is None:
            continue
        feat = extract_features(fp)
        features.append(feat)
        labels.append(emotion)

    X = np.array(features)  # (N, MAX_PAD_LEN, N_MFCC+2)
    le = LabelEncoder()
    y = le.fit_transform(labels)

    print(f"\nDataset shape: X={X.shape}, y={y.shape}")
    print(f"Classes: {le.classes_}")
    print(f"Label distribution: {np.bincount(y)}")

    return X, y, le


# ─── Model Architecture ────────────────────────────────────────────────────────
def build_cnn_lstm_model(input_shape, num_classes: int):
    """
    CNN feature extractor → BiLSTM sequence model → classification head.

    Input: (batch, MAX_PAD_LEN, N_MFCC+2) i.e. (batch, 216, 42)
    """
    inputs = layers.Input(shape=input_shape, name='mfcc_input')

    # ── CNN Feature Extraction (treats time as spatial) ──────────────────────
    x = layers.Reshape((input_shape[0], input_shape[1], 1))(inputs)  # Add channel dim

    x = layers.Conv2D(64, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Dropout(0.25)(x)

    x = layers.Conv2D(128, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Dropout(0.25)(x)

    x = layers.Conv2D(256, (3, 3), padding='same', activation='relu')(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 1))(x)

    # Reshape for LSTM: merge spatial dims, keep time
    shape = x.shape
    x = layers.Reshape((shape[1], shape[2] * shape[3]))(x)

    # ── Bidirectional LSTM ──────────────────────────────────────────────────
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.3))(x)
    x = layers.Bidirectional(layers.LSTM(64, dropout=0.3))(x)

    # ── Classification Head ─────────────────────────────────────────────────
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(128, activation='relu')(x)
    outputs = layers.Dense(num_classes, activation='softmax', name='emotion_output')(x)

    model = models.Model(inputs, outputs, name='mindsense_speech_emotion')
    return model


# ─── Training ─────────────────────────────────────────────────────────────────
def train(args):
    X, y, label_encoder = load_dataset(args.data_path)

    # Train / val / test split (70/15/15)
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

    num_classes = len(label_encoder.classes_)
    y_train_oh = tf.keras.utils.to_categorical(y_train, num_classes)
    y_val_oh = tf.keras.utils.to_categorical(y_val, num_classes)

    # Class weights
    class_counts = np.bincount(y_train)
    total = len(y_train)
    class_weights = {i: total / (num_classes * c) for i, c in enumerate(class_counts)}

    model = build_cnn_lstm_model(input_shape=(X.shape[1], X.shape[2]), num_classes=num_classes)
    model.summary()

    cb = [
        callbacks.EarlyStopping(monitor='val_accuracy', patience=15, restore_best_weights=True),
        callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=1e-6),
        callbacks.ModelCheckpoint(
            filepath=args.output_path.replace('.h5', '_best.h5'),
            monitor='val_accuracy', save_best_only=True
        ),
    ]

    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history = model.fit(
        X_train, y_train_oh,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_data=(X_val, y_val_oh),
        class_weight=class_weights,
        callbacks=cb,
        verbose=1
    )

    # Evaluation
    y_test_oh = tf.keras.utils.to_categorical(y_test, num_classes)
    loss, acc = model.evaluate(X_test, y_test_oh)
    print(f"\nTest Accuracy: {acc:.4f} | Test Loss: {loss:.4f}")

    y_pred = np.argmax(model.predict(X_test), axis=1)
    for i, label in enumerate(label_encoder.classes_):
        mask = y_test == i
        class_acc = np.mean(y_pred[mask] == y_test[mask]) if mask.any() else 0
        print(f"  {label}: {class_acc:.3f}")

    # Save
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    model.save(args.output_path)

    # Save label encoder classes
    np.save(args.output_path.replace('.h5', '_classes.npy'), label_encoder.classes_)
    print(f"Model saved to: {args.output_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train Speech Emotion Model (CNN-LSTM)')
    parser.add_argument('--data-path', required=True, help='Path to RAVDESS dataset directory')
    parser.add_argument('--output-path', default='ml/speech/models/speech_emotion_cnn_lstm.h5')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args()
    train(args)
