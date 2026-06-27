"""
Module 9: Patient Results & Medical Report Management
- Prediction history storage
- PDF report generation
- Doctor remarks section
"""

from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from database.models import MedicalReport, User, HealthPrediction, VitalSign, HealthScore
from datetime import datetime, timedelta
import json
import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO

bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@bp.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate medical report"""
    data = request.get_json()
    
    patient_id = data.get('patient_id', current_user.id)
    report_type = data.get('report_type', 'health_summary')
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get patient
    patient = User.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Generate report based on type
    if report_type == 'health_summary':
        content = generate_health_summary(patient)
    elif report_type == 'risk_assessment':
        content = generate_risk_assessment(patient)
    elif report_type == 'vitals_report':
        content = generate_vitals_report(patient)
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    # Create report record
    report = MedicalReport(
        patient_id=patient_id,
        report_type=report_type,
        title=data.get('title', f'{report_type.replace("_", " ").title()} - {datetime.utcnow().strftime("%Y-%m-%d")}'),
        content=json.dumps(content),
        generated_by=current_user.id
    )
    
    db.session.add(report)
    db.session.commit()
    
    # Generate PDF
    pdf_path = generate_pdf_report(report, patient, content)
    report.file_path = pdf_path
    db.session.commit()
    
    return jsonify({
        'message': 'Report generated successfully',
        'report': report.to_dict()
    }), 201


@bp.route('/list', methods=['GET'])
@login_required
def get_reports():
    """Get medical reports list"""
    patient_id = request.args.get('patient_id', current_user.id, type=int)
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    reports = MedicalReport.query.filter_by(patient_id=patient_id).order_by(
        MedicalReport.generated_at.desc()
    ).all()
    
    return jsonify({
        'reports': [r.to_dict() for r in reports]
    }), 200


@bp.route('/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    """Get report details"""
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and report.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({'report': report.to_dict()}), 200


@bp.route('/<int:report_id>/download', methods=['GET'])
@login_required
def download_report(report_id):
    """Download PDF report"""
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin', 'doctor'] and report.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not report.file_path or not os.path.exists(report.file_path):
        return jsonify({'error': 'Report file not found'}), 404
    
    return send_file(
        report.file_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'medical_report_{report.id}.pdf'
    )


@bp.route('/<int:report_id>/remarks', methods=['POST'])
def add_remarks(report_id):
    """Add doctor remarks to report"""
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    data = request.get_json()
    remarks = data.get('remarks', '').strip()
    
    if not remarks:
        return jsonify({'error': 'Remarks cannot be empty'}), 400
    
    report.doctor_remarks = remarks
    db.session.commit()
    
    return jsonify({
        'message': 'Remarks added successfully',
        'report': report.to_dict()
    }), 200


@bp.route('/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """Delete report"""
    report = MedicalReport.query.get(report_id)
    
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    
    # Check permission
    if current_user.role not in ['admin'] and report.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Delete PDF file
    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)
    
    db.session.delete(report)
    db.session.commit()
    
    return jsonify({'message': 'Report deleted successfully'}), 200


def generate_health_summary(patient):
    """Generate comprehensive health summary"""
    # Get latest vital signs
    latest_vital = VitalSign.query.filter_by(patient_id=patient.id).order_by(
        VitalSign.recorded_at.desc()
    ).first()
    
    # Get latest health score
    latest_score = HealthScore.query.filter_by(patient_id=patient.id).order_by(
        HealthScore.calculated_at.desc()
    ).first()
    
    # Get latest prediction
    latest_prediction = HealthPrediction.query.filter_by(patient_id=patient.id).order_by(
        HealthPrediction.predicted_at.desc()
    ).first()
    
    # Get vital statistics for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    vitals = VitalSign.query.filter(
        VitalSign.patient_id == patient.id,
        VitalSign.recorded_at >= thirty_days_ago
    ).all()
    
    content = {
        'patient_info': {
            'name': patient.full_name,
            'age': calculate_age(patient.date_of_birth) if patient.date_of_birth else 'N/A',
            'gender': patient.gender or 'N/A',
            'email': patient.email
        },
        'current_vitals': latest_vital.to_dict() if latest_vital else None,
        'health_score': latest_score.to_dict() if latest_score else None,
        'risk_assessment': latest_prediction.to_dict() if latest_prediction else None,
        'vital_statistics': calculate_vital_statistics(vitals),
        'generated_date': datetime.utcnow().isoformat()
    }
    
    return content


def generate_risk_assessment(patient):
    """Generate risk assessment report"""
    # Get last 10 predictions
    predictions = HealthPrediction.query.filter_by(patient_id=patient.id).order_by(
        HealthPrediction.predicted_at.desc()
    ).limit(10).all()
    
    content = {
        'patient_info': {
            'name': patient.full_name,
            'age': calculate_age(patient.date_of_birth) if patient.date_of_birth else 'N/A',
        },
        'prediction_history': [p.to_dict() for p in predictions],
        'risk_trend': analyze_risk_trend(predictions),
        'generated_date': datetime.utcnow().isoformat()
    }
    
    return content


def generate_vitals_report(patient):
    """Generate vitals monitoring report"""
    # Get vitals for last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    vitals = VitalSign.query.filter(
        VitalSign.patient_id == patient.id,
        VitalSign.recorded_at >= thirty_days_ago
    ).order_by(VitalSign.recorded_at.desc()).all()
    
    content = {
        'patient_info': {
            'name': patient.full_name,
            'age': calculate_age(patient.date_of_birth) if patient.date_of_birth else 'N/A',
        },
        'vitals_data': [v.to_dict() for v in vitals],
        'statistics': calculate_vital_statistics(vitals),
        'period': '30 days',
        'generated_date': datetime.utcnow().isoformat()
    }
    
    return content


def generate_pdf_report(report, patient, content):
    """Generate PDF file for report"""
    # Create reports directory if not exists
    reports_dir = 'reports'
    os.makedirs(reports_dir, exist_ok=True)
    
    filename = f'report_{report.id}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.pdf'
    filepath = os.path.join(reports_dir, filename)
    
    # Create PDF
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1976D2'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(report.title, title_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Patient info table
    patient_data = [
        ['Patient Name:', patient.full_name],
        ['Patient ID:', str(patient.id)],
        ['Date of Birth:', patient.date_of_birth.strftime('%Y-%m-%d') if patient.date_of_birth else 'N/A'],
        ['Gender:', patient.gender or 'N/A'],
        ['Report Type:', report.report_type.replace('_', ' ').title()],
        ['Generated Date:', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    story.append(patient_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Add content based on report type
    if report.report_type == 'health_summary':
        add_health_summary_content(story, content, styles)
    elif report.report_type == 'risk_assessment':
        add_risk_assessment_content(story, content, styles)
    elif report.report_type == 'vitals_report':
        add_vitals_report_content(story, content, styles)
    
    # Add doctor remarks if available
    if report.doctor_remarks:
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph('<b>Doctor\'s Remarks:</b>', styles['Heading2']))
        story.append(Paragraph(report.doctor_remarks, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    return filepath


def add_health_summary_content(story, content, styles):
    """Add health summary content to PDF"""
    # Current Vitals
    if content.get('current_vitals'):
        story.append(Paragraph('<b>Current Vital Signs</b>', styles['Heading2']))
        vitals = content['current_vitals']
        vitals_data = [
            ['Heart Rate:', f"{vitals.get('heart_rate', 'N/A')} bpm"],
            ['Blood Pressure:', f"{vitals.get('blood_pressure_systolic', 'N/A')}/{vitals.get('blood_pressure_diastolic', 'N/A')} mmHg"],
            ['Oxygen Level:', f"{vitals.get('oxygen_level', 'N/A')}%"],
            ['Temperature:', f"{vitals.get('temperature', 'N/A')}°C"]
        ]
        table = Table(vitals_data, colWidths=[2*inch, 3*inch])
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))
    
    # Health Score
    if content.get('health_score'):
        story.append(Paragraph('<b>Health Score</b>', styles['Heading2']))
        score = content['health_score']
        story.append(Paragraph(f"Overall Score: {score.get('score', 'N/A')}/100", styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))


def add_risk_assessment_content(story, content, styles):
    """Add risk assessment content to PDF"""
    if content.get('prediction_history'):
        story.append(Paragraph('<b>Risk Assessment History</b>', styles['Heading2']))
        latest = content['prediction_history'][0]
        story.append(Paragraph(f"Latest Risk Level: {latest.get('risk_level', 'N/A').upper()}", styles['Normal']))
        story.append(Paragraph(f"Risk Probability: {latest.get('risk_probability', 0)*100:.1f}%", styles['Normal']))


def add_vitals_report_content(story, content, styles):
    """Add vitals report content to PDF"""
    if content.get('statistics'):
        story.append(Paragraph('<b>Vital Signs Statistics (30 Days)</b>', styles['Heading2']))
        stats = content['statistics']
        
        for vital_name, stat in stats.items():
            if stat:
                story.append(Paragraph(f"{vital_name.replace('_', ' ').title()}:", styles['Heading3']))
                story.append(Paragraph(f"Average: {stat.get('average', 'N/A')}", styles['Normal']))


def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    today = datetime.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def calculate_vital_statistics(vitals):
    """Calculate statistics from vital signs"""
    if not vitals:
        return None
    
    stats = {}
    
    # Heart rate
    hr_values = [v.heart_rate for v in vitals if v.heart_rate]
    if hr_values:
        stats['heart_rate'] = {
            'average': round(sum(hr_values) / len(hr_values), 2),
            'min': min(hr_values),
            'max': max(hr_values)
        }
    
    # Blood pressure
    bp_sys = [v.blood_pressure_systolic for v in vitals if v.blood_pressure_systolic]
    if bp_sys:
        stats['blood_pressure_systolic'] = {
            'average': round(sum(bp_sys) / len(bp_sys), 2),
            'min': min(bp_sys),
            'max': max(bp_sys)
        }
    
    return stats


def analyze_risk_trend(predictions):
    """Analyze risk trend from predictions"""
    if len(predictions) < 2:
        return 'insufficient_data'
    
    recent_avg = sum(p.risk_probability for p in predictions[:3]) / min(3, len(predictions))
    older_avg = sum(p.risk_probability for p in predictions[3:6]) / max(1, len(predictions[3:6]))
    
    if recent_avg < older_avg - 0.1:
        return 'improving'
    elif recent_avg > older_avg + 0.1:
        return 'worsening'
    else:
        return 'stable'
