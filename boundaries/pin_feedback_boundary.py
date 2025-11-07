# boundaries/pin_feedback_boundary.py
from flask import request, session, redirect, url_for, render_template, flash, jsonify
from datetime import datetime, timedelta
from controllers.FeedbackController import FeedbackController
from entities.UserEntity import UserEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.FeedbackEntity import FeedbackEntity

def display_pin_feedback_dashboard():
    """Display PIN's feedback dashboard with all features"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    pin = UserEntity.query.get(session['user_id'])
    
    # Get all filter parameters
    rating_filter = request.args.get('rating', type=int)
    service_filter = request.args.get('service_type')
    date_filter = request.args.get('date_range')
    
    # Get pending requests for feedback
    pending_requests = FeedbackController.get_completed_requests_for_pin(
        session['user_id'], 
        service_filter
    )
    
    # Get personal feedback history
    feedback_history = FeedbackController.get_feedback_history_for_pin(
        session['user_id'], 
        rating_filter, 
        service_filter, 
        date_filter
    )
    
    # Get community ratings
    community_ratings = FeedbackController.get_community_ratings()
    
    # Get public feedback (other PINs' reviews)
    public_feedback = FeedbackController.get_public_feedback(
        rating_filter, 
        service_filter, 
        date_filter
    )
    
    # Get feedback statistics
    feedback_stats = FeedbackController.get_feedback_stats_for_pin(
        session['user_id'], 
        service_filter, 
        date_filter
    )
    
    return render_template('pin_feedback_dashboard.html', 
                         user=pin, 
                         pending_requests=pending_requests,
                         feedback_history=feedback_history,
                         community_ratings=community_ratings,
                         public_feedback=public_feedback,
                         feedback_stats=feedback_stats,
                         current_rating_filter=rating_filter,
                         current_service_filter=service_filter,
                         current_date_filter=date_filter)

def display_feedback_form(request_id):
    """Display feedback form for a specific request"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    # Verify the PIN owns this request and it's completed
    pin_request = PINRequestEntity.query.filter_by(
        request_id=request_id,
        requested_by_id=session['user_id'],
        status='completed'
    ).first()
    
    if not pin_request:
        flash('Invalid request or request not completed', 'error')
        return redirect(url_for('pin_feedback_dashboard'))
    
    # Check for existing feedback
    existing_feedback = FeedbackEntity.query.filter_by(
        request_id=request_id,
        pin_id=session['user_id']
    ).first()
    
    if existing_feedback:
        flash('You have already submitted feedback for this request', 'error')
        return redirect(url_for('pin_feedback_dashboard'))
    
    pin = UserEntity.query.get(session['user_id'])
    return render_template('pin_feedback_form.html', 
                         user=pin, 
                         request=pin_request)

def submit_feedback():
    """Handle feedback submission"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    # Get form data
    request_id = request.form.get('request_id')
    rating = request.form.get('rating')
    comments = request.form.get('comments', '')
    
    # Validate required fields
    if not request_id or not rating:
        flash('Please provide both rating and request information', 'error')
        return redirect(url_for('display_feedback_form_route', request_id=request_id))
    
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5', 'error')
            return redirect(url_for('display_feedback_form_route', request_id=request_id))
    except ValueError:
        flash('Invalid rating value', 'error')
        return redirect(url_for('display_feedback_form_route', request_id=request_id))
    
    # Check if request exists and is completed
    pin_request = PINRequestEntity.query.filter_by(
        request_id=request_id,
        requested_by_id=session['user_id'],
        status='completed'
    ).first()
    
    if not pin_request:
        flash('Invalid request or request not completed', 'error')
        return redirect(url_for('pin_feedback_dashboard'))
    
    # Check for duplicate feedback
    existing_feedback = FeedbackEntity.query.filter_by(
        request_id=request_id,
        pin_id=session['user_id']
    ).first()
    
    if existing_feedback:
        flash('Feedback already submitted for this request', 'error')
        return redirect(url_for('pin_feedback_dashboard'))
    
    # Determine who to rate
    if pin_request.assigned_by_id:  # Rated CSRRep who assigned the request
        rated_user_id = pin_request.assigned_by_id
        rated_user_role = 'csrrep'
    elif pin_request.assigned_to_id:  # Rated CV who completed the request
        rated_user_id = pin_request.assigned_to_id
        rated_user_role = 'cv'
    else:
        flash('Cannot provide feedback - no assigned user found for this request', 'error')
        return redirect(url_for('pin_feedback_dashboard'))
    
    # Create feedback
    try:
        new_feedback = FeedbackEntity(
            request_id=request_id,
            pin_id=session['user_id'],
            rated_user_id=rated_user_id,
            rated_user_role=rated_user_role,
            rating=rating,
            comments=comments
        )
        
        from entities.UserEntity import db
        db.session.add(new_feedback)
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('pin_feedback_dashboard'))
        
    except Exception as e:
        flash('Error submitting feedback. Please try again.', 'error')
        return redirect(url_for('display_feedback_form_route', request_id=request_id))

def bulk_rate_requests():
    """Handle bulk rating of multiple requests"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return jsonify({'success': False, 'message': 'Unauthorized access'})
    
    if request.method == 'POST':
        request_ids = request.form.getlist('request_ids[]')
        rating = request.form.get('rating')
        comments = request.form.get('comments', '')
        
        if not request_ids or not rating:
            return jsonify({'success': False, 'message': 'Please select requests and provide a rating'})
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'})
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid rating value'})
        
        success, message = FeedbackController.bulk_rate_requests(request_ids, rating, comments)
        
        if success:
            flash(message, 'success')
            return jsonify({'success': True, 'message': message})
        else:
            flash(message, 'error')
            return jsonify({'success': False, 'message': message})
    
    return jsonify({'success': False, 'message': 'Invalid request method'})