"""
AI/ML Model for Health Risk Prediction
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
try:
    from sklearn.exceptions import InconsistentVersionWarning
except Exception:
    InconsistentVersionWarning = Warning
import joblib
import os
import json
import warnings
from datetime import datetime

class HealthRiskPredictor:
    """Health risk prediction model"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_version = "1.0.0"
        self.model_path = "app/ml/models"
        self.feature_names = [
            'age', 'bmi', 'heart_rate', 'blood_pressure_systolic',
            'blood_pressure_diastolic', 'oxygen_level', 'cholesterol', 'glucose'
        ]
        
        # Create models directory if not exists
        os.makedirs(self.model_path, exist_ok=True)
        
        # Load model if exists, otherwise create new
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        model_file = os.path.join(self.model_path, 'risk_predictor.pkl')
        scaler_file = os.path.join(self.model_path, 'scaler.pkl')
        
        if os.path.exists(model_file) and os.path.exists(scaler_file):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", InconsistentVersionWarning)
                    self.model = joblib.load(model_file)
                    self.scaler = joblib.load(scaler_file)
                print("Loaded existing model")
            except InconsistentVersionWarning as e:
                print(f"Model version mismatch detected: {e}. Retraining model.")
                self._create_and_train_model()
            except Exception as e:
                print(f"Error loading model: {e}. Creating new model.")
                self._create_and_train_model()
        else:
            self._create_and_train_model()
    
    def _create_and_train_model(self):
        """Create and train a new model with synthetic data"""
        print("Creating and training new model...")
        
        # Generate synthetic training data
        X, y = self._generate_synthetic_data(n_samples=1000)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model trained with accuracy: {accuracy:.2f}")
        
        # Save model
        self._save_model()
    
    def _generate_synthetic_data(self, n_samples=1000):
        """Generate synthetic health data for training"""
        np.random.seed(42)
        
        # Generate features
        age = np.random.randint(18, 90, n_samples)
        bmi = np.random.normal(26, 5, n_samples)
        heart_rate = np.random.normal(75, 12, n_samples)
        bp_systolic = np.random.normal(120, 15, n_samples)
        bp_diastolic = np.random.normal(80, 10, n_samples)
        oxygen_level = np.random.normal(97, 2, n_samples)
        cholesterol = np.random.normal(200, 40, n_samples)
        glucose = np.random.normal(100, 20, n_samples)
        
        X = np.column_stack([
            age, bmi, heart_rate, bp_systolic, bp_diastolic,
            oxygen_level, cholesterol, glucose
        ])
        
        # Generate risk labels based on rules
        y = np.zeros(n_samples, dtype=int)  # 0: low, 1: medium, 2: high
        
        for i in range(n_samples):
            risk_score = 0
            
            # Age factor
            if age[i] > 60:
                risk_score += 2
            elif age[i] > 45:
                risk_score += 1
            
            # BMI factor
            if bmi[i] > 30:
                risk_score += 2
            elif bmi[i] > 25:
                risk_score += 1
            
            # Blood pressure
            if bp_systolic[i] > 140 or bp_diastolic[i] > 90:
                risk_score += 2
            elif bp_systolic[i] > 130 or bp_diastolic[i] > 85:
                risk_score += 1
            
            # Heart rate
            if heart_rate[i] > 100 or heart_rate[i] < 60:
                risk_score += 1
            
            # Oxygen level
            if oxygen_level[i] < 92:
                risk_score += 2
            elif oxygen_level[i] < 95:
                risk_score += 1
            
            # Cholesterol
            if cholesterol[i] > 240:
                risk_score += 2
            elif cholesterol[i] > 200:
                risk_score += 1
            
            # Glucose
            if glucose[i] > 126:
                risk_score += 2
            elif glucose[i] > 100:
                risk_score += 1
            
            # Assign risk level
            if risk_score >= 6:
                y[i] = 2  # high
            elif risk_score >= 3:
                y[i] = 1  # medium
            else:
                y[i] = 0  # low
        
        return X, y
    
    def predict(self, features):
        """Predict health risk"""
        # Prepare features
        feature_values = [
            features.get('age', 30),
            features.get('bmi', 25),
            features.get('heart_rate', 75),
            features.get('blood_pressure_systolic', 120),
            features.get('blood_pressure_diastolic', 80),
            features.get('oxygen_level', 98),
            features.get('cholesterol', 200),
            features.get('glucose', 100)
        ]
        
        X = np.array([feature_values])
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        # Map prediction to risk level
        risk_levels = ['low', 'medium', 'high']
        risk_level = risk_levels[prediction]
        risk_probability = probabilities[prediction]
        
        # Get contributing factors
        contributing_factors = self._get_contributing_factors(features)
        
        # Get predicted conditions
        predicted_conditions = self._get_predicted_conditions(features, risk_level)
        
        result = {
            'risk_level': risk_level,
            'risk_probability': float(risk_probability),
            'predicted_conditions': predicted_conditions,
            'contributing_factors': contributing_factors,
            'model_version': self.model_version,
            'confidence_score': float(max(probabilities))
        }
        
        return result
    
    def _get_contributing_factors(self, features):
        """Identify contributing factors to risk"""
        factors = []
        
        age = features.get('age', 30)
        if age > 60:
            factors.append(f"Advanced age ({age} years)")
        
        bmi = features.get('bmi', 25)
        if bmi > 30:
            factors.append(f"High BMI ({bmi:.1f})")
        elif bmi > 25:
            factors.append(f"Elevated BMI ({bmi:.1f})")
        
        bp_sys = features.get('blood_pressure_systolic', 120)
        if bp_sys > 140:
            factors.append(f"High blood pressure ({bp_sys} mmHg)")
        elif bp_sys > 130:
            factors.append(f"Elevated blood pressure ({bp_sys} mmHg)")
        
        hr = features.get('heart_rate', 75)
        if hr > 100:
            factors.append(f"Elevated heart rate ({hr} bpm)")
        elif hr < 60:
            factors.append(f"Low heart rate ({hr} bpm)")
        
        oxygen = features.get('oxygen_level', 98)
        if oxygen < 92:
            factors.append(f"Low oxygen saturation ({oxygen}%)")
        
        cholesterol = features.get('cholesterol', 200)
        if cholesterol > 240:
            factors.append(f"High cholesterol ({cholesterol} mg/dL)")
        
        glucose = features.get('glucose', 100)
        if glucose > 126:
            factors.append(f"High blood glucose ({glucose} mg/dL)")
        
        if not factors:
            factors.append("All parameters within normal range")
        
        return factors
    
    def _get_predicted_conditions(self, features, risk_level):
        """Get predicted health conditions"""
        conditions = []
        
        bp_sys = features.get('blood_pressure_systolic', 120)
        bp_dias = features.get('blood_pressure_diastolic', 80)
        
        if bp_sys > 140 or bp_dias > 90:
            conditions.append("Hypertension risk")
        
        glucose = features.get('glucose', 100)
        if glucose > 126:
            conditions.append("Diabetes risk")
        
        cholesterol = features.get('cholesterol', 200)
        if cholesterol > 240:
            conditions.append("Cardiovascular disease risk")
        
        bmi = features.get('bmi', 25)
        if bmi > 30:
            conditions.append("Obesity-related complications")
        
        oxygen = features.get('oxygen_level', 98)
        if oxygen < 92:
            conditions.append("Respiratory issues")
        
        if not conditions:
            if risk_level == 'low':
                conditions.append("No significant health risks detected")
            else:
                conditions.append("General health monitoring recommended")
        
        return conditions
    
    def _save_model(self):
        """Save model and scaler"""
        model_file = os.path.join(self.model_path, 'risk_predictor.pkl')
        scaler_file = os.path.join(self.model_path, 'scaler.pkl')
        
        joblib.dump(self.model, model_file)
        joblib.dump(self.scaler, scaler_file)
        
        print(f"Model saved to {model_file}")
    
    def get_model_info(self):
        """Get model information"""
        return {
            'model_version': self.model_version,
            'model_type': type(self.model).__name__,
            'features': self.feature_names,
            'risk_levels': ['low', 'medium', 'high'],
            'last_updated': datetime.utcnow().isoformat()
        }
    
    def retrain_model(self):
        """Retrain model with new data"""
        self._create_and_train_model()
        return {
            'status': 'success',
            'model_version': self.model_version,
            'message': 'Model retrained successfully'
        }
