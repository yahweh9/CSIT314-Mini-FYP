# boundaries/csrrep_opportunities_boundary.py
"""
CSR Representative features for searching, shortlisting opportunities 
and viewing completed services history
"""

from flask import request, session, redirect, url_for, render_template, jsonify
from entities.UserEntity import UserEntity, db
from entities.PINRequestEntity import PINRequestEntity
from entities.FeedbackEntity import FeedbackEntity
from entities.ShortlistEntity import ShortlistEntity
from datetime import datetime, timedelta


# ============================================================================
# FEATURE 1: SEARCH & SHORTLIST OPPORTUNITIES
# ============================================================================

def display_search_opportunities():
    """Display search opportunities page with filters"""
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    # Get filter parameters
    search_query = request.args.get('search', '')
    service_type = request.args.get('service_type', '')
    urgency = request.args.get('urgency', '')
    status_filter = request.args.get('status', 'active')
    
    # Build query
    query = PINRequestEntity.query
    
    # Apply filters
    if search_query:
        query = query.filter(
            db.or_(
                PINRequestEntity.title.ilike(f'%{search_query}%'),
                PINRequestEntity.description.ilike(f'%{search_query}%'),
                PINRequestEntity.location.ilike(f'%{search_query}%')
            )
        )
    
    if service_type:
        query = query.filter_by(service_type=service_type)
    
    if urgency:
        query = query.filter_by(urgency=urgency)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    opportunities = query.paginate(page=page, per_page=10)
    
    # Get user's shortlist
    csrrep_id = session.get('user_id')
    shortlisted_ids = [item.request_id for item in ShortlistEntity.query.filter_by(csrrep_id=csrrep_id).all()]
    
    # Get service types for dropdown
    service_types = db.session.query(PINRequestEntity.service_type).distinct().filter(
        PINRequestEntity.service_type.isnot(None)
    ).all()
    service_types = [st[0] for st in service_types]
    
    return render_template(
        'csrrep_search_opportunities.html',
        opportunities=opportunities,
        shortlisted_ids=shortlisted_ids,
        service_types=service_types,
        current_search=search_query,
        current_service_type=service_type,
        current_urgency=urgency,
        current_status=status_filter
    )


def display_my_shortlist():
    """Display CSR Rep's shortlisted opportunities"""
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    csrrep_id = session.get('user_id')
    
    # Get shortlist with opportunity details
    shortlist_items = db.session.query(ShortlistEntity, PINRequestEntity).join(
        PINRequestEntity,
        ShortlistEntity.request_id == PINRequestEntity.request_id
    ).filter(ShortlistEntity.csrrep_id == csrrep_id).all()
    
    return render_template('csrrep_shortlist.html', shortlist_items=shortlist_items)


def add_to_shortlist():
    """Add opportunity to shortlist (AJAX)"""
    if 'user_id' not in session or session.get('role') != 'csrrep':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    request_id = request.form.get('request_id')
    csrrep_id = session.get('user_id')
    
    # Check if already shortlisted
    existing = ShortlistEntity.query.filter_by(request_id=request_id, csrrep_id=csrrep_id).first()
    if existing:
        # Changed: Return success: true so toast appears (but let user know it's already saved)
        return jsonify({'success': True, 'message': 'Already saved to shortlist', 'already_exists': True}), 200
    
    try:
        shortlist_item = ShortlistEntity(
            request_id=request_id,
            csrrep_id=csrrep_id,
            added_at=datetime.utcnow()
        )
        db.session.add(shortlist_item)
        db.session.commit()
        
        # Update shortlist count
        opp = PINRequestEntity.query.get(request_id)
        if opp:
            opp.shortlist_count = (opp.shortlist_count or 0) + 1
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Successfully added to shortlist', 'already_exists': False})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


def remove_from_shortlist():
    """Remove opportunity from shortlist (AJAX)"""
    if 'user_id' not in session or session.get('role') != 'csrrep':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    request_id = request.form.get('request_id')
    csrrep_id = session.get('user_id')
    
    try:
        shortlist_item = ShortlistEntity.query.filter_by(
            request_id=request_id,
            csrrep_id=csrrep_id
        ).first()
        
        if not shortlist_item:
            return jsonify({'success': False, 'message': 'Not in shortlist'}), 404
        
        db.session.delete(shortlist_item)
        
        # Update shortlist count
        opp = PINRequestEntity.query.get(request_id)
        if opp and opp.shortlist_count > 0:
            opp.shortlist_count -= 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Removed from shortlist'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


