import csv
import io
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.emotion_session import EmotionSession
from app.models.mood_journal import MoodJournalEntry

export_bp = Blueprint('export', __name__, url_prefix='/api/export')

@export_bp.route('/csv', methods=['GET'])
@jwt_required()
def export_csv():
    user_id = get_jwt_identity()
    sessions = EmotionSession.query.filter_by(user_id=user_id).order_by(EmotionSession.created_at.desc()).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Timestamp', 'Fused Emotion', 'Confidence', 'Conflict Detected', 'Conflict Score', 'Severity Tier'])
    
    for s in sessions:
        cw.writerow([
            s.created_at.isoformat(),
            s.fused_label,
            f"{s.fused_confidence:.2f}" if s.fused_confidence else "",
            s.conflict_detected,
            f"{s.conflict_score:.2f}" if s.conflict_score else "",
            s.severity_tier
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=emotion_history.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@export_bp.route('/journal', methods=['GET'])
@jwt_required()
def export_journal():
    user_id = get_jwt_identity()
    entries = MoodJournalEntry.query.filter_by(user_id=user_id).order_by(MoodJournalEntry.created_at.desc()).all()
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Timestamp', 'Mood Tag', 'Content', 'Tags'])
    
    for e in entries:
        cw.writerow([
            e.created_at.isoformat(),
            e.mood_tag,
            e.content,
            ",".join(e.tags) if e.tags else ""
        ])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=mood_journal.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@export_bp.route('/pdf', methods=['GET'])
@jwt_required()
def export_pdf():
    # Scaffold endpoint for PDF export, ideally uses reportlab to generate the PDF
    return jsonify({"message": "PDF export not implemented in base scaffold."}), 501
