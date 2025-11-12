# boundaries/platform_manager_boundary.py

from flask import session, redirect, url_for
from controllers.PlatformManagerController import PlatformManagerController

def display_dashboard_platform_manager():
    """
    Boundary for the Platform Manager dashboard.
    Delegates heavy lifting to the PlatformManagerController.
    """
    # Ensure user is logged in and has correct role
    if 'username' not in session:
        return redirect('/')
    if session.get('role') != 'pm':  # adjust role name if yours differs
        return redirect(url_for('login_page'))

    # Render the full dashboard (categories + PIN requests)
    return PlatformManagerController.display_dashboard()
