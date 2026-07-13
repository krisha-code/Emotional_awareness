"""
FER2013 + MobileNetV2 Transfer Learning Training Script
Team Prompt 1 — Facial Intelligence & Backend Engineer

Dataset: FER2013 (Kaggle)
  https://www.kaggle.com/datasets/msambare/fer2013

Usage:
  python ml/face/train_fer2013.py \
      --data-path ml/face/data/fer2013.csv \
      --output-path ml/face/models/fer2013_mobilenetv2.h5 \
      --epochs 50 \
      --batch-size 64
"""

import argparse
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, callbacks
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

# ─── Constants ────────────────────────────────────────────────────────────────
EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
IMG_SIZE = 96          # MobileNetV2 minimum is 32x32; 96 gives better accuracy than 48x48
NUM_CLASSES = 7
CHANNELS = 3           # Convert grayscale FER2013 to RGB for MobileNetV2


# ─── Data Loading ─────────────────────────────────────────────────────────────
def load_fer2013(csv_path: str):
    """Load FER2013 CSV and return train/val/test splits as numpy arrays."""
    print(f"Loading FER2013 from: {csv_path}")
    df = pd.read_csv(csv_path)

    def parse_pixels(pixel_str):
        arr = np.array(pixel_str.split(), dtype=np.float32)
        return arr.reshape(48, 48, 1)

    X = np.array([parse_pixels(p) for p in df['pixels']])
    y = np.array(df['emotion'], dtype=np.int32)

    # Normalize to [0, 1]
    X = X / 255.0

    # Convert grayscale → RGB by repeating channels (MobileNetV2 needs 3 channels)
    X = np.repeat(X, 3, axis=-1)

    # Resize to IMG_SIZE
    X_resized = tf.image.resize(X, [IMG_SIZE, IMG_SIZE]).numpy()

    # Split by 'Usage' column if present, otherwise do 80/10/10
    if 'Usage' in df.columns:
        train_mask = df['Usage'] == 'Training'
        val_mask = df['Usage'] == 'PublicTest'
        test_mask = df['Usage'] == 'PrivateTest'
        X_train, y_train = X_resized[train_mask], y[train_mask]
        X_val, y_val = X_resized[val_mask], y[val_mask]
        X_test, y_test = X_resized[test_mask], y[test_mask]
    else:
        X_train, X_temp, y_train, y_temp = train_test_split(X_resized, y, test_size=0.2, random_state=42)
        X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

    print(f"Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    print(f"Label distribution (train): {np.bincount(y_train)}")
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


# ─── Model Architecture ────────────────────────────────────────────────────────
def build_model(num_classes: int = NUM_CLASSES, img_size: int = IMG_SIZE, fine_tune_layers: int = 30):
    """
    MobileNetV2 transfer learning model.
    Phase 1: Train classification head only (MobileNetV2 frozen).
    Phase 2: Fine-tune last `fine_tune_layers` layers.
    """
    base = MobileNetV2(
        input_shape=(img_size, img_size, CHANNELS),
        include_top=False,
        weights='imagenet'
    )
    base.trainable = False  # Freeze for phase 1

    inputs = layers.Input(shape=(img_size, img_size, CHANNELS))
    x = base(inputs, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(128, activation='relu')(x)
    x = layers.Dropout(0.3)(x)
    outputs = layers.Dense(num_classes, activation='softmax', name='emotion_output')(x)

    model = models.Model(inputs, outputs, name='mindsense_facial_emotion')
    return model, base


def enable_fine_tuning(model, base_model, fine_tune_layers: int = 30):
    """Unfreeze the top N layers of MobileNetV2 for fine-tuning."""
    base_model.trainable = True
    for layer in base_model.layers[:-fine_tune_layers]:
        layer.trainable = False
    print(f"Fine-tuning: {sum(1 for l in base_model.layers if l.trainable)} layers unfrozen")


# ─── Data Augmentation ─────────────────────────────────────────────────────────
def get_augmenter():
    return ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
        brightness_range=[0.8, 1.2],
        fill_mode='nearest'
    )


# ─── Training ─────────────────────────────────────────────────────────────────
def train(args):
    # Load data
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_fer2013(args.data_path)

    # Handle class imbalance with class weights
    class_counts = np.bincount(y_train)
    total = len(y_train)
    class_weights = {i: total / (NUM_CLASSES * count) for i, count in enumerate(class_counts)}
    print(f"Class weights: {class_weights}")

    # One-hot encode
    y_train_oh = tf.keras.utils.to_categorical(y_train, NUM_CLASSES)
    y_val_oh = tf.keras.utils.to_categorical(y_val, NUM_CLASSES)

    # Build model
    model, base_model = build_model()
    model.summary()

    # Augmenter
    aug = get_augmenter()

    # Callbacks
    cb = [
        callbacks.EarlyStopping(
            monitor='val_accuracy', patience=10, restore_best_weights=True, verbose=1
        ),
        callbacks.ReduceLROnPlateau(
            monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6, verbose=1
        ),
        callbacks.ModelCheckpoint(
            filepath=args.output_path.replace('.h5', '_best.h5'),
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1
        ),
    ]

    # ── Phase 1: Train head only ───────────────────────────────────────────────
    print("\n=== Phase 1: Training classification head (frozen backbone) ===")
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-3),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history1 = model.fit(
        aug.flow(X_train, y_train_oh, batch_size=args.batch_size),
        epochs=args.epochs // 2,
        validation_data=(X_val, y_val_oh),
        class_weight=class_weights,
        callbacks=cb,
        verbose=1
    )

    # ── Phase 2: Fine-tune top layers ─────────────────────────────────────────
    print("\n=== Phase 2: Fine-tuning top 30 MobileNetV2 layers ===")
    enable_fine_tuning(model, base_model, fine_tune_layers=30)
    model.compile(
        optimizer=optimizers.Adam(learning_rate=1e-5),  # Lower LR for fine-tuning
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    history2 = model.fit(
        aug.flow(X_train, y_train_oh, batch_size=args.batch_size),
        epochs=args.epochs // 2,
        validation_data=(X_val, y_val_oh),
        class_weight=class_weights,
        callbacks=cb,
        verbose=1
    )

    # ── Evaluation ─────────────────────────────────────────────────────────────
    print("\n=== Final Evaluation on Test Set ===")
    y_test_oh = tf.keras.utils.to_categorical(y_test, NUM_CLASSES)
    loss, acc = model.evaluate(X_test, y_test_oh, verbose=1)
    print(f"Test Accuracy: {acc:.4f} | Test Loss: {loss:.4f}")

    # Per-class accuracy
    y_pred = np.argmax(model.predict(X_test), axis=1)
    for i, label in enumerate(EMOTION_LABELS):
        mask = y_test == i
        class_acc = np.mean(y_pred[mask] == y_test[mask]) if mask.any() else 0
        print(f"  {label}: {class_acc:.3f} ({mask.sum()} samples)")

    # Save final model
    os.makedirs(os.path.dirname(args.output_path), exist_ok=True)
    model.save(args.output_path)
    print(f"\nModel saved to: {args.output_path}")

    # Save training plots
    _plot_history([history1, history2], os.path.dirname(args.output_path))

    return model


def _plot_history(histories, output_dir):
    """Save accuracy and loss curves."""
    acc = []
    val_acc = []
    loss = []
    val_loss = []
    for h in histories:
        acc.extend(h.history.get('accuracy', []))
        val_acc.extend(h.history.get('val_accuracy', []))
        loss.extend(h.history.get('loss', []))
        val_loss.extend(h.history.get('val_loss', []))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(acc, label='Train Accuracy')
    axes[0].plot(val_acc, label='Val Accuracy')
    axes[0].set_title('Accuracy')
    axes[0].legend()
    axes[1].plot(loss, label='Train Loss')
    axes[1].plot(val_loss, label='Val Loss')
    axes[1].set_title('Loss')
    axes[1].legend()
    plot_path = os.path.join(output_dir, 'training_curves.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Training curves saved to: {plot_path}")
    plt.close()


# ─── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train FER2013 Facial Emotion Model')
    parser.add_argument('--data-path', required=True, help='Path to fer2013.csv')
    parser.add_argument('--output-path', default='ml/face/models/fer2013_mobilenetv2.h5')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch-size', type=int, default=64)
    args = parser.parse_args()
    train(args)
