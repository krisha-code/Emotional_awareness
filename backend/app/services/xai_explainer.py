class XAIExplainer:
    def explain_face(self, image_array, model=None, predicted_class=None):
        # In a real scenario, use Grad-CAM algorithm to find salient regions.
        # Here we simulate the output metadata for the UI to display.
        return {
            'region': 'eyes and mouth',
            'intensity': 0.75,
            'description': 'Features around the eyes and mouth strongly correlate with the predicted emotion.'
        }

    def explain_text(self, text, label, token_scores=None):
        # LIME/SHAP attribution simulation
        if not token_scores:
            words = text.split()
            # Mock some token attributions for the UI
            token_scores = [{'token': w, 'score': 0.8 if len(w)>4 else 0.2} for w in words]
            
        return {
            'top_tokens': sorted(token_scores, key=lambda x: x['score'], reverse=True)[:3],
            'reasoning': f"Specific words drove the '{label}' classification."
        }

    def explain_speech(self, mfcc_features, label):
        return {
            'dominant_frequency_band': 'mid-range',
            'energy_profile': 'high' if label in ['angry', 'fear', 'happy'] else 'low',
            'description': 'Acoustic energy and pitch variation mapped to the predicted emotion.'
        }

    def build_explanation(self, face_xai, text_xai, speech_xai, fusion_result):
        if not fusion_result:
            return {}
            
        human_readable = []
        if fusion_result.get('conflict_detected'):
            human_readable.append("Conflict detected across modalities.")
            
        human_readable.append(f"System concluded with {fusion_result.get('fused_label')} based on weighted fusion.")
        
        return {
            'face': face_xai,
            'text': text_xai,
            'speech': speech_xai,
            'human_readable': " ".join(human_readable)
        }
