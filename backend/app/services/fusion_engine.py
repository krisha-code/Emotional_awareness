import math

class FusionEngine:
    DISTRESS_KEYWORDS = ["hopeless", "suicide", "worthless", "want to die", "can't go on", "end it"]
    
    def __init__(self):
        # Default base weights
        self.base_weights = {
            'text': 0.45,
            'face': 0.30,
            'speech': 0.20,
            'physiological': 0.05
        }
        
        # Valence scores (rough mapping from -1 to 1)
        self.emotion_valence = {
            'happy': 1.0, 'joy': 1.0,
            'neutral': 0.0, 'calm': 0.0, 'surprise': 0.5, 'surprised': 0.5,
            'sad': -0.8, 'sadness': -0.8,
            'angry': -0.8, 'anger': -0.8,
            'fear': -0.9, 'fearful': -0.9,
            'disgust': -0.7, 'disgusted': -0.7,
            'distress': -1.0
        }

    def fuse(self, face_result, text_result, speech_result, physiological_result=None):
        weights = self.base_weights.copy()
        
        # Elevate text weight if distress is found
        has_distress_text = False
        if text_result and text_result.get('label') == 'distress' or text_result.get('crisis_detected', False):
            has_distress_text = True
            weights['text'] = 0.65
            weights['face'] = 0.20
            weights['speech'] = 0.10
            weights['physiological'] = 0.05
            
        # Ensure weights sum to 1 for modalities that are present
        present_weights = {}
        if face_result: present_weights['face'] = weights['face']
        if text_result: present_weights['text'] = weights['text']
        if speech_result: present_weights['speech'] = weights['speech']
        if physiological_result: present_weights['physiological'] = weights['physiological']
        
        total_weight = sum(present_weights.values())
        if total_weight == 0:
            return None
            
        normalized_weights = {k: v / total_weight for k, v in present_weights.items()}
        
        # Calculate conflict score
        valences = []
        if face_result and face_result.get('label'):
            valences.append(self.emotion_valence.get(face_result['label'].lower(), 0))
        if text_result and text_result.get('label'):
            valences.append(self.emotion_valence.get(text_result['label'].lower(), 0))
        if speech_result and speech_result.get('label'):
            valences.append(self.emotion_valence.get(speech_result['label'].lower(), 0))
            
        conflict_score = self._calculate_valence_distance(valences)
        conflict_detected = conflict_score > 0.4
        
        # Determine fused label based on highest weighted confidence
        # In a real system, you'd multiply full probability distributions.
        scores = {}
        for mod, result in [('face', face_result), ('text', text_result), ('speech', speech_result)]:
            if result and result.get('label'):
                label = result['label'].lower()
                scores[label] = scores.get(label, 0) + (result.get('confidence', 0) * normalized_weights[mod])
                
        if scores:
            fused_label = max(scores.items(), key=lambda x: x[1])[0]
            fused_confidence = min(1.0, max(scores.values()) * 1.5)  # Roughly scaling up
        else:
            fused_label = 'neutral'
            fused_confidence = 0.0
            
        # If distress is heavily weighted, force distress label
        if has_distress_text:
            fused_label = 'distress'
            fused_confidence = max(0.9, fused_confidence)

        return {
            'fused_label': fused_label,
            'fused_confidence': fused_confidence,
            'conflict_detected': conflict_detected,
            'conflict_score': conflict_score,
            'modality_weights_used': normalized_weights
        }

    def _calculate_valence_distance(self, valences):
        if len(valences) < 2:
            return 0.0
        # Calculate maximum absolute difference in valences
        return max(valences) - min(valences)
