"""
Report Service
Generate health reports and analytics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from database.models import User, VitalSign, HealthScore, HealthPrediction, MedicalReport, db


class ReportService:
    """Service for generating health reports"""
    
    @staticmethod
    def generate_patient_report(user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive patient health report
        
        Args:
            user_id: User ID
            days: Number of days to include in report
            
        Returns:
            Dictionary containing report data
        """
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get vital signs
        vital_signs = VitalSign.query.filter(
            VitalSign.user_id == user_id,
            VitalSign.timestamp >= since_date
        ).order_by(VitalSign.timestamp.desc()).all()
        
        # Get health scores
        health_scores = HealthScore.query.filter(
            HealthScore.user_id == user_id,
            HealthScore.calculated_at >= since_date
        ).order_by(HealthScore.calculated_at.desc()).all()
        
        # Get predictions
        predictions = HealthPrediction.query.filter(
            HealthPrediction.user_id == user_id,
            HealthPrediction.created_at >= since_date
        ).order_by(HealthPrediction.created_at.desc()).all()
        
        report = {
            'patient_info': user.to_dict(),
            'report_period': {
                'start': since_date.isoformat(),
                'end': datetime.utcnow().isoformat(),
                'days': days
            },
            'vital_signs_summary': ReportService._summarize_vitals(vital_signs),
            'health_scores': [hs.to_dict() for hs in health_scores],
            'predictions': [p.to_dict() for p in predictions],
            'vital_signs_count': len(vital_signs),
            'latest_vital_signs': vital_signs[0].to_dict() if vital_signs else None,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return report
    
    @staticmethod
    def _summarize_vitals(vital_signs: List[VitalSign]) -> Dict[str, Any]:
        """Summarize vital signs data"""
        if not vital_signs:
            return {}
        
        summary = {
            'heart_rate': {'values': [], 'avg': 0, 'min': 0, 'max': 0},
            'blood_pressure_systolic': {'values': [], 'avg': 0, 'min': 0, 'max': 0},
            'blood_pressure_diastolic': {'values': [], 'avg': 0, 'min': 0, 'max': 0},
            'temperature': {'values': [], 'avg': 0, 'min': 0, 'max': 0},
            'oxygen_saturation': {'values': [], 'avg': 0, 'min': 0, 'max': 0}
        }
        
        # Collect values
        for vs in vital_signs:
            if vs.heart_rate:
                summary['heart_rate']['values'].append(vs.heart_rate)
            if vs.blood_pressure_systolic:
                summary['blood_pressure_systolic']['values'].append(vs.blood_pressure_systolic)
            if vs.blood_pressure_diastolic:
                summary['blood_pressure_diastolic']['values'].append(vs.blood_pressure_diastolic)
            if vs.temperature:
                summary['temperature']['values'].append(vs.temperature)
            if vs.oxygen_saturation:
                summary['oxygen_saturation']['values'].append(vs.oxygen_saturation)
        
        # Calculate statistics
        for key in summary:
            if summary[key]['values']:
                summary[key]['avg'] = sum(summary[key]['values']) / len(summary[key]['values'])
                summary[key]['min'] = min(summary[key]['values'])
                summary[key]['max'] = max(summary[key]['values'])
                summary[key]['count'] = len(summary[key]['values'])
        
        return summary
    
    @staticmethod
    def create_medical_report(patient_id: int, doctor_id: int, report_type: str, 
                            title: str, content: str, file_path: str = None) -> MedicalReport:
        """
        Create a medical report
        
        Args:
            patient_id: Patient user ID
            doctor_id: Doctor user ID
            report_type: Type of report
            title: Report title
            content: Report content
            file_path: Optional file path
            
        Returns:
            Created MedicalReport object
        """
        report = MedicalReport(
            patient_id=patient_id,
            doctor_id=doctor_id,
            report_type=report_type,
            title=title,
            content=content,
            file_path=file_path,
            created_at=datetime.utcnow()
        )
        
        db.session.add(report)
        db.session.commit()
        
        return report
    
    @staticmethod
    def get_patient_reports(patient_id: int) -> List[MedicalReport]:
        """
        Get all reports for a patient
        
        Args:
            patient_id: Patient user ID
            
        Returns:
            List of MedicalReport objects
        """
        return MedicalReport.query.filter_by(patient_id=patient_id)\
            .order_by(MedicalReport.created_at.desc()).all()
    
    @staticmethod
    def export_report_to_file(report_data: Dict, filename: str = None) -> str:
        """
        Export report data to a file
        
        Args:
            report_data: Report data dictionary
            filename: Optional filename
            
        Returns:
            File path of the exported report
        """
        if not filename:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"health_report_{timestamp}.txt"
        
        reports_dir = 'reports'
        os.makedirs(reports_dir, exist_ok=True)
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("HEALTH REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            if 'patient_info' in report_data:
                f.write("Patient Information:\n")
                f.write(f"  Name: {report_data['patient_info'].get('full_name', 'N/A')}\n")
                f.write(f"  Email: {report_data['patient_info'].get('email', 'N/A')}\n\n")
            
            if 'report_period' in report_data:
                f.write("Report Period:\n")
                f.write(f"  {report_data['report_period']['days']} days\n")
                f.write(f"  From: {report_data['report_period']['start']}\n")
                f.write(f"  To: {report_data['report_period']['end']}\n\n")
            
            if 'vital_signs_summary' in report_data:
                f.write("Vital Signs Summary:\n")
                for key, value in report_data['vital_signs_summary'].items():
                    if value.get('count', 0) > 0:
                        f.write(f"  {key.replace('_', ' ').title()}:\n")
                        f.write(f"    Average: {value['avg']:.2f}\n")
                        f.write(f"    Min: {value['min']:.2f}\n")
                        f.write(f"    Max: {value['max']:.2f}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Generated: {report_data.get('generated_at', datetime.utcnow().isoformat())}\n")
        
        return filepath
