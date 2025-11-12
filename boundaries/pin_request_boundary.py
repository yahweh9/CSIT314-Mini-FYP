# boundaries/pin_request_boundary.py
from flask import request, session, redirect, url_for, render_template, flash
from controllers.PINRequestController import PINRequestController
from controllers.CategoryController import CategoryController
from entities.UserEntity import UserEntity

def display_create_request_form():
    """Display the request creation form"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    categories = CategoryController.list_categories()
    
    print("📂 Categories fetched:", categories) #DELETE
    return render_template('pin_create_request.html', user=user, categories=categories)

def handle_create_request():
    """Handle request creation form submission"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    if PINRequestController.create_request():
        return redirect(url_for('pin_my_requests'))
    else:
        return redirect(url_for('pin_create_request'))

def display_my_requests():
    """Display user's active requests"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    active_requests = PINRequestController.get_active_requests(session['user_id'])
    
    return render_template('pin_my_requests.html', user=user, requests=active_requests)

#made changes to the content to allow filter mechanism
def display_request_history():
    """Display PIN's completed request history with filters."""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')

    pin_id = session['user_id']
    user = UserEntity.query.get(pin_id)

    # Collect filters from query params
    service_type = request.args.get('service_type', '').strip()
    status = request.args.get('status', '').strip()
    date = request.args.get('date', '').strip()

    # Fetch all service types (same as create request form)
    categories = CategoryController.list_categories()
    service_types = [c.name for c in categories]

    try:
        requests = PINRequestController.get_completed_requests_with_filters(
            pin_id=pin_id,
            service_type=service_type or None,
            status=status or None,
            date=date or None
        )
    except Exception:
        flash("Unable to retrieve request history. Please try again later.", "warning")
        requests = []

    message = None
    if not requests:
        message = "No requests available." if not (service_type or status or date) else "No results match your filters."

    return render_template(
        'pin_request_history.html',
        user=user,
        requests=requests,
        categories=categories,      # for dropdown
        service_types=service_types,
        service_type=service_type,
        status=status,
        date=date,
        message=message
    )

def display_request_detail(request_id):
    """Display detailed view of a specific request"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')
    
    user = UserEntity.query.get(session['user_id'])
    request_obj = PINRequestController.get_request_by_id(request_id, session['user_id'])
    
    if not request_obj:
        flash('Request not found', 'error')
        return redirect(url_for('pin_my_requests'))
    
    return render_template('pin_request_detail.html', user=user, request=request_obj)

def handle_edit_request(request_id):
    """Display and handle editing a request"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')

    request_obj = PINRequestController.get_request_by_id(request_id, session['user_id'])
    if not request_obj:
        flash('Request not found', 'error')
        return redirect(url_for('pin_my_requests'))

    if request.method == 'POST':
        success = PINRequestController.update_request(request_id, request.form, session['user_id'])
        if success:
            return redirect(url_for('pin_request_detail', request_id=request_id))
        else:
            return redirect(url_for('pin_edit_request', request_id=request_id))

    # GET → show edit form
    return render_template('pin_edit_request.html', request=request_obj)

def handle_cancel_request(request_id):
    """Handle cancelling a request (soft delete)"""
    if 'user_id' not in session or session.get('role') != 'pin':
        return redirect('/')

    success = PINRequestController.cancel_request(request_id, session['user_id'])
    if success:
        return redirect(url_for('pin_my_requests'))
    else:
        return redirect(url_for('pin_request_detail', request_id=request_id))