def display_opportunity_detail(request_id):
    """Display detailed view of an opportunity"""
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    opportunity = PINRequestEntity.query.get(request_id)
    if not opportunity:
        return render_template('error.html', message='Opportunity not found'), 404
    
    # Get PIN details
    pin_user = UserEntity.query.get(opportunity.requested_by_id)
    
    # Check if in shortlist
    csrrep_id = session.get('user_id')
    in_shortlist = ShortlistEntity.query.filter_by(
        request_id=request_id,
        csrrep_id=csrrep_id
    ).first() is not None
    
    # Increment view count
    opportunity.view_count = (opportunity.view_count or 0) + 1
    db.session.commit()
    
    return render_template(
        'csrrep_opportunity_detail.html',
        opportunity=opportunity,
        pin_user=pin_user,
        in_shortlist=in_shortlist
    )


# ============================================================================
# FEATURE 2: COMPLETED SERVICES HISTORY & ANALYTICS
# ============================================================================

def display_completed_services():
    """Display completed services with filters"""
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    csrrep_id = session.get('user_id')
    
    # Get filters
    service_type = request.args.get('service_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'completed_date_desc')
    
    # Build query for completed services assigned by this CSR
    query = PINRequestEntity.query.filter(
        PINRequestEntity.assigned_by_id == csrrep_id,
        PINRequestEntity.status == 'completed'
    )
    
    # Apply filters
    if service_type:
        query = query.filter_by(service_type=service_type)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(PINRequestEntity.completed_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(PINRequestEntity.completed_date < to_date)
        except ValueError:
            pass
    
    if search_query:
        query = query.filter(
            db.or_(
                PINRequestEntity.title.ilike(f'%{search_query}%'),
                PINRequestEntity.location.ilike(f'%{search_query}%')
            )
        )
    
    # Apply sorting
    if sort_by == 'completed_date_asc':
        query = query.order_by(PINRequestEntity.completed_date.asc())
    elif sort_by == 'title_asc':
        query = query.order_by(PINRequestEntity.title.asc())
    else:  # completed_date_desc (default)
        query = query.order_by(PINRequestEntity.completed_date.desc())
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    completed_services = query.paginate(page=page, per_page=15)
    
    # Get service types for filter
    service_types = db.session.query(PINRequestEntity.service_type).distinct().filter(
        PINRequestEntity.service_type.isnot(None)
    ).all()
    service_types = [st[0] for st in service_types]
    
    # Calculate statistics
    stats = _calculate_statistics(csrrep_id)
    
    return render_template(
        'csrrep_completed_services.html',
        completed_services=completed_services,
        service_types=service_types,
        current_service_type=service_type,
        current_date_from=date_from,
        current_date_to=date_to,
        current_search=search_query,
        current_sort=sort_by,
        stats=stats
    )


def display_service_detail(request_id):
    """Display detailed view of a completed service"""
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    csrrep_id = session.get('user_id')
    
    service = PINRequestEntity.query.filter(
        PINRequestEntity.request_id == request_id,
        PINRequestEntity.assigned_by_id == csrrep_id,
        PINRequestEntity.status == 'completed'
    ).first()
    
    if not service:
        return render_template('error.html', message='Service not found'), 404
    
    # Get related info
    pin_user = UserEntity.query.get(service.requested_by_id)
    cv_user = UserEntity.query.get(service.assigned_to_id)
    feedbacks = FeedbackEntity.query.filter_by(request_id=request_id).all()
    
    return render_template(
        'csrrep_service_detail.html',
        service=service,
        pin_user=pin_user,
        cv_user=cv_user,
        feedbacks=feedbacks
    )


def display_history_analytics():
    """Display analytics dashboard"""
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    csrrep_id = session.get('user_id')
    period = request.args.get('period', '30days')
    
    # Calculate date range
    if period == '7days':
        start_date = datetime.utcnow() - timedelta(days=7)
    elif period == '30days':
        start_date = datetime.utcnow() - timedelta(days=30)
    elif period == '90days':
        start_date = datetime.utcnow() - timedelta(days=90)
    else:
        start_date = datetime.min
    
    # Query completed services
    services = PINRequestEntity.query.filter(
        PINRequestEntity.assigned_by_id == csrrep_id,
        PINRequestEntity.status == 'completed',
        PINRequestEntity.completed_date >= start_date
    ).all()
    
    analytics = _calculate_detailed_analytics(services)
    
    # Get overall statistics
    stats = _calculate_statistics(csrrep_id)
    
    # Calculate total hours (placeholder - adjust based on your data)
    total_hours = sum([service.hours_completed if hasattr(service, 'hours_completed') else 0 for service in services])
    total_services = len(services)
    hours_this_month = len([s for s in services if s.completed_date and (datetime.utcnow() - s.completed_date).days <= 30])
    services_this_month = hours_this_month
    impact_score = stats.get('average_rating', 0) * 50  # Example calculation
    impact_tier = 'Bronze' if impact_score < 100 else 'Silver' if impact_score < 200 else 'Gold'
    people_helped = total_services * 5  # Example calculation
    environmental_hours = sum([s.hours_completed if hasattr(s, 'hours_completed') else 0 for s in services if s.service_type == 'environmental'])
    
    # Sample data for charts
    hours_monthly = [0, 0, 0, 0, 0, 0]  # Placeholder - populate from actual data
    service_type_counts = [total_services // 4, total_services // 4, total_services // 4, total_services // 4]  # Placeholder
    
    return render_template(
        'csrrep_history_analytics.html',
        total_hours=total_hours,
        total_services=total_services,
        hours_this_month=hours_this_month,
        services_this_month=services_this_month,
        impact_score=impact_score,
        impact_tier=impact_tier,
        people_helped=people_helped,
        environmental_hours=environmental_hours,
        hours_monthly=hours_monthly,
        service_type_counts=service_type_counts,
        analytics=analytics,
        current_period=period
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_statistics(csrrep_id):
    """Calculate summary statistics for CSR Rep"""
    completed = PINRequestEntity.query.filter(
        PINRequestEntity.assigned_by_id == csrrep_id,
        PINRequestEntity.status == 'completed'
    ).count()
    
    avg_rating = db.session.query(db.func.avg(FeedbackEntity.rating)).join(
        PINRequestEntity,
        FeedbackEntity.request_id == PINRequestEntity.request_id
    ).filter(PINRequestEntity.assigned_by_id == csrrep_id).scalar()
    
    most_common = db.session.query(
        PINRequestEntity.service_type,
        db.func.count(PINRequestEntity.request_id)
    ).filter(
        PINRequestEntity.assigned_by_id == csrrep_id,
        PINRequestEntity.status == 'completed'
    ).group_by(PINRequestEntity.service_type).order_by(
        db.func.count(PINRequestEntity.request_id).desc()
    ).first()
    
    return {
        'total_completed': completed,
        'average_rating': round(avg_rating, 2) if avg_rating else 0,
        'most_common_service': most_common[0] if most_common else 'N/A'
    }


def _calculate_detailed_analytics(services):
    """Calculate detailed analytics from services"""
    analytics = {
        'total': len(services),
        'by_service_type': {},
        'by_urgency': {},
        'avg_completion_time': 0
    }
    
    completion_times = []
    
    for service in services:
        # Count by type
        service_type = service.service_type or 'Unspecified'
        analytics['by_service_type'][service_type] = analytics['by_service_type'].get(service_type, 0) + 1
        
        # Count by urgency
        urgency = service.urgency or 'Not specified'
        analytics['by_urgency'][urgency] = analytics['by_urgency'].get(urgency, 0) + 1
        
        # Calculate completion time
        if service.start_date and service.completed_date:
            time_diff = (service.completed_date - service.start_date).days
            completion_times.append(time_diff)
    
    if completion_times:
        analytics['avg_completion_time'] = round(sum(completion_times) / len(completion_times), 1)
    
    return analytics


def export_to_csv():
    """Export completed services to CSV"""
    if 'user_id' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    import csv
    from io import StringIO
    from flask import send_file
    
    csrrep_id = session.get('user_id')
    services = PINRequestEntity.query.filter(
        PINRequestEntity.assigned_by_id == csrrep_id,
        PINRequestEntity.status == 'completed'
    ).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Request ID', 'Title', 'Service Type', 'Location', 'Completed Date'])
    
    for service in services:
        writer.writerow([
            service.request_id,
            service.title,
            service.service_type,
            service.location,
            service.completed_date.strftime('%Y-%m-%d') if service.completed_date else ''
        ])
    
    output.seek(0)
    return send_file(
        StringIO(output.getvalue()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'completed_services_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    )