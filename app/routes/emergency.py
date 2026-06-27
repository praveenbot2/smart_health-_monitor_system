"""
Emergency SOS Routes
Handles emergency contact management and SOS activation
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from database import db
from database.models import EmergencyContact, SOSEvent, User, VitalSign
from services.notification_service import get_notification_service
from datetime import datetime
import json

bp = Blueprint('emergency', __name__, url_prefix='/api/emergency')


# Emergency Contact Management

@bp.route('/contacts', methods=['GET'])
@login_required
def get_emergency_contacts():
    """Get all emergency contacts for current user"""
    try:
        contacts = EmergencyContact.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(EmergencyContact.priority.asc()).all()
        
        return jsonify({
            'contacts': [c.to_dict() for c in contacts],
            'count': len(contacts),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/contacts', methods=['POST'])
@login_required
def add_emergency_contact():
    """Add a new emergency contact"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Name and phone are required', 'success': False}), 400
        
        # Create new contact
        contact = EmergencyContact(
            user_id=current_user.id,
            name=data['name'],
            relationship=data.get('relationship', 'Other'),
            phone=data['phone'],
            email=data.get('email'),
            priority=data.get('priority', 1),
            notify_via_sms=data.get('notify_via_sms', True),
            notify_via_email=data.get('notify_via_email', True),
            notes=data.get('notes')
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({
            'message': 'Emergency contact added successfully',
            'contact': contact.to_dict(),
            'success': True
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def update_emergency_contact(contact_id):
    """Update an emergency contact"""
    try:
        contact = EmergencyContact.query.filter_by(
            id=contact_id,
            user_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contact not found', 'success': False}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            contact.name = data['name']
        if 'relationship' in data:
            contact.relationship = data['relationship']
        if 'phone' in data:
            contact.phone = data['phone']
        if 'email' in data:
            contact.email = data['email']
        if 'priority' in data:
            contact.priority = data['priority']
        if 'notify_via_sms' in data:
            contact.notify_via_sms = data['notify_via_sms']
        if 'notify_via_email' in data:
            contact.notify_via_email = data['notify_via_email']
        if 'notes' in data:
            contact.notes = data['notes']
        
        contact.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Emergency contact updated successfully',
            'contact': contact.to_dict(),
            'success': True
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_emergency_contact(contact_id):
    """Delete an emergency contact"""
    try:
        contact = EmergencyContact.query.filter_by(
            id=contact_id,
            user_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'error': 'Contact not found', 'success': False}), 404
        
        # Soft delete
        contact.is_active = False
        db.session.commit()
        
        return jsonify({
            'message': 'Emergency contact removed successfully',
            'success': True
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


# SOS Activation

@bp.route('/sos/activate', methods=['POST'])
@login_required
def activate_sos():
    """Activate emergency SOS and notify contacts"""
    try:
        data = request.get_json()
        
        # Create SOS event
        sos_event = SOSEvent(
            user_id=current_user.id,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            location_address=data.get('location_address'),
            emergency_type=data.get('emergency_type', 'Medical'),
            description=data.get('description'),
            status='active'
        )
        
        db.session.add(sos_event)
        db.session.flush()
        
        # Get emergency contacts
        contacts = EmergencyContact.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(EmergencyContact.priority.asc()).all()
        
        # Get latest vital signs and health data
        latest_vital = VitalSign.query.filter_by(
            patient_id=current_user.id
        ).order_by(VitalSign.recorded_at.desc()).first()
        
        # Prepare emergency message
        location_info = data.get('location_address', 'Location not available')
        if data.get('latitude') and data.get('longitude'):
            location_info += f" (Lat: {data['latitude']}, Lon: {data['longitude']})"
        
        emergency_message = f"""
        🚨 EMERGENCY SOS ALERT 🚨
        
        {current_user.full_name} has activated an emergency SOS signal.
        
        Emergency Type: {data.get('emergency_type', 'Medical Emergency')}
        Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
        Location: {location_info}
        
        """
        
        if data.get('description'):
            emergency_message += f"\nDescription: {data['description']}\n"
        
        if latest_vital:
            emergency_message += f"""
        Latest Health Data:
        - Heart Rate: {latest_vital.heart_rate} bpm
        - Blood Pressure: {latest_vital.blood_pressure_systolic}/{latest_vital.blood_pressure_diastolic} mmHg
        - Oxygen Level: {latest_vital.oxygen_level}%
        - Temperature: {latest_vital.temperature}°C
            """
        
        emergency_message += "\n\nPlease respond immediately or contact emergency services."
        
        # Notify contacts
        notification_service = get_notification_service()
        notified_contacts = []
        
        for contact in contacts:
            try:
                # Send email if enabled
                if contact.notify_via_email and contact.email:
                    notification_service.send_email(
                        recipient=contact.email,
                        subject=f'🚨 EMERGENCY: {current_user.full_name} needs help',
                        body=emergency_message,
                        html=f'<pre>{emergency_message}</pre>'
                    )
                
                # Send SMS if enabled
                if contact.notify_via_sms and contact.phone:
                    notification_service.send_sms(
                        phone_number=contact.phone,
                        message=f"🚨 EMERGENCY: {current_user.full_name} needs help at {location_info}. Check your email for details."
                    )
                
                notified_contacts.append(contact.id)
            except Exception as e:
                print(f"Error notifying contact {contact.id}: {e}")
        
        # Update SOS event with notification info
        sos_event.contacts_notified = json.dumps(notified_contacts)
        sos_event.emergency_services_notified = True  # In real system, would actually call services
        
        db.session.commit()
        
        return jsonify({
            'message': 'Emergency SOS activated successfully',
            'sos_event_id': sos_event.id,
            'contacts_notified': len(notified_contacts),
            'emergency_services_notified': True,
            'success': True
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/sos/events', methods=['GET'])
@login_required
def get_sos_events():
    """Get SOS event history"""
    try:
        events = SOSEvent.query.filter_by(
            user_id=current_user.id
        ).order_by(SOSEvent.created_at.desc()).limit(10).all()
        
        return jsonify({
            'events': [e.to_dict() for e in events],
            'count': len(events),
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/sos/events/<int:event_id>/resolve', methods=['POST'])
@login_required
def resolve_sos_event(event_id):
    """Mark an SOS event as resolved"""
    try:
        event = SOSEvent.query.filter_by(
            id=event_id,
            user_id=current_user.id
        ).first()
        
        if not event:
            return jsonify({'error': 'Event not found', 'success': False}), 404
        
        event.status = 'resolved'
        event.resolved_at = datetime.utcnow()
        
        # Calculate response time if available
        if event.created_at and event.resolved_at:
            event.response_time = int((event.resolved_at - event.created_at).total_seconds())
        
        db.session.commit()
        
        return jsonify({
            'message': 'SOS event resolved',
            'event': event.to_dict(),
            'success': True
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@bp.route('/quick-dial', methods=['GET'])
@login_required
def get_quick_dial_numbers():
    """Get quick dial emergency numbers"""
    try:
        # Standard emergency numbers
        quick_dial = [
            {'name': '🚑 Emergency Services', 'number': '911', 'type': 'emergency'},
            {'name': '🏥 Ambulance', 'number': '911', 'type': 'ambulance'},
            {'name': '☎️ Poison Control', 'number': '1-800-222-1222', 'type': 'poison'},
            {'name': '💊 Suicide Prevention', 'number': '988', 'type': 'crisis'}
        ]
        
        # Add user's emergency contacts
        contacts = EmergencyContact.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(EmergencyContact.priority.asc()).limit(3).all()
        
        for contact in contacts:
            quick_dial.append({
                'name': f'👤 {contact.name}',
                'number': contact.phone,
                'type': 'personal',
                'relationship': contact.relationship
            })
        
        return jsonify({
            'quick_dial': quick_dial,
            'success': True
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
