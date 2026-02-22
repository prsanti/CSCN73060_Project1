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
    user = User(username=username, password='123', role=role)
    
    # add to db
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    
    return user

# login helper function
def login(client, user):
    with client.session_transaction() as session:
        session['user_id'] = user.userID
        session['role'] = user.role
        
# test create ticket route
def test_create_ticket_route(client):
    # arrange
    with app.app_context():
        # create employee
        employee = create_user('employee', 'employee')
        
        # login with employee
        login(client, employee)
        
    # act
    response = client.post('/tickets/', data={
        'title': 'New Ticket',
        'description': 'Description',
        'priority': 'low'
    })
    
    # assert
    assert response.status_code == 201
    assert response.json['message'] == 'Ticket created successfully'
    assert 'ticket_id' in response.json