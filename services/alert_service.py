"""
Alert Service
Manages health alerts and notifications
"""

from datetime import datetime
from typing import List, Dict, Any
from database.models import Alert, User, VitalSign, db


class AlertService:
    """Service for managing health alerts"""
    
    @staticmethod
    def create_alert(user_id: int, alert_type: str, severity: str, message: str) -> Alert:
        """
        Create a new alert
        
        Args:
            user_id: User ID
            alert_type: Type of alert (vital, appointment, medication, etc.)
            severity: Severity level (low, medium, high, critical)
            message: Alert message
            
        Returns:
            Created alert object
        """
        alert = Alert(
            user_id=user_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            created_at=datetime.utcnow()
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return alert
    
    @staticmethod
    def check_vital_signs(vital_sign: VitalSign) -> List[Alert]:
        """
        Check vital signs and create alerts if needed
        
        Args:
            vital_sign: VitalSign object to check
            
        Returns:
            List of created alerts
        """
        alerts = []
        
        # Heart rate check
        if vital_sign.heart_rate:
            if vital_sign.heart_rate > 120:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_heart_rate',
                    severity='high',
                    message=f'High heart rate detected: {vital_sign.heart_rate} bpm'
                )
                alerts.append(alert)
            elif vital_sign.heart_rate < 40:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_heart_rate',
                    severity='high',
                    message=f'Low heart rate detected: {vital_sign.heart_rate} bpm'
                )
                alerts.append(alert)
        
        # Blood pressure check
        if vital_sign.blood_pressure_systolic and vital_sign.blood_pressure_diastolic:
            if vital_sign.blood_pressure_systolic > 180 or vital_sign.blood_pressure_diastolic > 120:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_blood_pressure',
                    severity='critical',
                    message=f'Critical blood pressure: {vital_sign.blood_pressure_systolic}/{vital_sign.blood_pressure_diastolic} mmHg'
                )
                alerts.append(alert)
            elif vital_sign.blood_pressure_systolic > 140 or vital_sign.blood_pressure_diastolic > 90:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_blood_pressure',
                    severity='medium',
                    message=f'Elevated blood pressure: {vital_sign.blood_pressure_systolic}/{vital_sign.blood_pressure_diastolic} mmHg'
                )
                alerts.append(alert)
        
        # Oxygen saturation check
        if vital_sign.oxygen_saturation:
            if vital_sign.oxygen_saturation < 90:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_oxygen',
                    severity='critical',
                    message=f'Low oxygen saturation: {vital_sign.oxygen_saturation}%'
                )
                alerts.append(alert)
        
        # Temperature check
        if vital_sign.temperature:
            if vital_sign.temperature > 38.5:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_temperature',
                    severity='medium',
                    message=f'High temperature detected: {vital_sign.temperature}°C'
                )
                alerts.append(alert)
            elif vital_sign.temperature < 35:
                alert = AlertService.create_alert(
                    user_id=vital_sign.user_id,
                    alert_type='vital_temperature',
                    severity='high',
                    message=f'Low temperature detected: {vital_sign.temperature}°C'
                )
                alerts.append(alert)
        
        return alerts
    
    @staticmethod
    def get_user_alerts(user_id: int, unread_only: bool = False) -> List[Alert]:
        """
        Get alerts for a user
        
        Args:
            user_id: User ID
            unread_only: If True, return only unread alerts
            
        Returns:
            List of alerts
        """
        query = Alert.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        return query.order_by(Alert.created_at.desc()).all()
    
    @staticmethod
    def mark_alert_read(alert_id: int) -> bool:
        """
        Mark an alert as read
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if successful, False otherwise
        """
        alert = Alert.query.get(alert_id)
        if alert:
            alert.is_read = True
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def mark_all_read(user_id: int) -> int:
        """
        Mark all alerts as read for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of alerts marked as read
        """
        count = Alert.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return count
    
    @staticmethod
    def delete_alert(alert_id: int) -> bool:
        """
        Delete an alert
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if successful, False otherwise
        """
        alert = Alert.query.get(alert_id)
        if alert:
            db.session.delete(alert)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_alert_statistics(user_id: int) -> Dict[str, Any]:
        """
        Get alert statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with alert statistics
        """
        all_alerts = Alert.query.filter_by(user_id=user_id).all()
        unread_alerts = [a for a in all_alerts if not a.is_read]
        
        severity_count = {}
        type_count = {}
        
        for alert in all_alerts:
            severity_count[alert.severity] = severity_count.get(alert.severity, 0) + 1
            type_count[alert.alert_type] = type_count.get(alert.alert_type, 0) + 1
        
        return {
            'total_alerts': len(all_alerts),
            'unread_alerts': len(unread_alerts),
            'by_severity': severity_count,
            'by_type': type_count
        }
