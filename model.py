"""
backend/ml/speech/model.py

CNN-LSTM hybrid architecture for speech emotion recognition over MFCC
sequences, matching the README tech stack entry ("PyTorch CNN-LSTM").

Input:  (batch, 1, N_MFCC, T)   -- MFCC "image" per utterance
Output: (batch, NUM_CLASSES)     -- logits over the shared 7-class taxonomy

Architecture rationale:
- Conv2D stack over the MFCC time-frequency grid captures local spectral
  patterns (formant-like structure, short energy bursts) the way it would
  treat a spectrogram image.
- The conv output is unrolled along time and fed to a bidirectional LSTM
  to capture the temporal dynamics of tone/prosody across the utterance
  (rising pitch, trailing-off energy, etc.) that a pure CNN would miss.
- A small attention-pooling layer over the LSTM outputs lets the model
  weight the most emotionally salient frames rather than averaging
  everything uniformly.
"""

from __future__ import annotations

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    _TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when torch missing
    _TORCH_AVAILABLE = False

# Shared taxonomy — same order as backend/ml/text/emotion_model.EMOTION_LABELS
EMOTION_LABELS = ["joy", "sadness", "anger", "fear", "disgust", "surprise", "neutral"]
NUM_CLASSES = len(EMOTION_LABELS)


if _TORCH_AVAILABLE:

    class AttentionPool(nn.Module):
        """Learned weighted average over the time dimension of LSTM outputs."""

        def __init__(self, hidden_dim: int):
            super().__init__()
            self.score = nn.Linear(hidden_dim, 1)

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (batch, time, hidden_dim)
            weights = F.softmax(self.score(x).squeeze(-1), dim=1)  # (batch, time)
            return torch.bmm(weights.unsqueeze(1), x).squeeze(1)  # (batch, hidden_dim)

    class SpeechEmotionCNNLSTM(nn.Module):
        def __init__(
            self,
            n_mfcc: int = 40,
            cnn_channels: tuple = (16, 32),
            lstm_hidden: int = 64,
            lstm_layers: int = 1,
            num_classes: int = NUM_CLASSES,
            dropout: float = 0.3,
        ):
            super().__init__()

            c1, c2 = cnn_channels
            self.conv = nn.Sequential(
                nn.Conv2d(1, c1, kernel_size=3, padding=1),
                nn.BatchNorm2d(c1),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=(2, 2)),
                nn.Conv2d(c1, c2, kernel_size=3, padding=1),
                nn.BatchNorm2d(c2),
                nn.ReLU(),
                nn.MaxPool2d(kernel_size=(2, 2)),
                nn.Dropout(dropout),
            )

            # After two (2,2) pools, frequency axis n_mfcc -> n_mfcc // 4
            freq_after_pool = n_mfcc // 4
            lstm_input_dim = c2 * freq_after_pool

            self.lstm = nn.LSTM(
                input_size=lstm_input_dim,
                hidden_size=lstm_hidden,
                num_layers=lstm_layers,
                batch_first=True,
                bidirectional=True,
                dropout=dropout if lstm_layers > 1 else 0.0,
            )
            self.attn_pool = AttentionPool(lstm_hidden * 2)
            self.classifier = nn.Sequential(
                nn.Linear(lstm_hidden * 2, lstm_hidden),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(lstm_hidden, num_classes),
            )

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            # x: (batch, 1, n_mfcc, time)
            feat = self.conv(x)  # (batch, c2, freq', time')
            batch, channels, freq, time = feat.shape
            feat = feat.permute(0, 3, 1, 2).reshape(batch, time, channels * freq)  # (batch, time', c2*freq')
            lstm_out, _ = self.lstm(feat)  # (batch, time', lstm_hidden*2)
            pooled = self.attn_pool(lstm_out)  # (batch, lstm_hidden*2)
            return self.classifier(pooled)  # (batch, num_classes)

else:

    class SpeechEmotionCNNLSTM:  # type: ignore
        """Placeholder used only when torch isn't installed (mock-mode environments)."""

        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PyTorch is required to instantiate SpeechEmotionCNNLSTM. "
                "Install with: pip install torch"
            )
