# boundaries/CSRRepPage.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from controllers import RequestController as RC

csr_bp = Blueprint('csr', __name__, url_prefix='/csr')

@csr_bp.route('/match')
def match_page():
    pins = RC.get_incomplete_requests()
    return render_template('csr/match.html', pins=pins)

@csr_bp.route('/pin/<int:pin_id>')
def view_pin(pin_id):
    pins = RC.get_incomplete_requests()
    pin = next((p for p in pins if p.request_id == pin_id), None)
    return render_template('csr/pin_detail.html', pin=pin)

@csr_bp.route('/pin/<int:pin_id>/candidates')
def view_candidates(pin_id):
    candidates = RC.find_candidates(pin_id)
    ranked = RC.rank_candidates(pin_id, candidates)
    return render_template('csr/candidates.html', pin_id=pin_id, candidates=ranked)

@csr_bp.route('/assign', methods=['POST'])
def assign_volunteer():
    pin_id = int(request.form.get('pin_id'))
    user_id = int(request.form.get('user_id'))
    match = RC.assign_user(pin_id, user_id)
    if match:
        RC.notify_parties(match)
        flash('Volunteer assigned successfully!', 'success')
        return redirect(url_for('csr.success', match_id=match.match_id))
    flash('Assignment failed.', 'danger')
    return redirect(url_for('csr.match_page'))

@csr_bp.route('/success/<int:match_id>')
def success(match_id):
    return render_template('csr/confirm.html', match_id=match_id)
