"""
Recommendation Service
Provides health recommendations based on patient data
"""

from typing import Dict, List, Any
from database.models import User, VitalSign, HealthScore, HealthPrediction


class RecommendationService:
    """Service for generating health recommendations"""
    
    @staticmethod
    def get_vital_recommendations(vital_sign: VitalSign) -> List[str]:
        """
        Generate recommendations based on vital signs
        
        Args:
            vital_sign: VitalSign object
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Heart rate recommendations
        if vital_sign.heart_rate:
            if vital_sign.heart_rate > 100:
                recommendations.append("Your heart rate is elevated. Consider relaxation techniques and avoid caffeine.")
            elif vital_sign.heart_rate < 60:
                recommendations.append("Your heart rate is low. If you're not an athlete, consult your doctor.")
        
        # Blood pressure recommendations
        if vital_sign.blood_pressure_systolic and vital_sign.blood_pressure_diastolic:
            if vital_sign.blood_pressure_systolic > 120 or vital_sign.blood_pressure_diastolic > 80:
                recommendations.append("Your blood pressure is elevated. Reduce sodium intake, exercise regularly, and manage stress.")
                if vital_sign.blood_pressure_systolic > 140 or vital_sign.blood_pressure_diastolic > 90:
                    recommendations.append("⚠️ Your blood pressure is high. Please consult your healthcare provider.")
        
        # Temperature recommendations
        if vital_sign.temperature:
            if vital_sign.temperature > 37.5:
                recommendations.append("You have a fever. Rest, stay hydrated, and monitor your temperature.")
            elif vital_sign.temperature < 36:
                recommendations.append("Your body temperature is low. Warm up and seek medical attention if it persists.")
        
        # Oxygen saturation recommendations
        if vital_sign.oxygen_saturation:
            if vital_sign.oxygen_saturation < 95:
                recommendations.append("Your oxygen saturation is below normal. Seek immediate medical attention.")
        
        # Glucose level recommendations
        if vital_sign.glucose_level:
            if vital_sign.glucose_level > 126:
                recommendations.append("Your glucose level is high. Follow your diabetes management plan and consult your doctor.")
            elif vital_sign.glucose_level < 70:
                recommendations.append("Your glucose level is low. Consume fast-acting carbohydrates immediately.")
        
        # Weight recommendations
        if vital_sign.weight:
            # This would require BMI calculation with height
            pass
        
        if not recommendations:
            recommendations.append("Your vital signs are within normal ranges. Keep up the good work!")
        
        return recommendations
    
    @staticmethod
    def get_health_score_recommendations(health_score: HealthScore) -> List[str]:
        """
        Generate recommendations based on health score
        
        Args:
            health_score: HealthScore object
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Overall score recommendations
        if health_score.overall_score >= 80:
            recommendations.append("Excellent health! Continue your current healthy lifestyle.")
        elif health_score.overall_score >= 60:
            recommendations.append("Good health overall. Focus on areas that need improvement.")
        elif health_score.overall_score >= 40:
            recommendations.append("Your health needs attention. Consider lifestyle modifications.")
        else:
            recommendations.append("⚠️ Your health score is concerning. Please consult healthcare professionals.")
        
        # Cardiovascular recommendations
        if health_score.cardiovascular_score and health_score.cardiovascular_score < 60:
            recommendations.append("Cardiovascular Health: Increase aerobic exercise (30 min/day), reduce saturated fats.")
        
        # Metabolic recommendations
        if health_score.metabolic_score and health_score.metabolic_score < 60:
            recommendations.append("Metabolic Health: Balance your diet, maintain healthy weight, monitor blood sugar.")
        
        # Respiratory recommendations
        if health_score.respiratory_score and health_score.respiratory_score < 60:
            recommendations.append("Respiratory Health: Practice breathing exercises, avoid pollutants, stay active.")
        
        # Mental health recommendations
        if health_score.mental_health_score and health_score.mental_health_score < 60:
            recommendations.append("Mental Health: Practice stress management, ensure adequate sleep, consider counseling.")
        
        return recommendations
    
    @staticmethod
    def get_lifestyle_recommendations(user: User) -> Dict[str, List[str]]:
        """
        Generate comprehensive lifestyle recommendations
        
        Args:
            user: User object
            
        Returns:
            Dictionary categorizing recommendations
        """
        recommendations = {
            'nutrition': [
                "Eat a balanced diet with plenty of fruits and vegetables",
                "Limit processed foods and added sugars",
                "Stay hydrated - drink 8 glasses of water daily",
                "Include lean proteins in every meal"
            ],
            'exercise': [
                "Aim for 150 minutes of moderate exercise per week",
                "Include both cardio and strength training",
                "Take breaks from sitting every hour",
                "Consider activities you enjoy to stay motivated"
            ],
            'sleep': [
                "Maintain 7-9 hours of sleep per night",
                "Keep a consistent sleep schedule",
                "Create a relaxing bedtime routine",
                "Limit screen time before bed"
            ],
            'stress_management': [
                "Practice mindfulness or meditation daily",
                "Take regular breaks throughout the day",
                "Connect with friends and family",
                "Engage in hobbies you enjoy"
            ],
            'preventive_care': [
                "Schedule regular check-ups with your doctor",
                "Stay up to date with vaccinations",
                "Monitor your vital signs regularly",
                "Keep track of your family medical history"
            ]
        }
        
        return recommendations
    
    @staticmethod
    def get_prediction_recommendations(prediction: HealthPrediction) -> List[str]:
        """
        Generate recommendations based on health prediction
        
        Args:
            prediction: HealthPrediction object
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if prediction.risk_level == 'high':
            recommendations.append("⚠️ High risk detected. Schedule an appointment with your healthcare provider immediately.")
            recommendations.append("Follow all prescribed medications and treatment plans.")
        elif prediction.risk_level == 'medium':
            recommendations.append("Moderate risk identified. Increase monitoring and take preventive measures.")
            recommendations.append("Discuss this with your doctor at your next appointment.")
        else:
            recommendations.append("Low risk. Continue healthy habits and regular monitoring.")
        
        # Add specific recommendations based on prediction type
        if prediction.prediction_type == 'diabetes':
            recommendations.extend([
                "Monitor blood glucose levels regularly",
                "Follow a low-glycemic diet",
                "Maintain a healthy weight through diet and exercise"
            ])
        elif prediction.prediction_type == 'heart_disease':
            recommendations.extend([
                "Monitor blood pressure and heart rate",
                "Follow a heart-healthy diet low in saturated fats",
                "Engage in regular cardiovascular exercise"
            ])
        elif prediction.prediction_type == 'hypertension':
            recommendations.extend([
                "Reduce sodium intake to less than 2,300mg per day",
                "Manage stress through relaxation techniques",
                "Maintain a healthy weight"
            ])
        
        return recommendations
    
    @staticmethod
    def get_personalized_recommendations(user_id: int) -> Dict[str, Any]:
        """
        Generate personalized recommendations based on all user data
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with categorized recommendations
        """
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}
        
        # Get latest data
        latest_vital = VitalSign.query.filter_by(user_id=user_id)\
            .order_by(VitalSign.timestamp.desc()).first()
        
        latest_score = HealthScore.query.filter_by(user_id=user_id)\
            .order_by(HealthScore.calculated_at.desc()).first()
        
        recent_predictions = HealthPrediction.query.filter_by(user_id=user_id)\
            .order_by(HealthPrediction.created_at.desc()).limit(3).all()
        
        # Compile recommendations
        all_recommendations = {
            'vital_signs': [],
            'health_score': [],
            'predictions': [],
            'lifestyle': RecommendationService.get_lifestyle_recommendations(user),
            'priority': []
        }
        
        if latest_vital:
            all_recommendations['vital_signs'] = \
                RecommendationService.get_vital_recommendations(latest_vital)
        
        if latest_score:
            all_recommendations['health_score'] = \
                RecommendationService.get_health_score_recommendations(latest_score)
        
        for prediction in recent_predictions:
            all_recommendations['predictions'].extend(
                RecommendationService.get_prediction_recommendations(prediction)
            )
        
        # Identify priority recommendations (those with warning symbols)
        for category in ['vital_signs', 'health_score', 'predictions']:
            for rec in all_recommendations[category]:
                if '⚠️' in rec:
                    all_recommendations['priority'].append(rec)
        
        return all_recommendations
