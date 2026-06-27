"""
Mental Health Module Routes
Handles mood tracking, mental health assessments, journaling, and wellness habits
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from database import db
from database.models import MentalHealthEntry, MentalHealthJournal, HealthScore
from sqlalchemy import func
import json

bp = Blueprint('mental_health', __name__, url_prefix='/api/mental-health')


@bp.route('/entry', methods=['POST'])
@login_required
def log_mental_health_entry():
    """Log a new mental health entry"""
    try:
        data = request.get_json()
        
        # Create mental health entry
        entry = MentalHealthEntry(
            user_id=current_user.id,
            mood_score=data.get('mood_score', 5),
            stress_level=data.get('stress_level', 5),
            sleep_quality=data.get('sleep_quality'),
            energy_level=data.get('energy_level'),
            has_anxiety=data.get('has_anxiety', False),
            has_insomnia=data.get('has_insomnia', False),
            has_fatigue=data.get('has_fatigue', False),
            has_mood_swings=data.get('has_mood_swings', False),
            has_irritability=data.get('has_irritability', False),
            has_concentration_issues=data.get('has_concentration_issues', False),
            notes=data.get('notes', ''),
            entry_date=datetime.utcnow().date()
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Update mental health score
        update_mental_health_score(current_user.id)
        
        return jsonify({
            'success': True,
            'message': 'Mental health entry logged successfully',
            'entry': entry.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/entries', methods=['GET'])
@login_required
def get_mental_health_entries():
    """Get mental health entries for current user"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        entries = MentalHealthEntry.query.filter(
            MentalHealthEntry.user_id == current_user.id,
            MentalHealthEntry.entry_date >= start_date
        ).order_by(MentalHealthEntry.entry_date.desc()).all()
        
        return jsonify({
            'success': True,
            'entries': [entry.to_dict() for entry in entries],
            'count': len(entries)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/statistics', methods=['GET'])
@login_required
def get_mental_health_statistics():
    """Get mental health statistics for current user"""
    try:
        days = request.args.get('days', 7, type=int)
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        # Get entries for the period
        entries = MentalHealthEntry.query.filter(
            MentalHealthEntry.user_id == current_user.id,
            MentalHealthEntry.entry_date >= start_date
        ).all()
        
        if not entries:
            return jsonify({
                'success': True,
                'statistics': {
                    'entries_logged': 0,
                    'avg_mood': 0,
                    'avg_stress': 0,
                    'avg_sleep': 0,
                    'mental_score': 0,
                    'trend': 'stable'
                }
            }), 200
        
        # Calculate statistics
        avg_mood = sum(e.mood_score for e in entries) / len(entries)
        avg_stress = sum(e.stress_level for e in entries) / len(entries)
        sleep_entries = [e.sleep_quality for e in entries if e.sleep_quality]
        avg_sleep = sum(sleep_entries) / len(sleep_entries) if sleep_entries else 0
        
        # Calculate mental health score (0-100)
        # Higher mood and sleep = better, lower stress = better
        mental_score = ((avg_mood / 10) * 40 + 
                       ((10 - avg_stress) / 10) * 40 + 
                       (avg_sleep / 10) * 20) * 100
        mental_score = round(mental_score)
        
        # Determine trend
        if len(entries) >= 3:
            recent_score = (entries[0].mood_score + (10 - entries[0].stress_level)) / 2
            older_score = (entries[-1].mood_score + (10 - entries[-1].stress_level)) / 2
            if recent_score > older_score + 0.5:
                trend = 'improving'
            elif recent_score < older_score - 0.5:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        # Count common symptoms
        symptom_counts = {
            'anxiety': sum(1 for e in entries if e.has_anxiety),
            'insomnia': sum(1 for e in entries if e.has_insomnia),
            'fatigue': sum(1 for e in entries if e.has_fatigue),
            'mood_swings': sum(1 for e in entries if e.has_mood_swings),
            'irritability': sum(1 for e in entries if e.has_irritability),
            'concentration_issues': sum(1 for e in entries if e.has_concentration_issues)
        }
        
        return jsonify({
            'success': True,
            'statistics': {
                'entries_logged': len(entries),
                'avg_mood': round(avg_mood, 1),
                'avg_stress': round(avg_stress, 1),
                'avg_sleep': round(avg_sleep, 1) if avg_sleep > 0 else None,
                'mental_score': mental_score,
                'trend': trend,
                'symptom_counts': symptom_counts
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/journal', methods=['POST'])
@login_required
def create_journal_entry():
    """Create a new journal entry"""
    try:
        data = request.get_json()
        
        journal = MentalHealthJournal(
            user_id=current_user.id,
            reflection=data.get('reflection', ''),
            gratitude=data.get('gratitude', ''),
            challenges=data.get('challenges', ''),
            entry_date=datetime.utcnow().date()
        )
        
        db.session.add(journal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Journal entry saved successfully',
            'journal': journal.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/journals', methods=['GET'])
@login_required
def get_journal_entries():
    """Get journal entries for current user"""
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        journals = MentalHealthJournal.query.filter(
            MentalHealthJournal.user_id == current_user.id,
            MentalHealthJournal.entry_date >= start_date
        ).order_by(MentalHealthJournal.entry_date.desc()).all()
        
        return jsonify({
            'success': True,
            'journals': [journal.to_dict() for journal in journals],
            'count': len(journals)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/ai-advice', methods=['POST'])
@login_required
def get_ai_advice():
    """Get AI-powered mental health advice based on recent entries"""
    try:
        # Get recent entries (last 7 days)
        start_date = datetime.utcnow().date() - timedelta(days=7)
        entries = MentalHealthEntry.query.filter(
            MentalHealthEntry.user_id == current_user.id,
            MentalHealthEntry.entry_date >= start_date
        ).all()
        
        if not entries:
            advice = {
                'message': "Start tracking your mood daily to receive personalized mental health insights and recommendations.",
                'tips': [
                    "Log your mood and stress levels regularly",
                    "Practice mindfulness for 10 minutes daily",
                    "Maintain a consistent sleep schedule"
                ]
            }
        else:
            # Calculate averages
            avg_mood = sum(e.mood_score for e in entries) / len(entries)
            avg_stress = sum(e.stress_level for e in entries) / len(entries)
            
            # Generate advice based on patterns
            tips = []
            
            if avg_mood < 5:
                tips.append("Your mood has been low. Consider talking to a mental health professional.")
                tips.append("Try engaging in activities you enjoy and connecting with loved ones.")
            elif avg_mood < 7:
                tips.append("Your mood is moderate. Focus on self-care and stress management.")
            else:
                tips.append("Your mood is good! Keep up your current wellness practices.")
            
            if avg_stress > 7:
                tips.append("High stress detected. Practice deep breathing exercises and meditation.")
                tips.append("Consider taking short breaks throughout the day.")
            elif avg_stress > 5:
                tips.append("Moderate stress levels. Try progressive muscle relaxation.")
            
            # Check for common symptoms
            if any(e.has_anxiety for e in entries):
                tips.append("Anxiety noticed. Try the 4-7-8 breathing technique: inhale 4s, hold 7s, exhale 8s.")
            
            if any(e.has_insomnia for e in entries):
                tips.append("Sleep issues detected. Maintain a bedtime routine and avoid screens before bed.")
            
            if any(e.has_fatigue for e in entries):
                tips.append("Fatigue present. Ensure adequate sleep, nutrition, and light exercise.")
            
            message = f"Based on your recent entries, your average mood is {avg_mood:.1f}/10 and stress level is {avg_stress:.1f}/10."
            
            advice = {
                'message': message,
                'tips': tips[:4]  # Limit to top 4 tips
            }
        
        return jsonify({
            'success': True,
            'advice': advice
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def update_mental_health_score(user_id):
    """Update the mental health score in HealthScore table"""
    try:
        # Get entries from last 7 days
        start_date = datetime.utcnow().date() - timedelta(days=7)
        entries = MentalHealthEntry.query.filter(
            MentalHealthEntry.user_id == user_id,
            MentalHealthEntry.entry_date >= start_date
        ).all()
        
        if entries:
            # Calculate mental health score
            avg_mood = sum(e.mood_score for e in entries) / len(entries)
            avg_stress = sum(e.stress_level for e in entries) / len(entries)
            
            mental_score = ((avg_mood / 10) * 50 + 
                           ((10 - avg_stress) / 10) * 50) * 100
            mental_score = round(mental_score)
            
            # Update or create health score entry
            health_score = HealthScore.query.filter_by(
                patient_id=user_id
            ).order_by(HealthScore.calculated_at.desc()).first()
            
            if health_score and health_score.calculated_at.date() == datetime.utcnow().date():
                # Update existing entry for today
                health_score.mental_health_score = mental_score
            else:
                # Create new entry
                health_score = HealthScore(
                    patient_id=user_id,
                    score=mental_score,  # You might want to calculate overall score differently
                    mental_health_score=mental_score,
                    trend='stable'
                )
                db.session.add(health_score)
            
            db.session.commit()
            
    except Exception as e:
        print(f"Error updating mental health score: {e}")
        db.session.rollback()
