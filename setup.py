"""
Setup and Test Script for Smart Health Monitor System
"""

import os
import sys

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_cors',
        'flask_socketio',
        'flask_mail',
        'sklearn',
        'numpy',
        'pandas',
        'reportlab'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def setup_environment():
    """Set up environment variables"""
    print("\n🔧 Setting up environment...")
    
    if not os.path.exists('.env'):
        print("⚠️  .env file not found. Creating from .env.example...")
        if os.path.exists('.env.example'):
            import shutil
            shutil.copy('.env.example', '.env')
            print("✅ .env file created. Please update with your settings.")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file exists")
    
    return True

def initialize_database():
    """Initialize the database"""
    print("\n🗄️  Initializing database...")
    
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_test_users():
    """Create test users"""
    print("\n👥 Creating test users...")
    
    try:
        from app import create_app, db
        from database.models import User, DoctorProfile
        from datetime import date
        
        app = create_app()
        with app.app_context():
            # Check if admin already exists
            if User.query.filter_by(username='admin').first():
                print("ℹ️  Test users already exist")
                return True
            
            # Create admin
            admin = User(
                username='admin',
                email='admin@health.com',
                role='admin',
                full_name='System Administrator'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create doctor
            doctor = User(
                username='dr_smith',
                email='drsmith@health.com',
                role='doctor',
                full_name='Dr. John Smith',
                phone='555-0101'
            )
            doctor.set_password('doctor123')
            db.session.add(doctor)
            db.session.flush()
            
            # Create doctor profile
            doctor_profile = DoctorProfile(
                user_id=doctor.id,
                specialization='Cardiologist',
                license_number='MD12345',
                experience_years=10,
                qualification='MD, Cardiology',
                consultation_fee=150.0,
                available_days='["Monday","Tuesday","Wednesday","Thursday","Friday"]'
            )
            db.session.add(doctor_profile)
            
            # Create patient
            patient = User(
                username='patient1',
                email='patient@example.com',
                role='patient',
                full_name='Jane Doe',
                date_of_birth=date(1985, 5, 15),
                gender='Female',
                phone='555-0102'
            )
            patient.set_password('patient123')
            db.session.add(patient)
            
            db.session.commit()
            
            print("✅ Test users created:")
            print("   Admin    - username: admin, password: admin123")
            print("   Doctor   - username: dr_smith, password: doctor123")
            print("   Patient  - username: patient1, password: patient123")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create test users: {e}")
        return False

def test_ml_model():
    """Test ML model initialization"""
    print("\n🤖 Testing ML model...")
    
    try:
        from app.ml.predictor import HealthRiskPredictor
        
        predictor = HealthRiskPredictor()
        
        # Test prediction
        test_features = {
            'age': 45,
            'bmi': 28.5,
            'heart_rate': 85,
            'blood_pressure_systolic': 135,
            'blood_pressure_diastolic': 88,
            'oxygen_level': 96,
            'cholesterol': 220,
            'glucose': 110
        }
        
        result = predictor.predict(test_features)
        
        print(f"✅ ML model working correctly")
        print(f"   Test prediction: {result['risk_level']} risk ({result['risk_probability']:.2%})")
        
        return True
    except Exception as e:
        print(f"❌ ML model test failed: {e}")
        return False

def run_server_test():
    """Test if server can start"""
    print("\n🌐 Testing server startup...")
    
    try:
        from app import create_app
        
        app = create_app()
        print("✅ Server initialization successful")
        print("\nTo start the server, run: python run.py")
        
        return True
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🏥 Smart Health Monitor System - Setup & Test")
    print("=" * 60)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Dependencies Check", check_dependencies),
        ("Environment Setup", setup_environment),
        ("Database Initialization", initialize_database),
        ("Test Users Creation", create_test_users),
        ("ML Model Test", test_ml_model),
        ("Server Test", run_server_test)
    ]
    
    results = []
    for step_name, step_func in steps:
        success = step_func()
        results.append((step_name, success))
        
        if not success:
            print(f"\n⚠️  Setup stopped at: {step_name}")
            break
    
    print("\n" + "=" * 60)
    print("📊 Setup Summary")
    print("=" * 60)
    
    for step_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n🎉 Setup completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Update .env file with your configuration")
        print("   2. Run the server: python run.py")
        print("   3. Access the API at: http://localhost:5000")
        print("\n📚 Test Credentials:")
        print("   Admin:   username=admin,    password=admin123")
        print("   Doctor:  username=dr_smith, password=doctor123")
        print("   Patient: username=patient1, password=patient123")
    else:
        print("\n❌ Setup incomplete. Please fix the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
