# 🏥 Smart Health Monitor System

A comprehensive AI-powered health monitoring platform with real-time vital tracking, intelligent risk prediction, and automated emergency response.

## 🌟 Features

### 1️⃣ **User Authentication**
- Secure registration and login
- Role-based access control (Admin / Doctor / Patient)
- Password encryption and session management
- Profile management

### 2️⃣ **Real-Time Vital Monitoring**
- Live heart rate tracking
- Blood pressure monitoring
- Oxygen level monitoring
- Temperature tracking
- IoT device simulation
- WebSocket-based real-time updates

### 3️⃣ **AI-Based Health Risk Prediction**
- Machine Learning model integration (Random Forest)
- Risk classification (Low / Medium / High)
- Probability estimation
- Model evaluation metrics
- Feature importance analysis

### 4️⃣ **Dynamic Health Score & Trend Analysis**
- Overall health score (0-100)
- Component scores (Cardiovascular, Respiratory, Metabolic)
- Weekly trend visualization
- Future risk forecasting
- Historical trend analysis

### 5️⃣ **AI Health Assistant & Chatbot**
- Health-related Q&A
- Prediction explanations
- Lifestyle recommendations
- System navigation support
- Personalized health advice

### 6️⃣ **Intelligent Doctor Recommendation**
- Specialist suggestions based on health risks
- Risk-based doctor mapping
- Urgency classification
- Match scoring algorithm
- Doctor profiles with ratings

### 7️⃣ **Smart Appointment Scheduling**
- Available time slot detection
- Conflict prevention
- Appointment tracking
- Reminder notifications
- Rescheduling support

### 8️⃣ **Automated Alert & Emergency Response**
- Critical vital sign detection
- Email and UI alert triggers
- Emergency suggestion system
- Severity classification
- Real-time notifications

### 9️⃣ **Patient Results & Medical Report Management**
- Prediction history storage
- Automated PDF report generation
- Doctor remarks section
- Multiple report types
- Download support

### 🔟 **Administrative Analytics & Monitoring**
- User statistics dashboard
- Risk distribution analytics
- Appointment analytics
- System performance metrics
- Weekly trends visualization

## 🏗️ System Architecture

```
smart_health_monitor_system/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models.py                # Database models
│   ├── routes/                  # API endpoints
│   │   ├── auth.py             # Authentication
│   │   ├── vitals.py           # Vital monitoring
│   │   ├── predictions.py      # Health predictions
│   │   ├── health_score.py     # Health scoring
│   │   ├── chatbot.py          # AI assistant
│   │   ├── doctors.py          # Doctor management
│   │   ├── appointments.py     # Scheduling
│   │   ├── alerts.py           # Alert system
│   │   ├── reports.py          # Report generation
│   │   └── admin.py            # Admin dashboard
│   └── ml/                      # Machine Learning
│       ├── predictor.py        # Risk prediction model
│       └── model_trainer.py    # Model training
├── config.py                    # Configuration
├── run.py                       # Application entry point
├── requirements.txt             # Dependencies
└── README.md                    # Documentation
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd smart_health-_monitor_system
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///health_monitor.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Step 5: Initialize Database
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Step 6: Run the Application
```bash
python run.py
```

The application will be available at `http://localhost:5000`

## 🌐 Web Interface

### Access the Web Interface
Open your browser and navigate to```
http://localhost:5000
```

### Login Credentials (Test Users)

**Patient Account:**
- Username: `patient1`
- Password: `patient123`

**Doctor Account:**
- Username: `dr_smith`
- Password: `doctor123`

**Admin Account:**
- Username: `admin`
- Password: `admin123`

### Web Interface Features

The web interface provides:

1. **Login Page** - Secure authentication with test credentials
2. **Vital Signs Tab** 
   - Record vital signs manually with forms
   - Simulate IoT device data with one click
   - View latest vital signs in real-time
3. **Health Score Tab**
   - Calculate your current health score (0-100)
   - View health trends and status
4. **AI Prediction Tab**
   - Get AI-powered health risk predictions
   - View risk level, confidence, and recommendations
5. **AI Assistant Tab**
   - Chat with the AI health assistant
   - Get personalized health advice
   - Ask questions about your health data
6. **Doctors Tab**
   - Get doctor recommendations based on your health
   - View specialist suggestions with urgency levels

### Quick Start Guide

1. **Login** with one of the test accounts
2. **Record Vitals** in the Vital Signs tab (or click "Simulate IoT Data")
3. **Calculate Health Score** in the Health Score tab
4. **Get AI Prediction** in the AI Prediction tab
5. **Chat with AI** in the AI Assistant tab
6. **View Recommendations** in the Doctors tab

## 📡 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secure_password",
  "role": "patient",
  "full_name": "John Doe",
  "date_of_birth": "1990-01-01"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>
```

### Vital Signs Endpoints

#### Record Vitals
```http
POST /api/vitals/record
Content-Type: application/json

{
  "heart_rate": 75,
  "blood_pressure_systolic": 120,
  "blood_pressure_diastolic": 80,
  "oxygen_level": 98.5,
  "temperature": 36.8
}
```

#### Get Vital History
```http
GET /api/vitals/history?days=7
```

#### Simulate IoT Data
```http
POST /api/vitals/simulate
```

### Health Prediction Endpoints

#### Predict Health Risk
```http
POST /api/predictions/predict
Content-Type: application/json

