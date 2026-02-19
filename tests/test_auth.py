import pytest
import sys
import os

# import app directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from app import app
from modules.database.database import db
from models import Ticket, User
from flask import session

# create client for testing
@pytest.fixture
def client():
    # configure app
    # set to testing
    app.config['TESTING'] = True
    # use test db uri
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    # set test client
    with app.test_client() as client:
        with app.app_context():
            # create test database
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

# helper function to create user
def create_user(username, role):
    user = User(username=username, password='12345678', role=role)
    
    # add to db
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    
    return user
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
def is_user_in_db(username):
    user = User.query.filter_by(username=username).first()
    return user is not None

def test_signup_user_created(client):
    # test signup page
    response = client.get('/auth/sign_up')
    assert response.status_code == 200

    # test signup form submission
    response = client.post('/auth/sign_up', json={
        'username': 'Maksym',
        'password': '12345678',
    }, follow_redirects=True)
    
    assert response.status_code == 201
    assert is_user_in_db('Maksym') == True
    delete_user('Maksym')

def test_signup_duplicate_username(client):
    # create user
    create_user('Maksym', 'employee')

    # test duplicate username
    response = client.post('/auth/sign_up', json={
        'username': 'Maksym', 'password': '12345678'}, follow_redirects=True)
    assert response.status_code == 409
    assert is_user_in_db('Maksym') == True
    delete_user('Maksym')

def test_signup_missing_fields(client):
    response = client.post('/auth/sign_up', json={'no_username': 'Maksym', 'no_password':'12345678'}, follow_redirects=True)
    assert response.status_code == 400

def test_login_success(client):
    # create user
    create_user('Maksym', 'employee')

    # test login page
    response = client.get('/auth/login')
    assert response.status_code == 200

    # test login form submission
    response = client.post('/auth/login', json={
        'username': 'Maksym',
        'password': '12345678',
    }, follow_redirects=True)
    
    assert response.status_code == 200
    delete_user('Maksym')

def test_login_invalid_credentials(client):
    # create user
    create_user('Maksym', 'employee')

    # test login with wrong password
    response = client.post('/auth/login', json={
        'username': 'Maksym',
        'password': 'wrongpassword'}, follow_redirects=True)
    assert response.status_code == 401
    delete_user('Maksym')

def test_login_missing_fields(client):
    response = client.post('/auth/login', json={'no_username': 'Maksym', 'no_password':'12345678'}, follow_redirects=True)
    assert response.status_code == 400

# integration tests 
def test_signup_and_login(client):
    # test signup
    response = client.post('/auth/sign_up', json={
        'username': 'Maksym', 'password': '12345678'}, follow_redirects=True)
    assert response.status_code == 201
    assert is_user_in_db('Maksym') == True
    # test login
    response = client.post('/auth/login', json={
        'username': 'Maksym', 'password': '12345678'}, follow_redirects=True)
    assert response.status_code == 200
    delete_user('Maksym')

def test_login_and_logout(client):
    # create user
    create_user('Maksym', 'employee')
    # test login
    response = client.post('/auth/login', json={'username': 'Maksym', 'password': '12345678'}, follow_redirects=True)
    assert response.status_code == 200
    # test logout
    response = client.post('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    # check session cleared
    with client.session_transaction() as session_test:
        assert 'user_id' not in session_test
        assert 'role' not in session_test
    delete_user('Maksym')

