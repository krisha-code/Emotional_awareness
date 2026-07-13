import os
import random
import base64
import numpy as np
import cv2

class FaceEmotionInferer:
    EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
    
    def __init__(self):
        self.model_path = os.getenv('FACE_MODEL_PATH', 'ml/face/models/fer2013_mobilenetv2.h5')
        self.mock_mode = not os.path.exists(self.model_path)
        self.model = None
        
        if not self.mock_mode:
            try:
                import tensorflow as tf
                self.model = tf.keras.models.load_model(self.model_path)
            except Exception as e:
                print(f"Failed to load face model: {e}")
                self.mock_mode = True

    def preprocess(self, image_base64):
        # Decode base64 image
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        img_data = base64.b64decode(image_base64)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Here you would typically use Haar cascades or MTCNN to crop the face
        # For simplicity in the scaffold, we just resize the whole image to 96x96
        if img is not None:
            img = cv2.resize(img, (96, 96))
            img = img / 255.0
            return np.expand_dims(img, axis=0)
        return None

    def predict(self, image_base64):
        if self.mock_mode:
            # Generate realistic random distribution
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
                'gradcam_hint': {'region': 'eyes', 'intensity': 0.8},
                'mock': True
            }
            
        # Real inference
        img_array = self.preprocess(image_base64)
        if img_array is None:
            raise ValueError("Failed to preprocess image")
            
        preds = self.model.predict(img_array)[0]
        idx = np.argmax(preds)
        probs = {self.EMOTION_LABELS[i]: float(preds[i]) for i in range(len(self.EMOTION_LABELS))}
        
        return {
            'label': self.EMOTION_LABELS[idx],
            'confidence': float(preds[idx]),
            'probabilities': probs,
            'gradcam_hint': {'region': 'mouth', 'intensity': 0.7}, # Mocked XAI for now
            'mock': False
        }