{
  "age": 45,
  "bmi": 28.5,
  "heart_rate": 85,
  "blood_pressure_systolic": 135,
  "blood_pressure_diastolic": 88,
  "oxygen_level": 96,
  "cholesterol": 220,
  "glucose": 110
}
```

#### Get Prediction History
```http
GET /api/predictions/history?limit=10
```

### Health Score Endpoints

#### Calculate Health Score
```http
POST /api/health-score/calculate
```

#### Get Health Trend
```http
GET /api/health-score/trend?weeks=12
```

### Chatbot Endpoints

#### Chat with AI Assistant
```http
POST /api/chatbot/chat
Content-Type: application/json

{
  "message": "What is my current health risk?"
}
```

#### Get Chat History
```http
GET /api/chatbot/history?limit=20
```

### Doctor Endpoints

#### Get Doctor Recommendations
```http
GET /api/doctors/recommend?patient_id=1
```

#### Search Doctors
```http
GET /api/doctors/search?q=cardiologist
```

### Appointment Endpoints

#### Book Appointment
```http
POST /api/appointments/book
Content-Type: application/json

{
  "doctor_id": 2,
  "appointment_date": "2026-03-01T10:00:00",
  "duration_minutes": 30,
  "reason": "Regular checkup",
  "urgency": "normal"
}
```

#### Get Available Slots
```http
GET /api/appointments/available-slots?doctor_id=2&date=2026-03-01
```

### Alert Endpoints

#### Get Alerts
```http
GET /api/alerts/list?severity=critical
```

#### Get Emergency Suggestions
```http
GET /api/alerts/emergency-suggestions
```

### Report Endpoints

#### Generate Report
```http
POST /api/reports/generate
Content-Type: application/json

{
  "report_type": "health_summary",
  "title": "Monthly Health Summary"
}
```

#### Download Report
```http
GET /api/reports/<report_id>/download
```

### Admin Endpoints

#### Get Dashboard Statistics
```http
GET /api/admin/dashboard
Authorization: Bearer <admin_token>
```

#### Get High-Risk Patients
```http
GET /api/admin/risks/high-risk-patients
Authorization: Bearer <admin_token>
```

## 🔒 Security Features

- **Password Hashing**: Werkzeug secure password hashing
- **Session Management**: Flask-Login session handling
- **Role-Based Access Control**: Admin, Doctor, Patient roles
- **Input Validation**: Data validation on all endpoints
- **SQL Injection Prevention**: SQLAlchemy ORM
- **CORS Protection**: Flask-CORS configuration

## 🤖 Machine Learning Model

The system uses a **Random Forest Classifier** for health risk prediction with the following features:

**Input Features:**
- Age
- BMI
- Heart Rate
- Blood Pressure (Systolic & Diastolic)
- Oxygen Level
- Cholesterol
- Blood Glucose

**Output:**
- Risk Level: Low / Medium / High
- Risk Probability: 0.0 - 1.0
- Contributing Factors
- Predicted Conditions
- Confidence Score

**Model Performance:**
- Training Accuracy: ~85%
- Feature Importance Analysis
- Cross-validation
- Regular retraining capability

## 📊 Database Schema

### Users
- User authentication and profile information
- Role-based access control
- Doctor profiles (for medical staff)

### Vital Signs
- Real-time health measurements
- Historical tracking
- Source tracking (manual/IoT)

### Health Predictions
- AI-generated risk assessments
- Contributing factors
- Confidence scores

### Health Scores
- Overall health scores
- Component scores
- Trend tracking

### Appointments
- Scheduling information
- Status tracking
- Conflict prevention

### Alerts
- Critical notifications
- Severity levels
- Resolution tracking

### Medical Reports
- Generated reports
- PDF storage
- Doctor remarks

## 🔧 Technology Stack

**Backend:**
- Flask 3.0
- SQLAlchemy (ORM)
- Flask-Login (Authentication)
- Flask-SocketIO (Real-time)
- Flask-Mail (Email notifications)

**Machine Learning:**
- scikit-learn
- NumPy
- pandas

**Report Generation:**
- ReportLab (PDF generation)
- Matplotlib (Charts)

**Database:**
- SQLite (Development)
- PostgreSQL/MySQL (Production-ready)

## 🧪 Testing

### Create Test Users
```python
# Admin user
POST /api/auth/register
{
  "username": "admin",
  "email": "admin@health.com",
  "password": "admin123",
  "role": "admin",
  "full_name": "System Administrator"
}

# Doctor user
POST /api/auth/register
{
  "username": "dr_smith",
  "email": "drsmith@health.com",
  "password": "doctor123",
  "role": "doctor",
  "full_name": "Dr. John Smith",
  "doctor_profile": {
    "specialization": "Cardiologist",
    "experience_years": 10,
    "license_number": "MD12345"
  }
}

# Patient user
POST /api/auth/register
{
  "username": "patient1",
  "email": "patient@example.com",
  "password": "patient123",
  "role": "patient",
  "full_name": "Jane Doe",
  "date_of_birth": "1985-05-15"
}
```

### Test Real-time Monitoring
```bash
# Terminal 1: Start the server
python run.py

# Terminal 2: Simulate IoT data
curl -X POST http://localhost:5000/api/vitals/simulate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"
```

## 🚀 Production Deployment

### Using Gunicorn
```bash
gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 run:app
```

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "run:app"]
```

## 📈 Future Enhancements

- [ ] Mobile app integration
- [ ] Wearable device connectivity
- [ ] Advanced ML models (Deep Learning)
- [ ] Multi-language support
- [ ] Telemedicine video consultation
- [ ] Pharmacy integration
- [ ] Insurance claim processing
- [ ] Health goal tracking
- [ ] Nutrition planning
- [ ] Exercise recommendations

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

Smart Health Monitor System Development Team

## 📞 Support

For support, email support@healthmonitor.com or open an issue in the repository.

---

**Built with ❤️ for better healthcare monitoring**