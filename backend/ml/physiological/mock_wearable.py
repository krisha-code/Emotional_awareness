import random

class MockWearableInferer:
    # Typical ranges
    HEART_RATE_RANGE = (60, 180)  # bpm
    HRV_RANGE = (20, 100)         # ms
    EDA_RANGE = (0.5, 20.0)       # microsiemens
    SKIN_TEMP_RANGE = (32.0, 37.0) # Celsius
    
    def analyze(self, heart_rate, hrv, eda, skin_temp):
        stress_score = 0.0
        
        if heart_rate > 100: stress_score += 0.3
        if heart_rate > 120: stress_score += 0.2
        if hrv < 40: stress_score += 0.2
        if eda > 10.0: stress_score += 0.2
        if skin_temp < 33.0: stress_score += 0.1 # Stress can cause peripheral vasoconstriction (colder skin)
        
        stress_score = min(1.0, stress_score)
        
        if stress_score < 0.3:
            arousal = 'low'
            label = 'calm'
        elif stress_score < 0.7:
            arousal = 'medium'
            label = 'moderate_stress'
        else:
            arousal = 'high'
            label = 'high_stress'
            
        return {
            'arousal_level': arousal,
            'stress_indicator': stress_score,
            'label': label,
            'confidence': 0.8 + (0.2 * stress_score),
            'raw': {
                'heart_rate': heart_rate,
                'hrv': hrv,
                'eda': eda,
                'skin_temp': skin_temp
            }
        }
        
    def generate_mock_reading(self):
        # Generate random state: 0=calm, 1=stressed
        is_stressed = random.choice([True, False])
        
        if is_stressed:
            hr = random.uniform(95, 140)
            hrv = random.uniform(20, 45)
            eda = random.uniform(8.0, 15.0)
            temp = random.uniform(32.0, 34.5)
        else:
            hr = random.uniform(60, 85)
            hrv = random.uniform(50, 90)
            eda = random.uniform(1.0, 5.0)
            temp = random.uniform(34.0, 36.5)
            
        return {
            'heart_rate': hr,
            'hrv': hrv,
            'eda': eda,
            'skin_temp': temp
        }
