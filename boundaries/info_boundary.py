# boundaries/info_boundary.py
from flask import render_template
from controllers.GuestInfoController import GuestInfoController

def display_homepage():
    info = GuestInfoController.fetch_platform_info()
    return render_template('homepage.html', info=info)

def display_csr_mission():
    csr_details = GuestInfoController.present_csr_details()
    return render_template('csr_mission.html', csr=csr_details)