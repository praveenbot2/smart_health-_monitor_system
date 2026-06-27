"""
ML Model Initialization and Training
"""

from app.ml.predictor import HealthRiskPredictor

def initialize_models():
    """Initialize ML models on application startup"""
    print("Initializing ML models...")
    
    try:
        # Initialize health risk predictor
        predictor = HealthRiskPredictor()
        print("✓ Health Risk Predictor initialized successfully")
        
        return True
    except Exception as e:
        print(f"✗ Error initializing ML models: {e}")
        return False
