# MindSense — Multimodal Emotion-Aware System

<div align="center">
  <img src="docs/banner.png" alt="MindSense" width="800"/>
  <h3>Real-time multimodal emotion detection with cross-modal conflict analysis, full accessibility, and explainable AI</h3>

  [![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
  [![React 18](https://img.shields.io/badge/React-18-61DAFB?style=flat-square)](https://reactjs.org)
  [![Flask 3](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square)](https://flask.palletsprojects.com)
  [![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square)](https://postgresql.org)
  [![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square)](https://docker.com)
</div>

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quick Start (Docker)](#quick-start-docker)
5. [Manual Setup](#manual-setup)
6. [ML Model Training](#ml-model-training)
7. [API Reference](#api-reference)
8. [Shared JSON Schema](#shared-json-schema)
9. [Team Work Division](#team-work-division)
10. [Accessibility Features](#accessibility-features)
11. [Ethical Safeguards](#ethical-safeguards)

---

## System Overview

MindSense fuses **three emotional signals** (face, text, speech) plus optional physiological data from wearables to detect when signals contradict each other — the situations where single-modality systems fail most dangerously.

Key differentiators:
- **Cross-modal conflict detection** with a quantified conflict score
- **Severity-graded response** (Low → Critical) with matching escalation actions
- **Explainable AI** — shows *why* a conflict was flagged, not just that one was
- **Personalized baseline calibration** — cuts false positives for flat affect / dry humor
- **Longitudinal trend analysis** — detects slow decline over days/weeks
- **Full accessibility suite** — voice-first UI, audio earcons, sonified trends, haptic alerts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vite + React)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │FaceCapture│  │TextInput │  │AudioRec. │  │Accessibility │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  │    Bar       │   │
│       └─────────────┴─────────────┘         └──────────────┘   │
│                         ↓  REST API                             │
└─────────────────────────────────────────────────────────────────┘
                          ↓ /api/fusion/analyze
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (Flask)                          │
│                                                                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐  │
│  │  Face Model │   │  Text Model │   │  Speech Model       │  │
│  │ MobileNetV2 │   │ DistilBERT  │   │  CNN-LSTM + MFCC    │  │
│  └──────┬──────┘   └──────┬──────┘   └──────────┬──────────┘  │
│         └─────────────────┴──────────────────────┘             │
│                           ↓                                     │
│              ┌────────────────────────┐                         │
│              │     FUSION ENGINE      │                         │
│              │  Weighted fusion       │                         │
│              │  Conflict detection    │                         │
│              │  Severity grading      │                         │
│              │  XAI explanation       │                         │
│              └────────────┬───────────┘                         │
│                           ↓                                     │
│              ┌────────────────────────┐                         │
│              │    PostgreSQL + Redis  │                         │
│              │  Emotion history       │                         │
│              │  Baseline calibration  │                         │
│              │  JWT sessions          │                         │
│              └────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Vite + React 18 | SPA, component-based UI |
| Routing | React Router v6 | Client-side routing |
| Charts | Chart.js + react-chartjs-2 | Emotion history visualization |
| Animation | Framer Motion | Page transitions + micro-animations |
| Icons | Lucide React | Accessible icon set |
| Backend | Flask 3.0 | REST API, app factory pattern |
| ORM | SQLAlchemy + Flask-Migrate | Database models + migrations |
| Auth | Flask-JWT-Extended | JWT access + refresh tokens |
| Task Queue | Celery + Redis | Async inference (optional) |
| Face Model | TensorFlow/Keras MobileNetV2 | FER2013 transfer learning |
| Text Model | HuggingFace DistilBERT | Emotion + crisis detection |
| Speech Model | PyTorch CNN-LSTM | MFCC-based speech emotion |
| XAI | Grad-CAM + SHAP | Explainability layer |
| Database | PostgreSQL 16 | Structured emotion history |
| Cache/Queue | Redis 7 | JWT blocklist, task queue |
| Container | Docker Compose | One-command local dev |

---

## Quick Start (Docker)

> Prerequisites: Docker Desktop installed and running.

```bash
# 1. Clone the repository
git clone https://github.com/your-team/mindsense.git
cd mindsense

# 2. Copy environment file
cp backend/.env.example backend/.env
# Edit backend/.env and set your SECRET_KEY, JWT_SECRET_KEY

# 3. Start all services
docker-compose up --build

# 4. The app is running at:
#    Frontend:  http://localhost:5173
#    Backend:   http://localhost:5000
#    Postgres:  localhost:5432
#    Redis:     localhost:6379
```

---

## Manual Setup

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL and Redis connection strings

# Run database migrations
flask db upgrade

# Start development server
flask run --port 5000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server (proxies /api to localhost:5000)
npm run dev
# Opens at http://localhost:5173
```

---

## ML Model Training

> ⚠️ Training requires a GPU. Use Google Colab or Kaggle Notebooks for free GPU access.

### Face Model (FER2013 + MobileNetV2)

```bash
# Download FER2013 dataset from Kaggle:
# https://www.kaggle.com/datasets/msambare/fer2013

# Place dataset at: backend/ml/face/data/fer2013.csv

cd backend
python ml/face/train_fer2013.py \
    --data-path ml/face/data/fer2013.csv \
    --output-path ml/face/models/fer2013_mobilenetv2.h5 \
    --epochs 50 \
    --batch-size 64
```

### Text Model (DistilBERT)

```bash
# Using HuggingFace pretrained model (no training needed for demo)
# Model: bhadresh-savani/distilbert-base-uncased-emotion
# Will be auto-downloaded on first inference call

# OR fine-tune on custom dataset:
python ml/text/train_bert.py \
    --model distilbert-base-uncased \
    --output-path ml/text/models/distilbert_emotion
```

### Speech Model (CNN-LSTM + MFCC)

```bash
# Download RAVDESS dataset:
# https://zenodo.org/record/1188976

python ml/speech/train_speech.py \
    --data-path ml/speech/data/RAVDESS/ \
    --output-path ml/speech/models/speech_emotion_cnn_lstm.h5
```

> **Mock mode**: All models fall back to realistic random distributions if model files are not found. This lets you demo the entire system without trained models.

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login, receive JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | Logout (blocklists token) |
| GET | `/api/auth/me` | Get current user profile |
| PUT | `/api/auth/consent` | Update consent flags |

### Prediction
| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | `/api/predict/face` | Facial emotion from base64 image |
| POST | `/api/predict/text` | Text emotion + crisis detection |
| POST | `/api/predict/speech` | Speech emotion from audio file |
| POST | `/api/predict/physiological` | Mock wearable signal analysis |

### Fusion
| Method | Endpoint | Description |
|--------|---------|-------------|
| POST | `/api/fusion/analyze` | Full multimodal fusion analysis |
| GET | `/api/fusion/session/:id` | Get session details |

### History & Trends
| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/api/history/` | Paginated emotion history |
| GET | `/api/history/trends` | 7/30-day longitudinal trends |
| GET | `/api/history/summary` | Aggregate statistics |
| DELETE | `/api/history/:id` | Delete session (GDPR) |

### Export
| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/api/export/csv` | Download emotion history as CSV |
| GET | `/api/export/pdf` | Download PDF summary report |
| GET | `/api/export/journal` | Download mood journal as CSV |

---

## Shared JSON Schema

> **CRITICAL for team coordination**: All three modality models MUST return this format.

### Modality Result (face / text / speech)
```json
{
  "label": "sadness",
  "confidence": 0.84,
  "probabilities": {
    "joy": 0.03,
    "sadness": 0.84,
    "anger": 0.02,
    "fear": 0.05,
    "disgust": 0.01,
    "surprise": 0.02,
    "neutral": 0.03
  },
  "mock": false
}
```

### Fusion Result (POST /api/fusion/analyze response)
```json
{
  "session_id": "uuid",
  "timestamp": "2026-07-13T11:40:00Z",
  "modalities": {
    "face": { "...modality result..." },
    "text": {
      "...modality result...",
      "sarcasm_detected": false,
      "crisis_detected": false,
      "token_attributions": [{"token": "hopeless", "score": 0.91}]
    },
    "speech": { "...modality result..." },
    "physiological": {
      "arousal_level": "medium",
      "stress_indicator": 0.45,
      "label": "moderate_stress",
      "confidence": 0.70
    }
  },
  "fusion": {
    "fused_label": "sadness",
    "fused_confidence": 0.76,
    "conflict_detected": true,
    "conflict_score": 0.68,
    "modality_weights": {"face": 0.30, "text": 0.45, "speech": 0.20, "physiological": 0.05}
  },
  "severity": {
    "tier": "high",
    "action": "Direct follow-up question, surface self-help and professional resources",
    "resources": ["iCall: 9152987821", "Vandrevala Foundation: 1860-2662-345"]
  },
  "xai": {
    "face": {"region": "eyes", "intensity": 0.72, "description": "Downward gaze and narrowed eyes"},
    "text": {"top_tokens": [{"token": "hopeless", "score": 0.91}], "reasoning": "Word 'hopeless' strongly indicates distress"},
    "speech": {"dominant_band": "low_frequency", "energy": "subdued", "description": "Low energy, slow tempo"},
    "human_readable": "Text signals significant distress (word 'hopeless' — score 0.91) while face shows sadness markers. Speech corroborates with subdued energy. Combined confidence: HIGH."
  },
  "baseline_deviation": {
    "deviation_score": 0.62,
    "is_significant": true,
    "deviating_modalities": ["text", "face"]
  }
}
```

---

## Team Work Division

### 🧑‍💻 Prompt 1 — Facial Intelligence & Backend Engineer
**Files owned:**
- `backend/ml/face/` — FER2013 training, inference, face detection
- `backend/ml/physiological/` — Mock wearable
- `backend/app/routes/` — All Flask API routes
- `backend/app/models/` — Database ORM models
- `backend/migrations/` — Alembic migrations
- `docker-compose.yml`, `docker/Dockerfile.backend`

**First task:** Download FER2013, run `train_fer2013.py`, share the `.h5` model file with the team.

---

### 🧑‍💻 Prompt 2 — NLP & Speech Intelligence Engineer
**Files owned:**
- `backend/ml/text/` — DistilBERT inference, sarcasm detection, crisis detection
- `backend/ml/speech/` — CNN-LSTM training, MFCC extraction, inference
- `backend/app/services/fusion_engine.py` — Weighted fusion logic
- `backend/app/services/severity_grader.py` — Severity tier logic
- `backend/app/services/xai_explainer.py` — XAI explanation layer

**First task:** Test HuggingFace DistilBERT pipeline locally, confirm the shared JSON schema format with Prompt 1.

---

### 🧑‍💻 Prompt 3 — Integration & Frontend Engineer
**Files owned:**
- `frontend/` — Entire React application
- `backend/app/services/baseline.py` — Per-user calibration
- `backend/app/services/longitudinal.py` — Trend analysis
- `backend/app/routes/export.py` — PDF/CSV export
- `docker/Dockerfile.frontend`

**First task:** Run `npm install && npm run dev`, verify the UI renders. Wire the analyze page to the backend `/api/fusion/analyze` endpoint once it's stubbed.

---

## Accessibility Features

| Feature | Implementation |
|---------|---------------|
| Voice commands | Web Speech API `SpeechRecognition` |
| Screen reader | Semantic HTML + full ARIA labeling |
| Audio earcons | Web Audio API (synthesized, no files) |
| Sonified trends | Pitch-mapped emotion history playback |
| Spoken summary | `speechSynthesis` API |
| Haptic alerts | `navigator.vibrate` patterns |
| Audio-guided camera | `speechSynthesis` directional cues |
| One-step crisis | Persistent "Crisis Help" button + voice phrase |
| Braille | Falls out from correct ARIA/semantic HTML |
| Skip links | `.skip-link` class + ARIA |
| Focus visible | Custom focus rings, never hidden |
| Reduced motion | `@media (prefers-reduced-motion)` respected |

---

## Ethical Safeguards

> ⚠️ **Not a diagnostic tool.** This system flags patterns for human review — it does not diagnose mental health conditions.

- **No automated diagnosis** — all flags go to a human reviewer
- **Layered consent** — separate opt-ins for camera, mic, wearable, emergency contact
- **Data minimization** — only derived scores stored server-side (not raw video/audio)
- **Encryption** — sensitive fields encrypted at rest; HTTPS in production
- **Right to erasure** — DELETE /api/history/:id + DELETE /api/auth/account
- **Bias testing** — FER2013 is known to have label noise; validate across demographics before deployment
- **Clinical review required** — severity thresholds must be reviewed by a mental health professional before production use

---

## Project Structure

```
Emotional_awareness/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── config.py            # Dev/Prod/Test configs
│   │   ├── extensions.py        # SQLAlchemy, JWT, CORS
│   │   ├── models/              # ORM: User, EmotionSession, MoodJournal
│   │   ├── routes/              # Blueprints: auth, predict, fusion, history, export
│   │   └── services/            # Business logic: fusion, severity, XAI, baseline, longitudinal
│   ├── ml/
│   │   ├── face/                # CNN (MobileNetV2) training + inference
│   │   ├── text/                # DistilBERT inference + sarcasm/crisis detection
│   │   ├── speech/              # CNN-LSTM training + MFCC extraction
│   │   └── physiological/       # Mock wearable signals
│   ├── migrations/              # Alembic migrations
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # FaceCapture, TextInput, AudioRecorder, FusionResult...
│   │   ├── pages/               # Home, Analyze, History, Journal, Settings, Login
│   │   ├── context/             # AuthContext, EmotionContext
│   │   ├── api/                 # Axios client + typed API functions
│   │   └── accessibility/       # voiceCommands, earcons, sonification
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
└── README.md
```

---

## License

For academic/research use. Not for production mental health deployment without clinical review.
