from flask import Blueprint, render_template, request, jsonify, session, url_for
from modules.database.database import db
from models import User 

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    
    # 1. Login GET: Show the login page
    if request.method == 'GET':
        # FIX: Point directly to the file inside the templates folder
        return render_template('auth/login.html')

    # 2. Login POST: Process credentials
    if request.method == 'POST':
        data = request.get_json()

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing credentials'}), 400 

        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            session.clear()
            session['user_id'] = user.userID
            session['role'] = user.role
        
            # Return a JSON object with the URL for the frontend to handle.
            return jsonify({'message': 'Login successful', 'redirect': '/dashboard'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
