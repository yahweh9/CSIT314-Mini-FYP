# controllers/PINRequestController.py
from flask import request, session, flash
from datetime import datetime
from entities.UserEntity import db
from entities.PINRequestEntity import PINRequestEntity

class PINRequestController:
    
    @staticmethod
    def create_request():
        """Create a new assistance request"""
        if 'user_id' not in session or session.get('role') != 'pin':
            flash('Unauthorized access', 'error')
            return False
            
        title = request.form.get('title')
        description = request.form.get('description')
        service_type = request.form.get('service_type')
        location = request.form.get('location')
        urgency = request.form.get('urgency')
        skills_required = request.form.get('skills_required')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # Validate required fields
        if not all([title, description, service_type, location]):
            flash('Please fill in all required fields', 'error')
            return False
            
        try:
            # Parse dates
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d') if start_date else datetime.utcnow()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.utcnow()
            
            # Create new request WITH ALL FIELDS
            new_request = PINRequestEntity(
                requested_by_id=session['user_id'],
                title=title,
                description=description,
                service_type=service_type,
                location=location,
                urgency=urgency or 'medium',
                skills_required=skills_required,
                start_date=start_date_obj,
                end_date=end_date_obj,
                status='pending'
            )
            
            db.session.add(new_request)
            db.session.commit()
            
            flash('Request created successfully! Volunteers can now view your request.', 'success')
            return True
            
        except Exception as e:
            flash('Error creating request. Please try again.', 'error')
            return False
    
    @staticmethod
    def get_user_requests(pin_id, status_filter=None):
        """Get all requests for a PIN user"""
        query = PINRequestEntity.query.filter_by(requested_by_id=pin_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
            
        return query.order_by(PINRequestEntity.created_at.desc()).all()
    
    @staticmethod
    def get_active_requests(pin_id):
        """Get active and pending requests"""
        return PINRequestEntity.query.filter(
            PINRequestEntity.requested_by_id == pin_id,
            PINRequestEntity.status.in_(['pending', 'active'])
        ).order_by(PINRequestEntity.created_at.desc()).all()
    
    @staticmethod
    def get_completed_requests(pin_id):
        """Get completed requests for history"""
        return PINRequestEntity.query.filter(
            PINRequestEntity.requested_by_id == pin_id,
            PINRequestEntity.status.in_(['completed', 'expired'])
        ).order_by(PINRequestEntity.created_at.desc()).all()
    
    @staticmethod
    def get_request_by_id(request_id, pin_id=None):
        """Get specific request with optional ownership check"""
        query = PINRequestEntity.query.filter_by(request_id=request_id)
        if pin_id:
            query = query.filter_by(requested_by_id=pin_id)
        return query.first()
    
    @staticmethod
    def update_request_status(request_id, status):
        """Update request status"""
        request = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if request:
            request.status = status
            request.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def increment_view_count(request_id):
        """Increment view count when someone views the request"""
        request = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if request:
            request.view_count += 1
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def increment_shortlist_count(request_id):
        """Increment shortlist count when someone shortlists the request"""
        request = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if request:
            request.shortlist_count += 1
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def update_request(request_id, form_data, pin_id=None):
        """Update an existing request with new details"""
        request_obj = PINRequestEntity.query.filter_by(request_id=request_id).first()

        # Ownership check
        if not request_obj or (pin_id and request_obj.requested_by_id != pin_id):
            flash("Unauthorized or request not found", "error")
            return False

        # Validate required fields
        title = form_data.get('title')
        description = form_data.get('description')
        service_type = form_data.get('service_type')
        location = form_data.get('location')

        if not all([title, description, service_type, location]):
            flash("Please fill in all required fields", "error")
            return False

        try:
            # Update fields
            request_obj.title = title
            request_obj.description = description
            request_obj.service_type = service_type
            request_obj.location = location
            request_obj.urgency = form_data.get('urgency') or 'medium'
            request_obj.skills_required = form_data.get('skills_required')

            # Dates
            start_date = form_data.get('start_date')
            end_date = form_data.get('end_date')
            if start_date:
                request_obj.start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                request_obj.end_date = datetime.strptime(end_date, '%Y-%m-%d')

            request_obj.updated_at = datetime.utcnow()

            db.session.commit()
            flash("Request updated successfully!", "success")
            return True

        except Exception as e:
            flash("Error updating request. Please try again.", "error")
            return False
        
    @staticmethod
    def cancel_request(request_id, pin_id=None):
        """Soft delete a request by marking it cancelled"""
        request_obj = PINRequestEntity.query.filter_by(request_id=request_id).first()

        # Ownership check
        if not request_obj or (pin_id and request_obj.requested_by_id != pin_id):
            flash("Unauthorized or request not found", "error")
            return False

        # Prevent cancellation if already processed
        if request_obj.status == 'completed':
            flash("This request cannot be cancelled as it is already being processed", "warning")
            return False

        try:
            request_obj.status = 'cancelled'
            request_obj.cancelled_at = datetime.utcnow()
            db.session.commit()
            flash("Request cancelled successfully", "success")
            return True

        except Exception as e:
            flash("Error cancelling request. Please try again.", "error")
            return False
    
    @staticmethod
    def get_unassigned_requests():
        return PINRequestEntity.get_unassigned()
