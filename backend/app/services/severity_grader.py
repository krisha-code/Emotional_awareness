class SeverityGrader:
    CRISIS_PHRASES = ["hopeless", "suicide", "want to die", "can't go on", "kill myself"]
    DISTRESS_PHRASES = ["exhausted", "worthless", "tired of trying", "no point"]
    
    CRISIS_RESOURCES = [
        "National Suicide Prevention Lifeline: 988",
        "Crisis Text Line: Text HOME to 741741",
        "iCall (India): 9152987821"
    ]

    def grade(self, fusion_result, text_result):
        if not fusion_result:
            return {'tier': 'low', 'action': 'Log silently', 'resources': []}
            
        conflict_score = fusion_result.get('conflict_score', 0)
        has_crisis_phrase = False
        has_distress_phrase = False
        
        if text_result and text_result.get('crisis_detected'):
            has_crisis_phrase = True
            
        if text_result and text_result.get('label') == 'distress':
            has_distress_phrase = True
            
        if has_crisis_phrase:
            return {
                'tier': 'critical',
                'action': 'Immediate escalation: crisis helpline surfaced, pre-consented emergency contact notified.',
                'resources': self.CRISIS_RESOURCES
            }
            
        if conflict_score > 0.7 or (has_distress_phrase and conflict_score > 0.4):
            return {
                'tier': 'high',
                'action': 'Direct follow-up question, surface self-help and professional resources.',
                'resources': self.CRISIS_RESOURCES[:1]
            }
            
        if conflict_score >= 0.4 and conflict_score <= 0.7:
            return {
                'tier': 'moderate',
                'action': 'Gentle check-in prompt, suggest a coping exercise.',
                'resources': []
            }
            
        return {
            'tier': 'low',
            'action': 'Minor or no mismatch. Log silently, no interruption.',
            'resources': []
        }
