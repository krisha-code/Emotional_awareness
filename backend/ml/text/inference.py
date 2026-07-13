import re
import random

class TextEmotionInferer:
    EMOTION_LABELS = ['joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise', 'distress', 'neutral']
    
    SARCASM_PATTERNS = [
        r"(?i)\b(just great)\b",
        r"(?i)\b(oh wonderful)\b",
        r"(?i)\b(perfect timing)\b",
        r"(?i)\b(yeah, right)\b"
    ]
    
    CRISIS_PHRASES = [
        r"(?i)\b(kill myself)\b",
        r"(?i)\b(want to die)\b",
        r"(?i)\b(end it all)\b",
        r"(?i)\b(hopeless)\b",
        r"(?i)\b(no point in living)\b",
        r"(?i)\b(can't go on)\b"
    ]

    def __init__(self):
        self.mock_mode = True # Use mock by default to avoid heavy HF downloads on startup

    def detect_sarcasm(self, text):
        return any(re.search(pattern, text) for pattern in self.SARCASM_PATTERNS)

    def detect_crisis(self, text):
        return any(re.search(pattern, text) for pattern in self.CRISIS_PHRASES)

    def predict(self, text):
        crisis = self.detect_crisis(text)
        sarcasm = self.detect_sarcasm(text)
        
        if self.mock_mode:
            if crisis:
                probs = {label: 0.05 for label in self.EMOTION_LABELS}
                probs['distress'] = 0.95
                idx = self.EMOTION_LABELS.index('distress')
            else:
                idx = random.randint(0, len(self.EMOTION_LABELS)-1)
                probs = {label: random.uniform(0.01, 0.1) for label in self.EMOTION_LABELS}
                probs[self.EMOTION_LABELS[idx]] = random.uniform(0.6, 0.9)
                
                # Normalize
                total = sum(probs.values())
                probs = {k: v/total for k, v in probs.items()}
                
            token_scores = [{'token': w, 'score': random.uniform(0.1, 0.9)} for w in text.split()]
                
            return {
                'label': self.EMOTION_LABELS[idx],
                'confidence': probs[self.EMOTION_LABELS[idx]],
                'probabilities': probs,
                'sarcasm_detected': sarcasm,
                'crisis_detected': crisis,
                'token_attributions': token_scores,
                'mock': True
            }
