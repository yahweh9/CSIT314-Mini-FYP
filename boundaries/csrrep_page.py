# boundaries/csrrep_page.py
"""
CSR Representative Dashboard Page
Displays the main dashboard with opportunities, shortlist, and analytics
"""

from flask import redirect, render_template, session
from entities.UserEntity import UserEntity, db
from entities.PINRequestEntity import PINRequestEntity
from entities.ShortlistEntity import ShortlistEntity
from entities.FeedbackEntity import FeedbackEntity
from datetime import datetime, timedelta


def display_dashboard_csrrep():
    """Display CSR Rep main dashboard"""
    
    # Check if user is logged in and has CSR Rep role
    if 'username' not in session or session.get('role') != 'csrrep':
        return redirect('/')
    
    try:
        csrrep_id = session.get('user_id')
        
        # Get current user info
        current_user = UserEntity.query.get(csrrep_id)
        if not current_user:
            return redirect('/')
        
        # ============================================================================
        # Calculate Statistics
        # ============================================================================
        
        # 1. Active Opportunities (open requests in the system)
        active_opportunities = PINRequestEntity.query.filter_by(status='open').count()
        
        # 2. Shortlist count (opportunities saved by this CSR Rep)
        shortlist_count = ShortlistEntity.query.filter_by(csrrep_id=csrrep_id).count()
        
        # 3. Completed Services (requests assigned by this CSR Rep that are completed)
        completed_count = PINRequestEntity.query.filter(
            PINRequestEntity.assigned_by_id == csrrep_id,
            PINRequestEntity.status == 'completed'
        ).count()
        
        # 4. Total hours (count of completed services as a proxy for hours)
        # Since we don't have 'hours' field, we'll use completed count
        total_hours = completed_count  # Simplified: just count completed services
        
        # 5. Recent Activities
        recent_activities = []
        
        # Get recent shortlist additions
        try:
            recent_shortlists = ShortlistEntity.query.filter_by(csrrep_id=csrrep_id).order_by(
                ShortlistEntity.added_at.desc()
            ).limit(3).all()
            
            for shortlist in recent_shortlists:
                opp = PINRequestEntity.query.get(shortlist.request_id)
                if opp:
                    recent_activities.append({
                        'date': shortlist.added_at,
                        'description': f'Saved "{opp.title}" to shortlist'
                    })
        except:
            pass  # If added_at doesn't exist, skip
        
        # Get recent completed services
        try:
            recent_completed = PINRequestEntity.query.filter(
                PINRequestEntity.assigned_by_id == csrrep_id,
                PINRequestEntity.status == 'completed'
            ).order_by(PINRequestEntity.completed_date.desc()).limit(3).all()
            
            for service in recent_completed:
                recent_activities.append({
                    'date': service.completed_date or datetime.now(),
                    'description': f'Marked "{service.title}" as completed'
                })
        except:
            pass  # If completed_date doesn't exist, skip
        
        # Sort by date (most recent first)
        if recent_activities:
            recent_activities.sort(key=lambda x: x['date'], reverse=True)
            recent_activities = recent_activities[:5]  # Keep only top 5
        
        # 6. Calculate impact score
        impact_score = _calculate_impact_score(csrrep_id)
        
        # ============================================================================
        # Render Template with Data
        # ============================================================================
        
        return render_template(
            'dashboard_csrrep.html',
            user=current_user,
            active_opportunities=active_opportunities,
            shortlist_count=shortlist_count,
            completed_count=completed_count,
            total_hours=total_hours,
            recent_activities=recent_activities,
            impact_score=impact_score
        )
    
    except Exception as e:
        print(f"Error in display_dashboard_csrrep: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect('/')


def _calculate_impact_score(csrrep_id):
    """
    Calculate impact score for CSR Rep based on:
    - Number of completed services
    - Average rating from feedback
    """
    try:
        # Base score from completed services
        completed_services = PINRequestEntity.query.filter(
            PINRequestEntity.assigned_by_id == csrrep_id,
            PINRequestEntity.status == 'completed'
        ).count()
        
        base_score = completed_services * 10  # 10 points per completed service
        
        # Bonus from feedback ratings
        try:
            avg_rating = db.session.query(db.func.avg(FeedbackEntity.rating)).join(
                PINRequestEntity,
                FeedbackEntity.request_id == PINRequestEntity.request_id
            ).filter(PINRequestEntity.assigned_by_id == csrrep_id).scalar()
            
            rating_bonus = (avg_rating * 5) if avg_rating else 0
        except:
            rating_bonus = 0
        
        # Total impact score
        impact_score = int(base_score + rating_bonus)
        
        return impact_score
    
    except Exception as e:
        print(f"Error calculating impact score: {str(e)}")
        return 0