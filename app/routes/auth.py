"""
Module 1: User Authentication
- Registration
- Login / Logout
"""

import json
from datetime import datetime

from flask import Blueprint, jsonify, make_response, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_

from app import db
from database.models import (
    Alert,
    Appointment,
    ChatMessage,
    EmergencyContact,
    FamilyMember,
    HealthPrediction,
    HealthScore,
    MedicalReport,
    MentalHealthEntry,
    MentalHealthJournal,
    SOSEvent,
    User,
    UserSettings,
    VitalSign,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    """Register a new user"""
    data = request.get_json() or {}

    required_fields = ["username", "email", "password", "full_name"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists"}), 400

    user = User(
        username=data["username"],
        email=data["email"],
        role="user",
        full_name=data["full_name"],
        phone=data.get("phone"),
        gender=data.get("gender"),
        address=data.get("address"),
    )

    if "date_of_birth" in data and data["date_of_birth"]:
        try:
            user.date_of_birth = datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201


@bp.route("/login", methods=["POST"])
def login():
    """Login user - Single session enforcement"""
    data = request.get_json() or {}

    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Username/email and password required"}), 400

    # Check if another user is already logged in
    if current_user.is_authenticated:
        # If same user is logging in again, return success for smoother UX.
        same_user_identifier = (
            identifier.lower() == (current_user.username or "").lower()
            or identifier.lower() == (current_user.email or "").lower()
        )

        if same_user_identifier:
            return (
                jsonify(
                    {
                        "message": "Already logged in",
                        "user": current_user.to_dict(),
                        "redirect": "/dashboard",
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "error": "Another user is already logged in. Please logout first.",
                    "logged_in_user": current_user.username,
                }
            ),
            403,
        )

    # Allow login with either username or email (case-insensitive)
    user = User.query.filter(
        or_(
            func.lower(User.username) == identifier.lower(),
            func.lower(User.email) == identifier.lower(),
        )
    ).first()

    password_ok = False
    if user:
        # Preferred path: hashed password verification
        try:
            password_ok = user.check_password(password)
        except Exception:
            password_ok = False

        # Backward compatibility: legacy plaintext password in DB
        if (not password_ok) and user.password_hash == password:
            user.set_password(password)
            db.session.commit()
            password_ok = True

    if not user or not password_ok:
        return jsonify({"error": "Invalid username or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    login_user(user, remember=data.get("remember", False))

    return (
        jsonify({"message": "Login successful", "user": user.to_dict(), "redirect": "/dashboard"}),
        200,
    )


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({"message": "Logout successful"}), 200


@bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current logged-in user"""
    return jsonify({"user": current_user.to_dict()}), 200


@bp.route("/profile", methods=["GET", "PUT"])
@login_required
def profile():
    """Get or update user profile"""
    if request.method == "GET":
        return jsonify({"user": current_user.to_dict()}), 200

    # PUT - Update profile
    data = request.get_json() or {}

    # Update allowed fields
    allowed_fields = ["full_name", "phone", "gender", "address", "email"]
    for field in allowed_fields:
        if field in data:
            setattr(current_user, field, data[field])

    if "date_of_birth" in data and data["date_of_birth"]:
        try:
            current_user.date_of_birth = datetime.strptime(data["date_of_birth"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    db.session.commit()

    return jsonify({"message": "Profile updated successfully", "user": current_user.to_dict()}), 200


@bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json() or {}

    if not data.get("current_password") or not data.get("new_password"):
        return jsonify({"error": "Current and new password required"}), 400

    if not current_user.check_password(data["current_password"]):
        return jsonify({"error": "Current password is incorrect"}), 401

    current_user.set_password(data["new_password"])
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200


def _get_or_create_user_settings(user_id):
    """Get settings row for user, creating defaults if needed."""
    settings = UserSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.session.add(settings)
        db.session.commit()
    return settings


@bp.route("/preferences", methods=["GET", "PUT"])
@login_required
def preferences():
    """Get or update notification + privacy preferences"""
    settings = _get_or_create_user_settings(current_user.id)

    if request.method == "GET":
        return jsonify({"preferences": settings.to_dict()}), 200

    data = request.get_json() or {}
    allowed_fields = [
        "email_notifications",
        "sms_notifications",
        "push_notifications",
        "profile_visibility",
        "share_anonymized_data",
        "allow_family_access",
        "data_export_consent",
    ]

    for field in allowed_fields:
        if field in data:
            setattr(settings, field, data[field])

    if settings.profile_visibility not in {"private", "care_team", "public"}:
        return jsonify({"error": "Invalid profile_visibility value"}), 400

    db.session.commit()
    return (
        jsonify(
            {
                "message": "Preferences updated successfully",
                "preferences": settings.to_dict(),
            }
        ),
        200,
    )


@bp.route("/export-data", methods=["GET"])
@login_required
def export_data():
    """Export user account and health data as JSON download"""
    settings = _get_or_create_user_settings(current_user.id)

    if not settings.data_export_consent:
        return jsonify({"error": "Data export is disabled in privacy settings"}), 403

    export_payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": current_user.to_dict(),
        "preferences": settings.to_dict(),
        "vital_signs": [
            v.to_dict()
            for v in VitalSign.query.filter_by(patient_id=current_user.id)
            .order_by(VitalSign.recorded_at.desc())
            .all()
        ],
        "health_predictions": [
            p.to_dict()
            for p in HealthPrediction.query.filter_by(patient_id=current_user.id)
            .order_by(HealthPrediction.predicted_at.desc())
            .all()
        ],
        "health_scores": [
            s.to_dict()
            for s in HealthScore.query.filter_by(patient_id=current_user.id)
            .order_by(HealthScore.calculated_at.desc())
            .all()
        ],
        "alerts": [
            a.to_dict()
            for a in Alert.query.filter_by(patient_id=current_user.id)
            .order_by(Alert.created_at.desc())
            .all()
        ],
        "appointments_as_patient": [
            a.to_dict()
            for a in Appointment.query.filter_by(patient_id=current_user.id)
            .order_by(Appointment.created_at.desc())
            .all()
        ],
        "medical_reports": [
            r.to_dict()
            for r in MedicalReport.query.filter_by(patient_id=current_user.id)
            .order_by(MedicalReport.generated_at.desc())
            .all()
        ],
        "chat_messages": [
            m.to_dict()
            for m in ChatMessage.query.filter_by(user_id=current_user.id)
            .order_by(ChatMessage.created_at.desc())
            .all()
        ],
        "mental_health_entries": [
            e.to_dict()
            for e in MentalHealthEntry.query.filter_by(user_id=current_user.id)
            .order_by(MentalHealthEntry.created_at.desc())
            .all()
        ],
        "mental_health_journals": [
            j.to_dict()
            for j in MentalHealthJournal.query.filter_by(user_id=current_user.id)
            .order_by(MentalHealthJournal.created_at.desc())
            .all()
        ],
        "family_members": [
            f.to_dict()
            for f in FamilyMember.query.filter_by(user_id=current_user.id)
            .order_by(FamilyMember.created_at.desc())
            .all()
        ],
        "emergency_contacts": [
            c.to_dict()
            for c in EmergencyContact.query.filter_by(user_id=current_user.id)
            .order_by(EmergencyContact.created_at.desc())
            .all()
        ],
        "sos_events": [
            e.to_dict()
            for e in SOSEvent.query.filter_by(user_id=current_user.id)
            .order_by(SOSEvent.created_at.desc())
            .all()
        ],
    }

    file_name = (
        f"smart-health-export-{current_user.username}-"
        f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json"
    )
    response = make_response(json.dumps(export_payload, indent=2))
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
    return response, 200
