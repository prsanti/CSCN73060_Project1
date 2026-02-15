from flask import Blueprint, render_template, request, jsonify, session
from modules.database.database import db
from models import User 
from flask import redirect

auth_bp = Blueprint('auth', __name__)

# --- LOGIN ROUTE ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('auth/login.html')

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
            return jsonify({'message': 'Login successful', 'redirect': '/auth/dashboard'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

# --- SIGN UP ROUTE ---
@auth_bp.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    # 1. GET: Show the Sign Up page
    if request.method == 'GET':
        return render_template('auth/sign_up.html')
    
    # 2. POST: Create the User
    if request.method == 'POST':
        data = request.get_json()
        
        # Validation
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username and/or password'}), 400
        
        username = data['username']
        password = data['password']
        
        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Create new user 
        new_user = User(username=username, password=password, role='employee')
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': 'User created successfully', 'redirect': '/auth/login'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Database error'}), 500

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # 1. Clear the session (removes user_id and role)
    session.clear()
    
    # 2. Return success and tell frontend where to go
    return jsonify({'message': 'Logged out successfully', 'redirect': '/auth/login'}), 200

#Dashboard route for testing purposes. Will implement real dashboard later
@auth_bp.route('/dashboard', methods=['GET'])
def dashboard():
	# Ensure user is logged in
	if 'user_id' not in session:
		return jsonify({'error': 'Unauthorized'}), 401
	
	return redirect('/tickets')