# controllers/CVRequestController.py
from flask import request, session, flash
from typing import List

from entities.MatchEntity import MatchEntity

from datetime import datetime, timedelta
from flask import request, session, redirect, url_for, render_template
from sqlalchemy import func
from entities.UserEntity import db, UserEntity
from entities.PINRequestEntity import PINRequestEntity
from entities.FeedbackEntity import FeedbackEntity
from entities.InterestEntity import InterestEntity

class RequestController:
    
    @staticmethod
    def get_incomplete_requests(cv, status=None, urgency=None, sort=None):
        now = datetime.utcnow()

        # Auto-update late requests using entity method
        active_reqs = PINRequestEntity.query.filter_by(
            assigned_to_id=cv.user_id, status="active"
        ).all()

        for req in active_reqs:
            if req.is_late():
                req.mark_as_late()

        db.session.commit()

        # Base query (pending, active, late)
        query = PINRequestEntity.query.filter(
            PINRequestEntity.assigned_to_id == cv.user_id,
            PINRequestEntity.status.in_(["pending", "active", "late"])
        )

        # Filter by status using entity match method
        if status:
            query = query.filter(PINRequestEntity.status == status)

        # Filter by urgency using entity method
        if urgency:
            query = query.filter(
                func.lower(PINRequestEntity.urgency) == urgency.lower()
            )

        # Apply sorting using the entity helper
        if sort == "end_date_asc":
            query = PINRequestEntity.sort_by_end_date(query, "asc")
        elif sort == "end_date_desc":
            query = PINRequestEntity.sort_by_end_date(query, "desc")

        # Get final list
        assigned_requests = query.all()

        # Attach PIN name (boundary convenience data)
        for req in assigned_requests:
            pin_user = UserEntity.query.get(req.requested_by_id)
            req.pin_name = pin_user.fullname if pin_user else "Unknown"

        return assigned_requests

    # Get all completed requests of a CV (status is 'completed')
    @staticmethod
    def get_request_history(cv):
        # get PIN requests completed by this CV - status == "completed"
        completed_requests = (
            PINRequestEntity.query
            .filter(
                PINRequestEntity.assigned_to_id == cv.user_id,
                PINRequestEntity.status.in_(["completed"])
            )
            .all()
        )

        # attach the PIN's name to each request
        for req in completed_requests:
            pin_user = UserEntity.query.get(req.requested_by_id)
            req.pin_name = pin_user.fullname if pin_user else "Unknown"
            req.feedback_rating = FeedbackEntity.get_feedback_rating(req.request_id)
            
        return completed_requests
    
    @staticmethod
    def accept_request(request_id):
        req = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if req and req.status == 'pending':
            req.status = 'active'
            db.session.commit()
        return redirect(url_for('dashboard_cv'))

    @staticmethod
    def reject_request(request_id):
        req = PINRequestEntity.query.filter_by(request_id=request_id).first()
        if req and req.status == 'pending':
            db.session.delete(req)
            db.session.commit()
        return redirect(url_for('dashboard_cv'))

    # Set request status to 'active'
    @staticmethod
    def accept_request(request_id):
        try:
            req = PINRequestEntity.query.filter_by(request_id=request_id).first()
            if req and req.status == 'pending':
                req.status = 'active'
                db.session.commit()
                return True
            return False

        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return False
        
    @staticmethod
    def reject_request(request_id):
        try:
            # call the entity method
            req = PINRequestEntity.unassign(request_id)

            if req and req.status == 'pending':
                db.session.commit()
                return True

            return False

        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return False

        
    @staticmethod
    def complete_request(request_id):
        try:
            req = PINRequestEntity.query.filter_by(request_id=request_id).first()
            if req and (req.status == 'active' or req.status == 'late'):
                req.status = 'completed'
                req.completed_date = datetime.utcnow() + timedelta(hours=8)
                db.session.commit()
                return True
            return False
        
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return False
        
    @staticmethod
    def express_interest(request_id, cv_id):
        try:
            # check if interest already exists
            existing = InterestEntity.query.filter_by(request_id=request_id, cv_id=cv_id).first()
            if existing:
                flash("You already expressed interest.", "warning")
                print("ALREADY EXPRESSED") #DELETE
                return False

            new_interest = InterestEntity(request_id=request_id, cv_id=cv_id)
            db.session.add(new_interest)

            # Update shortlist_count
            req = PINRequestEntity.query.filter_by(request_id=request_id).first()
            req.shortlist_count = InterestEntity.query.filter_by(request_id=request_id).count()

            db.session.commit()

            print("SUCCESS") #DELETE
            flash("You have expressed your interest!", "success")
            return True

        except Exception as e:
            db.session.rollback()
            flash("Something went wrong.", "danger")
            print("Error:", e)
            return False


    @staticmethod
    def normalize_skills(value):
        if not value:
            return []
        if isinstance(value, list):
            return [v.lower().strip() for v in value]
        return [v.lower().strip() for v in str(value).replace(';', ',').split(',') if v.strip()]


    # EDITED NAME TO 'open'
    @staticmethod
    def get_open_requests() -> List[PINRequestEntity]:
        return (PINRequestEntity.query
                .filter(PINRequestEntity.status.in_(['open', 'pending']))
                .all())

    @staticmethod
    def find_candidates(pin_id: int) -> List[UserEntity]:
        pin = PINRequestEntity.query.get(pin_id)
        if not pin:
            return []
        req_skills = RequestController.normalize_skills(getattr(pin, 'required_skills', ''))
        pin_loc = getattr(pin, 'location', '').lower()
        candidates = (UserEntity.query
                    .filter(UserEntity.role == 'volunteer', UserEntity.status == 'active')
                    .all())
        matched = []
        for u in candidates:
            skills = RequestController.normalize_skills(getattr(u, 'skills', ''))
            if any(s in skills for s in req_skills) or getattr(u, 'location', '').lower() == pin_loc:
                matched.append(u)
        return matched

    @staticmethod
    def rank_candidates(pin_id: int, users: List[UserEntity]) -> List[UserEntity]:
        pin = PINRequestEntity.query.get(pin_id)
        if not pin:
            return users
        req_skills = RequestController.normalize_skills(getattr(pin, 'required_skills', ''))
        pin_loc = getattr(pin, 'location', '').lower()
        def score(u: UserEntity):
            overlap = len(set(req_skills) & set(RequestController.normalize_skills(getattr(u, 'skills', ''))))
            loc_score = 1 if getattr(u, 'location', '').lower() == pin_loc else 0
            return overlap * 10 + loc_score
        return sorted(users, key=score, reverse=True)

    @staticmethod
    def assign_user(pin_id: int, user_id: int) -> MatchEntity | None:
        pin = PINRequestEntity.query.get(pin_id)
        user = UserEntity.query.get(user_id)
        if not pin or not user:
            return None
        match = MatchEntity(pin_request_id=pin.request_id, user_id=user.user_id, status='confirmed')
        db.session.add(match)
        pin.status = 'fulfilled'
        db.session.add(pin)
        db.session.commit()
        return match

    @staticmethod
    def notify_parties(match: MatchEntity):
        print(f"[Notify] Match #{match.match_id} created for PIN {match.pin_request_id} and User {match.user_id}")

    @staticmethod
    def get_unassigned_requests():
        unassigned_requests = PINRequestEntity.get_unassigned()
        # Attach PIN name (boundary convenience data)
        for req in unassigned_requests:
            pin_user = UserEntity.query.get(req.requested_by_id)
            req.pin_name = pin_user.fullname if pin_user else "Unknown"
        return unassigned_requests

    @staticmethod
    def record_view(request_id, cv_id):
        # Check if this CV already viewed it
        from entities.RequestViewEntity import RequestViewEntity

        existing = RequestViewEntity.query.filter_by(
            request_id=request_id,
            cv_id=cv_id
        ).first()

        if existing:
            return False  # Already counted

        # Add new view record
        new_view = RequestViewEntity(request_id=request_id, cv_id=cv_id)
        db.session.add(new_view)

        # Increment view count
        req = PINRequestEntity.query.filter_by(request_id=request_id).first()
        req.view_count += 1

        db.session.commit()
        return True















