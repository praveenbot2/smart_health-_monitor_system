"""Service for persistent random patient data seeding with matched risk levels."""

from __future__ import annotations

import json
import random
from datetime import date, datetime

from database import db
from database.models import HealthPrediction, User, VitalSign


FIRST_NAMES = [
    "Aarav", "Vihaan", "Anaya", "Diya", "Ishaan", "Riya", "Kabir", "Meera", "Arjun", "Sara",
    "Rahul", "Priya", "Karan", "Neha", "Aisha", "Rohan", "Nikhil", "Pooja", "Ritik", "Naina"
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Reddy", "Kumar", "Gupta", "Nair", "Yadav", "Joshi", "Verma"
]


def random_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def date_of_birth_for_age(age: int) -> date:
    today = date.today()
    return date(today.year - age, random.randint(1, 12), random.randint(1, 28))


def pick_features_for_target(target_level: str) -> dict:
    """Generate a candidate feature set intended for a target risk level."""
    if target_level == "low":
        age = random.randint(21, 42)
        bmi = round(random.uniform(19.0, 24.5), 1)
        hr = random.randint(62, 88)
        bp_sys = random.randint(105, 124)
        bp_dia = random.randint(68, 82)
        oxygen = round(random.uniform(96.0, 99.5), 1)
        chol = round(random.uniform(150, 199), 1)
        glucose = round(random.uniform(78, 99), 1)
    elif target_level == "medium":
        age = random.randint(38, 62)
        bmi = round(random.uniform(25.1, 30.2), 1)
        hr = random.randint(72, 102)
        bp_sys = random.randint(126, 142)
        bp_dia = random.randint(82, 92)
        oxygen = round(random.uniform(93.5, 96.2), 1)
        chol = round(random.uniform(200, 245), 1)
        glucose = round(random.uniform(100, 128), 1)
    else:  # high
        age = random.randint(55, 82)
        bmi = round(random.uniform(30.5, 38.0), 1)
        hr = random.randint(95, 122)
        bp_sys = random.randint(145, 178)
        bp_dia = random.randint(92, 112)
        oxygen = round(random.uniform(86.0, 93.0), 1)
        chol = round(random.uniform(240, 320), 1)
        glucose = round(random.uniform(126, 220), 1)

    height_m = round(random.uniform(1.50, 1.88), 2)
    weight_kg = round(bmi * (height_m ** 2), 1)

    return {
        "age": age,
        "bmi": bmi,
        "heart_rate": hr,
        "blood_pressure_systolic": bp_sys,
        "blood_pressure_diastolic": bp_dia,
        "oxygen_level": oxygen,
        "cholesterol": chol,
        "glucose": glucose,
        "height": height_m,
        "weight": weight_kg,
    }


def _risk_score(features: dict) -> int:
    score = 0

    age = features["age"]
    bmi = features["bmi"]
    bp_sys = features["blood_pressure_systolic"]
    bp_dia = features["blood_pressure_diastolic"]
    hr = features["heart_rate"]
    oxygen = features["oxygen_level"]
    chol = features["cholesterol"]
    glucose = features["glucose"]

    if age > 60:
        score += 2
    elif age > 45:
        score += 1

    if bmi > 30:
        score += 2
    elif bmi > 25:
        score += 1

    if bp_sys > 140 or bp_dia > 90:
        score += 2
    elif bp_sys > 130 or bp_dia > 85:
        score += 1

    if hr > 100 or hr < 60:
        score += 1

    if oxygen < 92:
        score += 2
    elif oxygen < 95:
        score += 1

    if chol > 240:
        score += 2
    elif chol > 200:
        score += 1

    if glucose > 126:
        score += 2
    elif glucose > 100:
        score += 1

    return score


def _risk_level_from_score(score: int) -> str:
    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _predicted_conditions(features: dict, risk_level: str) -> list[str]:
    conditions = []

    if features["blood_pressure_systolic"] > 140 or features["blood_pressure_diastolic"] > 90:
        conditions.append("Hypertension risk")
    if features["glucose"] > 126:
        conditions.append("Diabetes risk")
    if features["cholesterol"] > 240:
        conditions.append("Cardiovascular disease risk")
    if features["bmi"] > 30:
        conditions.append("Obesity-related complications")
    if features["oxygen_level"] < 92:
        conditions.append("Respiratory issues")

    if not conditions:
        if risk_level == "low":
            conditions.append("No significant health risks detected")
        else:
            conditions.append("General health monitoring recommended")

    return conditions


