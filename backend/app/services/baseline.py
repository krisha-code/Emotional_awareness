class BaselineCalibrator:
    def initialize_baseline(self, emotion_distribution=None):
        return {
            'face': {'avg_confidence': 0.0, 'label_counts': {}},
            'text': {'avg_confidence': 0.0, 'label_counts': {}},
            'speech': {'avg_confidence': 0.0, 'label_counts': {}},
            'sessions_count': 0
        }

    def update_baseline(self, user_id, session_result, current_baseline=None):
        if not current_baseline:
            current_baseline = self.initialize_baseline()
            
        count = current_baseline.get('sessions_count', 0)
        alpha = 2.0 / (count + 2.0)  # Exponential moving average weight
        
        for mod in ['face', 'text', 'speech']:
            if mod in session_result and session_result[mod]:
                label = session_result[mod].get('label')
                conf = session_result[mod].get('confidence', 0)
                
                if label:
                    counts = current_baseline[mod].get('label_counts', {})
                    counts[label] = counts.get(label, 0) + 1
                    current_baseline[mod]['label_counts'] = counts
                    
                prev_conf = current_baseline[mod].get('avg_confidence', 0)
                current_baseline[mod]['avg_confidence'] = (alpha * conf) + ((1 - alpha) * prev_conf)
                
        current_baseline['sessions_count'] = count + 1
        return current_baseline

    def calculate_deviation(self, user_id, session_result, baseline_data):
        if not baseline_data or baseline_data.get('sessions_count', 0) < 5:
            return {'deviation_score': 0.0, 'is_significant': False, 'deviating_modalities': []}
            
        deviations = []
        score = 0.0
        
        for mod in ['face', 'text', 'speech']:
            if mod in session_result and session_result[mod]:
                label = session_result[mod].get('label')
                # If the user rarely expresses this label, it's a deviation
                counts = baseline_data[mod].get('label_counts', {})
                total_mod_sessions = sum(counts.values())
                if total_mod_sessions > 0:
                    freq = counts.get(label, 0) / total_mod_sessions
                    if freq < 0.1:  # Happens less than 10% of the time for this user
                        deviations.append(mod)
                        score += 0.33
                        
        return {
            'deviation_score': score,
            'is_significant': score > 0.5,
            'deviating_modalities': deviations
        }
