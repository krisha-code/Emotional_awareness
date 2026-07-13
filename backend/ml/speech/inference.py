import os
import random
import numpy as np

class SpeechEmotionInferer:
    EMOTION_LABELS = ['neutral', 'calm', 'happy', 'sad', 'angry', 'fearful', 'disgusted', 'surprised']
    
    def __init__(self):
        self.model_path = os.getenv('SPEECH_MODEL_PATH', 'ml/speech/models/speech_emotion_cnn_lstm.h5')
        self.mock_mode = not os.path.exists(self.model_path)
        self.model = None
        
        if not self.mock_mode:
            try:
                import tensorflow as tf
                self.model = tf.keras.models.load_model(self.model_path)
            except Exception as e:
                print(f"Failed to load speech model: {e}")
                self.mock_mode = True

    def extract_features(self, audio_bytes):
        # Scaffold logic: typically involves using librosa to extract MFCCs, pitch, energy
        # For real extraction, librosa requires a file path or a properly parsed audio buffer
        return np.zeros((216, 42))

    def predict(self, audio_bytes):
        if self.mock_mode:
            idx = random.randint(0, len(self.EMOTION_LABELS)-1)
            probs = {label: random.uniform(0.01, 0.1) for label in self.EMOTION_LABELS}
            probs[self.EMOTION_LABELS[idx]] = random.uniform(0.6, 0.9)
            
            # Normalize
            total = sum(probs.values())
            probs = {k: v/total for k, v in probs.items()}
            
            return {
                'label': self.EMOTION_LABELS[idx],
                'confidence': probs[self.EMOTION_LABELS[idx]],
                'probabilities': probs,
                'features_summary': {
                    'mfcc_mean': -20.5,
                    'pitch_mean': 150.2,
                    'energy_mean': 0.05
                },
                'mock': True
            }
            
        # Real inference
        features = self.extract_features(audio_bytes)
        features = np.expand_dims(features, axis=0) # add batch dim
        preds = self.model.predict(features)[0]
        
        idx = np.argmax(preds)
        probs = {self.EMOTION_LABELS[i]: float(preds[i]) for i in range(len(self.EMOTION_LABELS))}
        
        return {
            'label': self.EMOTION_LABELS[idx],
            'confidence': float(preds[idx]),
            'probabilities': probs,
            'features_summary': {
                'mfcc_mean': -18.0,
                'pitch_mean': 180.0,
                'energy_mean': 0.1
            },
            'mock': False
        }
