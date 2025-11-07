from flask import request, session, flash
from datetime import datetime, timedelta
from entities.UserEntity import db
from entities.FeedbackEntity import FeedbackEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.UserEntity import UserEntity

class FeedbackController:
    
    @staticmethod
    def get_completed_requests_for_pin(pin_id, service_type=None):
        """Get all completed requests that PIN can provide feedback for"""
        try:
            query = PINRequestEntity.query.filter_by(
                requested_by_id=pin_id, 
                status='completed'
            )
            
            if service_type:
                query = query.filter_by(service_type=service_type)
            
            completed_requests = query.all()
            
            # Filter out requests that already have feedback
            feedback_eligible_requests = []
            for req in completed_requests:
                existing_feedback = FeedbackEntity.query.filter_by(
                    request_id=req.request_id,
                    pin_id=pin_id
                ).first()
                
                # Only include requests that don't have feedback yet AND have someone to rate
                if not existing_feedback and (req.assigned_to_id or req.assigned_by_id):
                    # Determine who to rate
                    if req.assigned_by_id:  # If assigned by CSRRep, rate CSRRep
                        req.rate_user_id = req.assigned_by_id
                        req.rate_user_role = 'csrrep'
                        feedback_eligible_requests.append(req)
                    elif req.assigned_to_id:  # Otherwise rate the CV who completed it
                        req.rate_user_id = req.assigned_to_id
                        req.rate_user_role = 'cv'
                        feedback_eligible_requests.append(req)
            
            return feedback_eligible_requests
            
        except Exception as e:
            return []

    @staticmethod
    def get_feedback_history_for_pin(pin_id, rating_filter=None, service_type=None, date_range=None):
        """Get all feedback submitted by PIN, with multiple filters"""
        try:
            query = FeedbackEntity.query.filter_by(pin_id=pin_id)
            
            if rating_filter:
                query = query.filter_by(rating=rating_filter)
            
            # Apply service type filter by joining with PINRequestEntity
            if service_type:
                query = query.join(PINRequestEntity).filter(PINRequestEntity.service_type == service_type)
            
            # Apply date range filter
            if date_range:
                end_date = datetime.utcnow()
                if date_range == 'week':
                    start_date = end_date - timedelta(days=7)
                elif date_range == 'month':
                    start_date = end_date - timedelta(days=30)
                elif date_range == 'year':
                    start_date = end_date - timedelta(days=365)
                else:
                    start_date = end_date - timedelta(days=7)  # default to week
                
                query = query.filter(FeedbackEntity.created_at >= start_date)
            
            # Get feedback with request details
            feedback_list = query.order_by(FeedbackEntity.created_at.desc()).all()
            
            # Add request details to each feedback
            for feedback in feedback_list:
                request_details = PINRequestEntity.query.filter_by(request_id=feedback.request_id).first()
                if request_details:
                    feedback.request_title = request_details.title
                    feedback.request_description = request_details.description
                    feedback.service_type = request_details.service_type
                else:
                    feedback.request_title = "Unknown Request"
                    feedback.request_description = "No description available"
                    feedback.service_type = "Unknown"
            
            return feedback_list
            
        except Exception as e:
            return []

    @staticmethod
    def get_feedback_stats_for_pin(pin_id, service_type=None, date_range=None):
        """Get statistics about PIN's feedback with filters"""
        try:
            query = FeedbackEntity.query.filter_by(pin_id=pin_id)
            
            # Apply service type filter
            if service_type:
                query = query.join(PINRequestEntity).filter(PINRequestEntity.service_type == service_type)
            
            # Apply date range filter
            if date_range:
                end_date = datetime.utcnow()
                if date_range == 'week':
                    start_date = end_date - timedelta(days=7)
                elif date_range == 'month':
                    start_date = end_date - timedelta(days=30)
                elif date_range == 'year':
                    start_date = end_date - timedelta(days=365)
                else:
                    start_date = end_date - timedelta(days=7)
                
                query = query.filter(FeedbackEntity.created_at >= start_date)
            
            all_feedback = query.all()
            
            if not all_feedback:
                return {
                    'total': 0,
                    'average': 0,
                    'rating_counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                }
            
            total = len(all_feedback)
            average = sum(fb.rating for fb in all_feedback) / total
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for fb in all_feedback:
                rating_counts[fb.rating] += 1
            
            return {
                'total': total,
                'average': round(average, 1),
                'rating_counts': rating_counts
            }
            
        except Exception as e:
            return {
                'total': 0,
                'average': 0,
                'rating_counts': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

    @staticmethod
    def get_community_ratings():
        """Get average ratings for different service types across all feedback"""
        try:
            # Get all feedback with service types
            all_feedback = db.session.query(
                FeedbackEntity, PINRequestEntity.service_type
            ).join(
                PINRequestEntity, FeedbackEntity.request_id == PINRequestEntity.request_id
            ).all()
            
            service_ratings = {}
            
            for feedback, service_type in all_feedback:
                service_type = service_type or 'Other'
                if service_type not in service_ratings:
                    service_ratings[service_type] = {
                        'total_rating': 0,
                        'count': 0,
                        'ratings': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                    }
                
                service_ratings[service_type]['total_rating'] += feedback.rating
                service_ratings[service_type]['count'] += 1
                service_ratings[service_type]['ratings'][feedback.rating] += 1
            
            # Calculate averages and percentages
            for service_type, data in service_ratings.items():
                data['average'] = round(data['total_rating'] / data['count'], 1)
                data['rating_percentages'] = {}
                for rating in range(1, 6):
                    data['rating_percentages'][rating] = round((data['ratings'][rating] / data['count']) * 100, 1)
            
            return service_ratings
            
        except Exception as e:
            return {}

    @staticmethod
    def get_public_feedback(rating_filter=None, service_type=None, date_range=None):
        """Get all feedback from all PINs (public view)"""
        try:
            query = FeedbackEntity.query
            
            if rating_filter:
                query = query.filter_by(rating=rating_filter)
            
            # Apply service type filter
            if service_type:
                query = query.join(PINRequestEntity).filter(PINRequestEntity.service_type == service_type)
            
            # Apply date range filter
            if date_range:
                end_date = datetime.utcnow()
                if date_range == 'week':
                    start_date = end_date - timedelta(days=7)
                elif date_range == 'month':
                    start_date = end_date - timedelta(days=30)
                elif date_range == 'year':
                    start_date = end_date - timedelta(days=365)
                else:
                    start_date = end_date - timedelta(days=7)
                
                query = query.filter(FeedbackEntity.created_at >= start_date)
            
            # Get feedback with request and user details
            feedback_list = query.order_by(FeedbackEntity.created_at.desc()).all()
            
            # Add details to each feedback
            for feedback in feedback_list:
                # Get request details
                request_details = PINRequestEntity.query.filter_by(request_id=feedback.request_id).first()
                if request_details:
                    feedback.request_title = request_details.title
                    feedback.service_type = request_details.service_type
                
                # Get PIN user details (who gave the feedback)
                pin_user = UserEntity.query.get(feedback.pin_id)
                if pin_user:
                    feedback.pin_name = pin_user.fullname
                    feedback.pin_initials = pin_user.fullname[:2].upper()
                else:
                    feedback.pin_name = "Anonymous User"
                    feedback.pin_initials = "AU"
            
            return feedback_list
            
        except Exception as e:
            return []

    @staticmethod
    def bulk_rate_requests(request_ids, rating, comments):
        """Rate multiple requests at once with the same rating and comments"""
        try:
            if 'user_id' not in session or session.get('role') != 'pin':
                return False, "Unauthorized access"
            
            successful_ratings = 0
            errors = []
            
            for request_id in request_ids:
                # Check if request exists and is completed
                pin_request = PINRequestEntity.query.filter_by(
                    request_id=request_id,
                    requested_by_id=session['user_id'],
                    status='completed'
                ).first()
                
                if not pin_request:
                    errors.append(f"Request {request_id} not found or not completed")
                    continue
                
                # Check for duplicate feedback
                existing_feedback = FeedbackEntity.query.filter_by(
                    request_id=request_id,
                    pin_id=session['user_id']
                ).first()
                
                if existing_feedback:
                    errors.append(f"Feedback already submitted for request {request_id}")
                    continue
                
                # Determine who to rate
                if pin_request.assigned_by_id:
                    rated_user_id = pin_request.assigned_by_id
                    rated_user_role = 'csrrep'
                elif pin_request.assigned_to_id:
                    rated_user_id = pin_request.assigned_to_id
                    rated_user_role = 'cv'
                else:
                    errors.append(f"No assigned user for request {request_id}")
                    continue
                
                # Create feedback
                new_feedback = FeedbackEntity(
                    request_id=request_id,
                    pin_id=session['user_id'],
                    rated_user_id=rated_user_id,
                    rated_user_role=rated_user_role,
                    rating=rating,
                    comments=comments
                )
                
                db.session.add(new_feedback)
                successful_ratings += 1
            
            if successful_ratings > 0:
                db.session.commit()
                return True, f"Successfully rated {successful_ratings} requests"
            else:
                return False, "No requests were rated. " + "; ".join(errors)
                
        except Exception as e:
            return False, f"Error during bulk rating: {str(e)}"
    
    @staticmethod
    def submit_feedback():
        """Handle feedback submission from PIN"""
        if 'user_id' not in session or session.get('role') != 'pin':
            flash('Unauthorized access', 'error')
            return False
            
        request_id = request.form.get('request_id')
        rating = request.form.get('rating')
        comments = request.form.get('comments', '')
        
        # Validate inputs
        if not request_id or not rating:
            flash('Please provide both rating and request information', 'error')
            return False
            
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                flash('Rating must be between 1 and 5', 'error')
                return False
        except ValueError:
            flash('Invalid rating value', 'error')
            return False
        
        # Check if request exists and is completed
        pin_request = PINRequestEntity.query.filter_by(
            request_id=request_id,
            requested_by_id=session['user_id'],
            status='completed'
        ).first()
        
        if not pin_request:
            flash('Invalid request or request not completed', 'error')
            return False
        
        # Check for duplicate feedback
        existing_feedback = FeedbackEntity.query.filter_by(
            request_id=request_id,
            pin_id=session['user_id']
        ).first()
        
        if existing_feedback:
            flash('Feedback already submitted for this request', 'error')
            return False
        
        # Determine who to rate
        if pin_request.assigned_by_id:  # Rated CSRRep who assigned the request
            rated_user_id = pin_request.assigned_by_id
            rated_user_role = 'csrrep'
        elif pin_request.assigned_to_id:  # Rated CV who completed the request
            rated_user_id = pin_request.assigned_to_id
            rated_user_role = 'cv'
        else:
            flash('Cannot provide feedback - no assigned user found for this request', 'error')
            return False
        
        # Create feedback
        new_feedback = FeedbackEntity(
            request_id=request_id,
            pin_id=session['user_id'],
            rated_user_id=rated_user_id,
            rated_user_role=rated_user_role,
            rating=rating,
            comments=comments
        )
        
        db.session.add(new_feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return True
    
    @staticmethod
    def get_feedback_for_user(user_id, user_role):
        """Get all feedback received by a user (CSRRep or CV)"""
        return FeedbackEntity.query.filter_by(
            rated_user_id=user_id,
            rated_user_role=user_role
        ).all()
    
    @staticmethod
    def get_average_rating(user_id, user_role):
        """Calculate average rating for a user"""
        feedbacks = FeedbackEntity.query.filter_by(
            rated_user_id=user_id,
            rated_user_role=user_role
        ).all()
        
        if not feedbacks:
            return 0
        
        total_rating = sum(fb.rating for fb in feedbacks)
        return round(total_rating / len(feedbacks), 1)