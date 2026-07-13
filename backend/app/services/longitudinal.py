from datetime import datetime, timedelta

class LongitudinalAnalyzer:
    def _severity_to_score(self, tier):
        scores = {'low': 1, 'moderate': 2, 'high': 3, 'critical': 4}
        return scores.get(tier, 1)

    def analyze_trends(self, sessions, days=7):
        if not sessions:
            return {
                'daily_emotion_distribution': {},
                'dominant_emotion_per_day': {},
                'conflict_rate_trend': [],
                'severity_trend': [],
                'overall_trend_direction': 'stable',
                'low_points': [],
                'spoken_summary': "No recent data available to analyze trends."
            }

        # Date parsing
        for s in sessions:
            if isinstance(s['created_at'], str):
                s['date_obj'] = datetime.fromisoformat(s['created_at'].replace('Z', '+00:00')).date()
            else:
                s['date_obj'] = s['created_at'].date()
                
        # Group by date
        by_date = {}
        for s in sessions:
            d_str = s['date_obj'].isoformat()
            if d_str not in by_date:
                by_date[d_str] = []
            by_date[d_str].append(s)
            
        daily_emotion_distribution = {}
        dominant_emotion_per_day = {}
        conflict_rate_trend = []
        severity_trend = []
        low_points = []
        
        dates_sorted = sorted(by_date.keys())
        
        for d in dates_sorted:
            day_sessions = by_date[d]
            dist = {}
            conflict_count = 0
            severity_sum = 0
            
            for s in day_sessions:
                label = s.get('fused_label', 'neutral')
                dist[label] = dist.get(label, 0) + 1
                if s.get('conflict_detected'):
                    conflict_count += 1
                severity_sum += self._severity_to_score(s.get('severity_tier', 'low'))
                
            daily_emotion_distribution[d] = dist
            dominant_emotion_per_day[d] = max(dist.items(), key=lambda x: x[1])[0] if dist else 'neutral'
            
            conflict_rate = conflict_count / len(day_sessions)
            conflict_rate_trend.append({'date': d, 'rate': conflict_rate})
            
            avg_severity = severity_sum / len(day_sessions)
            severity_trend.append({'date': d, 'avg_severity_score': avg_severity})
            
            if avg_severity >= 2.5 or dominant_emotion_per_day[d] in ['distress', 'sadness', 'fear']:
                low_points.append(d)

        # Calculate overall trend direction
        trend_dir = 'stable'
        if len(severity_trend) >= 2:
            start_sev = severity_trend[0]['avg_severity_score']
            end_sev = severity_trend[-1]['avg_severity_score']
            if end_sev - start_sev >= 1.0:
                trend_dir = 'declining'  # getting worse
            elif start_sev - end_sev >= 1.0:
                trend_dir = 'improving'
                
        # Spoken summary
        if trend_dir == 'declining':
            spoken = "Your overall stress levels seem to be increasing recently."
        elif trend_dir == 'improving':
            spoken = "You seem to be feeling more positive compared to a few days ago."
        else:
            spoken = "Your emotional state has been relatively stable recently."
            
        if low_points:
            spoken += " I noticed some particularly difficult moments on certain days."

        return {
            'daily_emotion_distribution': daily_emotion_distribution,
            'dominant_emotion_per_day': dominant_emotion_per_day,
            'conflict_rate_trend': conflict_rate_trend,
            'severity_trend': severity_trend,
            'overall_trend_direction': trend_dir,
            'low_points': low_points,
            'spoken_summary': spoken
        }
