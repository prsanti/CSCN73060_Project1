import pytest
import sys
import os
import io

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
    app.config['TESTING'] = True
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
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user

# helper function to create ticket
def create_ticket(title, priority, employee_id, image_data=None):
    ticket = Ticket(
        title=title,
        description="Description",
        priority=priority,
        employeeID=employee_id,
        isAssigned=False,
        isComplete=False,
        image=image_data
    )
    db.session.add(ticket)
    db.session.commit()
    db.session.refresh(ticket)
    return ticket

# login helper function
def login(client, user):
    with client.session_transaction() as session:
        session['user_id'] = user.userID
        session['role'] = user.role

# Tests for GET /<int:ticket_id> (get_ticket_detail)
# not logged in user test
def test_get_ticket_detail_unauthorized(client):
    response = client.get('/tickets/1')
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']

# authorized employee test
def test_get_ticket_detail_success(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        ticket = create_ticket('Test Ticket', 'low', user.userID)
        login(client, user)
        ticket_id = ticket.ticketID

    response = client.get(f'/tickets/{ticket_id}')
    assert response.status_code == 200
    assert b'Test Ticket' in response.data

# test if ticket does not exist
def test_get_ticket_detail_not_found(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        login(client, user)

    response = client.get('/tickets/999')
    # Should redirect to tickets list if not found
    assert response.status_code == 302
    assert '/tickets' in response.headers['Location']

# test deleted ticket
def test_get_ticket_detail_deleted(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        ticket = create_ticket('Deleted Ticket', 'low', user.userID)
        ticket.is_deleted = True
        db.session.commit()
        login(client, user)
        ticket_id = ticket.ticketID

    response = client.get(f'/tickets/{ticket_id}')
    assert response.status_code == 302
    assert '/tickets' in response.headers['Location']

# test options route
def test_ticket_options(client):
    response = client.open('/tickets/1', method='OPTIONS')
    assert response.status_code == 200
    assert response.json['resource'] == 'Ticket'
    assert 'GET' in response.headers['Access-Control-Allow-Methods']


# Tests for PATCH /<int:ticket_id> (update_ticket)
# test not logged in user trying to patch a ticket
def test_update_ticket_unauthorized(client):
    response = client.patch('/tickets/1', json={'description': 'New desc'})
    assert response.status_code == 401

# test update ticket as user
def test_update_ticket_success(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        ticket = create_ticket('Test Ticket', 'low', user.userID)
        login(client, user)
        ticket_id = ticket.ticketID

    data = {'description': 'Updated Description', 'priority': 'high'}
    response = client.patch(f'/tickets/{ticket_id}', json=data)
    assert response.status_code == 200
    assert response.json['message'] == 'Ticket updated successfully'

    with app.app_context():
        updated_ticket = Ticket.query.get(ticket_id)
        assert updated_ticket.description == 'Updated Description'
        assert updated_ticket.priority == 'high'

# test if no changes when updating
def test_update_ticket_invalid_priority(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        ticket = create_ticket('Test Ticket', 'low', user.userID)
        login(client, user)
        ticket_id = ticket.ticketID

    data = {'priority': 'invalid_priority'}
    response = client.patch(f'/tickets/{ticket_id}', json=data)
    
    # If no valid fields are updated, it returns 400 'No changes provided'
    assert response.status_code == 400
    assert response.json['message'] == 'No changes provided'

def test_update_ticket_other_user(client):
    with app.app_context():
        owner = create_user('owner', 'employee')
        other = create_user('other', 'employee')
        ticket = create_ticket('Test Ticket', 'low', owner.userID)
        
        login(client, other)
        ticket_id = ticket.ticketID

    # Employee trying to update another employee's ticket
    response = client.patch(f'/tickets/{ticket_id}', json={'description': 'Hacked'})
    # Returns 404 because the query filters by employeeID
    assert response.status_code == 404

# test if updating as technician account
def test_update_ticket_as_technician(client):
    with app.app_context():
        owner = create_user('owner', 'employee')
        tech = create_user('tech', 'technician')
        ticket = create_ticket('Test Ticket', 'low', owner.userID)
        
        login(client, tech)
        ticket_id = ticket.ticketID

    response = client.patch(f'/tickets/{ticket_id}', json={'priority': 'critical'})
    assert response.status_code == 200
    
    with app.app_context():
        updated_ticket = Ticket.query.get(ticket_id)
        assert updated_ticket.priority == 'critical'

# Tests for PUT /<int:ticket_id>/assign (assign_ticket)
# test assign ticket not logged in
def test_assign_ticket_unauthorized(client):
    response = client.put('/tickets/1/assign')
    assert response.status_code == 401

def test_assign_ticket_as_employee(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        ticket = create_ticket('Test Ticket', 'low', user.userID)
        login(client, user)
        ticket_id = ticket.ticketID

    response = client.put(f'/tickets/{ticket_id}/assign')
    assert response.status_code == 403
    assert 'Only technicians' in response.json['error']

# test assigning ticket as technician
def test_assign_ticket_success(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        tech = create_user('tech', 'technician')
        ticket = create_ticket('Test Ticket', 'low', user.userID)
        
        login(client, tech)
        ticket_id = ticket.ticketID
        tech_id = tech.userID

    response = client.put(f'/tickets/{ticket_id}/assign')
    assert response.status_code == 200
    
    with app.app_context():
        assigned_ticket = Ticket.query.get(ticket_id)
        assert assigned_ticket.technicianID == tech_id
        assert assigned_ticket.isAssigned is True

# Tests for DELETE /<int:ticket_id> (delete_ticket)
# test delete if not logged in
def test_delete_ticket_unauthorized(client):
    response = client.delete('/tickets/1')
    assert response.status_code == 401

# test delete as employee
def test_delete_ticket_success(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        ticket = create_ticket('Test Ticket', 'low', user.userID)
        login(client, user)
        ticket_id = ticket.ticketID

    response = client.delete(f'/tickets/{ticket_id}')
    assert response.status_code == 200
    
    with app.app_context():
        deleted_ticket = Ticket.query.get(ticket_id)
        assert deleted_ticket.is_deleted is True

# test delete as a different employee than creator
def test_delete_ticket_other_user(client):
    with app.app_context():
        owner = create_user('owner', 'employee')
        other = create_user('other', 'employee')
        ticket = create_ticket('Test Ticket', 'low', owner.userID)
        
        login(client, other)
        ticket_id = ticket.ticketID

    response = client.delete(f'/tickets/{ticket_id}')
    # Should return 404 because query filters by employeeID
    assert response.status_code == 404

# test delete as a technician
def test_delete_ticket_as_technician(client):
    with app.app_context():
        owner = create_user('owner', 'employee')
        tech = create_user('tech', 'technician')
        ticket = create_ticket('Test Ticket', 'low', owner.userID)
        
        login(client, tech)
        ticket_id = ticket.ticketID

    response = client.delete(f'/tickets/{ticket_id}')
    assert response.status_code == 200
    
    with app.app_context():
        deleted_ticket = Ticket.query.get(ticket_id)
        assert deleted_ticket.is_deleted is True


# Tests for GET /<int:ticket_id>/image (get_ticket_image)
# test get ticket image
def test_get_ticket_image_success(client):
    with app.app_context():
        user = create_user('user1', 'employee')
        # Create a dummy image
        img_data = b'fake_image_data'
        # create new ticket with image
        ticket = create_ticket('Image Ticket', 'low', user.userID, image_data=img_data)
        ticket_id = ticket.ticketID

    response = client.get(f'/tickets/{ticket_id}/image')
    assert response.status_code == 200
    assert response.data == b'fake_image_data'

#  test image that does not exist
def test_get_ticket_image_not_found(client):
    # Tests a ticket that exists but has no image
    with app.app_context():
        user = create_user('user1', 'employee')
        # create ticket with no image
        ticket = create_ticket('No Image Ticket', 'low', user.userID, image_data=None)
        ticket_id = ticket.ticketID

    response = client.get(f'/tickets/{ticket_id}/image')
    assert response.status_code == 500
    assert response.json['error'] == 'Cannot upload image'