def _contributing_factors(features: dict) -> list[str]:
    factors = []

    if features["age"] > 60:
        factors.append(f"Advanced age ({features['age']} years)")

    if features["bmi"] > 30:
        factors.append(f"High BMI ({features['bmi']:.1f})")
    elif features["bmi"] > 25:
        factors.append(f"Elevated BMI ({features['bmi']:.1f})")

    if features["blood_pressure_systolic"] > 140:
        factors.append(f"High blood pressure ({features['blood_pressure_systolic']} mmHg)")
    elif features["blood_pressure_systolic"] > 130:
        factors.append(f"Elevated blood pressure ({features['blood_pressure_systolic']} mmHg)")

    if features["heart_rate"] > 100:
        factors.append(f"Elevated heart rate ({features['heart_rate']} bpm)")
    elif features["heart_rate"] < 60:
        factors.append(f"Low heart rate ({features['heart_rate']} bpm)")

    if features["oxygen_level"] < 92:
        factors.append(f"Low oxygen saturation ({features['oxygen_level']}%)")

    if features["cholesterol"] > 240:
        factors.append(f"High cholesterol ({features['cholesterol']} mg/dL)")

    if features["glucose"] > 126:
        factors.append(f"High blood glucose ({features['glucose']} mg/dL)")

    if not factors:
        factors.append("All parameters within normal range")

    return factors


def _predict_from_rules(features: dict) -> dict:
    score = _risk_score(features)
    level = _risk_level_from_score(score)

    risk_probability = min(0.99, max(0.05, score / 10.0))
    confidence = min(0.99, 0.55 + abs(score - 4) * 0.06)

    return {
        "risk_level": level,
        "risk_probability": float(risk_probability),
        "predicted_conditions": _predicted_conditions(features, level),
        "contributing_factors": _contributing_factors(features),
        "model_version": "rule_based_seed_v1",
        "confidence_score": float(confidence),
    }


def generate_matched_prediction(target_level: str, max_attempts: int = 30):
    """Try multiple candidates until predicted level matches target level."""
    for _ in range(max_attempts):
        features = pick_features_for_target(target_level)
        prediction = _predict_from_rules(features)
        if prediction.get("risk_level") == target_level:
            return features, prediction

    features = pick_features_for_target(target_level)
    prediction = _predict_from_rules(features)
    return features, prediction


def next_patient_identity(index: int) -> tuple[str, str]:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    username = f"seed_patient_{stamp}_{index}"
    email = f"{username}@health.local"
    return username, email


def seed_patients(count: int = 10) -> dict:
    """Persist random patient users + vitals + predictions with matched target risk levels."""
    if count < 10:
        raise ValueError("Please provide count >= 10")

    targets = ["low", "medium", "high"]
    created = []

    for i in range(count):
        target_level = targets[i % len(targets)]
        features, pred = generate_matched_prediction(target_level)

        full_name = random_name()
        username, email = next_patient_identity(i + 1)

        gender = random.choice(["Male", "Female", "Other"])
        dob = date_of_birth_for_age(features["age"])

        patient = User(
            username=username,
            email=email,
            full_name=full_name,
            role="patient",
            gender=gender,
            date_of_birth=dob,
            phone=f"9{random.randint(100000000, 999999999)}",
            address=f"{random.randint(10, 999)} Wellness Street",
            medical_history="Auto-generated seeded profile for testing and analytics.",
            current_medications="As per doctor advice",
            allergies=random.choice(["None", "Pollen", "Penicillin", "Dust"]),
            blood_type=random.choice(["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]),
        )
        patient.set_password("patient123")
        db.session.add(patient)
        db.session.flush()

        vital = VitalSign(
            patient_id=patient.id,
            heart_rate=features["heart_rate"],
            blood_pressure_systolic=features["blood_pressure_systolic"],
            blood_pressure_diastolic=features["blood_pressure_diastolic"],
            oxygen_level=features["oxygen_level"],
            temperature=round(random.uniform(36.2, 37.4), 1),
            weight=features["weight"],
            height=features["height"],
            cholesterol=features["cholesterol"],
            glucose=features["glucose"],
            source="seed_script",
            notes=f"Seeded profile targeting {target_level} risk",
        )
        db.session.add(vital)

        prediction = HealthPrediction(
            patient_id=patient.id,
            risk_level=pred["risk_level"],
            risk_probability=float(pred["risk_probability"]),
            predicted_conditions=json.dumps(pred.get("predicted_conditions", [])),
            contributing_factors=json.dumps(pred.get("contributing_factors", [])),
            model_version=pred.get("model_version", "1.0.0"),
            confidence_score=float(pred.get("confidence_score", 0.0)),
            age=features["age"],
            bmi=float(features["bmi"]),
            heart_rate=features["heart_rate"],
            blood_pressure_systolic=features["blood_pressure_systolic"],
            blood_pressure_diastolic=features["blood_pressure_diastolic"],
            oxygen_level=features["oxygen_level"],
            cholesterol=features["cholesterol"],
            glucose=features["glucose"],
        )
        db.session.add(prediction)

        created.append(
            {
                "patient_id": patient.id,
                "username": username,
                "target_level": target_level,
                "predicted_level": pred["risk_level"],
                "risk_probability": round(float(pred["risk_probability"]), 4),
            }
        )

    db.session.commit()

    matched = sum(1 for row in created if row["target_level"] == row["predicted_level"])
    return {
        "requested": count,
        "created": len(created),
        "matched": matched,
        "mismatch": len(created) - matched,
        "rows": created,
    }
