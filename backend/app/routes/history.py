from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.emotion_session import EmotionSession
from app.services.longitudinal import LongitudinalAnalyzer

history_bp = Blueprint('history', __name__, url_prefix='/api/history')
analyzer = LongitudinalAnalyzer()

@history_bp.route('/', methods=['GET'])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = EmotionSession.query.filter_by(user_id=user_id)\
        .order_by(EmotionSession.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    sessions = [session.to_dict() for session in pagination.items]

    return jsonify({
        'sessions': sessions,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@history_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    user_id = get_jwt_identity()
    days = request.args.get('days', 7, type=int)

    sessions = EmotionSession.query.filter_by(user_id=user_id)\
        .order_by(EmotionSession.created_at.desc())\
        .limit(days * 10)\
        .all()  # Rough limit, assuming max 10 sessions/day

    session_dicts = [s.to_dict() for s in sessions]
    trends = analyzer.analyze_trends(session_dicts, days=days)

    return jsonify(trends), 200

@history_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    user_id = get_jwt_identity()
    
    sessions = EmotionSession.query.filter_by(user_id=user_id).all()
    if not sessions:
        return jsonify({'message': 'No history available.'}), 404
        
    conflict_count = sum(1 for s in sessions if s.conflict_detected)
    
    severity_distribution = {'low': 0, 'moderate': 0, 'high': 0, 'critical': 0}
    for s in sessions:
        if s.severity_tier in severity_distribution:
            severity_distribution[s.severity_tier] += 1
            
    dominant_emotions = {}
    for s in sessions:
        if s.fused_label:
            dominant_emotions[s.fused_label] = dominant_emotions.get(s.fused_label, 0) + 1

    return jsonify({
        'total_sessions': len(sessions),
        'conflict_rate': conflict_count / len(sessions) if sessions else 0,
        'severity_distribution': severity_distribution,
        'dominant_emotions': dominant_emotions
    }), 200

@history_bp.route('/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    user_id = get_jwt_identity()
    session = EmotionSession.query.filter_by(id=session_id, user_id=user_id).first()
    
    if not session:
        return jsonify({'error': 'Session not found or unauthorized.'}), 404
        
    from app.extensions import db
    db.session.delete(session)
    db.session.commit()
    
    return jsonify({'message': 'Session deleted successfully.'}), 200
