import pytest
import sys
import os
from datetime import datetime, timedelta

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

# helper function to create ticket
def create_ticket(title, priority, employee_id, created_at=None):
    # set ticket parameters
    ticket = Ticket(
        title=title,
        description="Description",
        priority=priority,
        employeeID=employee_id,
        isAssigned=False,
        isComplete=False
    )
    
    if created_at:
        ticket.created_at = created_at
        
    # add to db
    db.session.add(ticket)
    db.session.commit()
    db.session.refresh(ticket)
    
    return ticket

# login helper function
def login(client, user):
    with client.session_transaction() as session:
        session['user_id'] = user.userID
        session['role'] = user.role

# test redirect to login page if not logged in
def test_get_tickets_unauthorized(client):
    # act
    # go to /tickets page
    response = client.get('/tickets/', follow_redirects=False)
    
    # assert
    # check if returns 302
    assert response.status_code == 302
    # check if redirects to login page
    assert '/auth/login' in response.headers['Location']

# test that employees only see their own tickets
def test_get_tickets_employee_filter(client):
    # arrange
    with app.app_context():
        # create employee 1
        employee1 = create_user('employee1', 'employee')
        # create employee 2
        employee2 = create_user('employee2', 'employee')
        
        # act
        # create ticket 1 with employee 1 id
        ticket1 = create_ticket('Ticket 1', 'Low', employee1.userID)
        
        # create ticket 2 with emlpoyee 2 id
        ticket2 = create_ticket('Ticket 2', 'High', employee2.userID)
        
        # login with employee 1
        login(client, employee1)
        
    # assert
    # go to /tickets page
    response = client.get('/tickets/')
    
    # check if page does not redirect
    assert response.status_code == 200
    # get data
    data = response.get_data(as_text=True)
    
    # check if employee 1 can see their own ticket, "Ticket 1"
    assert "Ticket 1" in data
    
    # check if employee 1 cannot see "Ticket 2"
    assert "Ticket 2" not in data

# check if technicians can view all tickets from all employees
def test_get_tickets_technician_view_all(client):
    # arrange
    with app.app_context():
        # create technician user
        tech = create_user('tech', 'technician')
        
        # create employee 1
        employee1 = create_user('employee1', 'employee')
        # create employee 2
        employee2 = create_user('employee2', 'employee')
        
        # act
        # create ticket by employee 1
        ticket1 = create_ticket('Ticket 1', 'Low', employee1.userID)
        # create ticket by emplyee 2
        ticket2 = create_ticket('Ticket 2', 'High', employee2.userID)
        
        # login with technician
        login(client, tech)

    # assert
    # go to /tickets
    response = client.get('/tickets/')
    
    # check if page returns 200
    assert response.status_code == 200
    # get data
    data = response.get_data(as_text=True)
    
    # check if ticket 1 and 2 are in data
    assert 'Ticket 1' in data
    assert 'Ticket 2' in data

# test filtering by title
def test_filter_by_title(client):
    # arrange
    with app.app_context():
        # create technician account
        tech = create_user('tech', 'technician')
        
        # create employee account
        employee1 = create_user('employee1', 'employee')
        
        # act
        # create tickets by employee 1
        create_ticket('Network Issue', 'High', employee1.userID)
        create_ticket('Printer Broken', 'Low', employee1.userID)
        
        # login with technician
        login(client, tech)

    # Search for "net"
    response = client.get('/tickets/?title=net')
    
    # assert
    # check if response returns 200
    assert response.status_code == 200
    # get data
    data = response.get_data(as_text=True)
    
    # check if "Network Issue" ticket is in data after filtering
    assert 'Network Issue' in data
    # check if "Printer Broken" is not in data after filtering
    assert 'Printer Broken' not in data

# test filtering tickets by critical priority
def test_filter_by_priority_critical(client):
    # arrange
    with app.app_context():
        # create technician
        tech = create_user('tech', 'technician')
        # create employee 1
        employee1 = create_user('employee1', 'employee')
        
        # act
        # critical tickets with different priority levels
        create_ticket("Critical Bug", "Critical", employee1.userID)
        create_ticket("High Bug", "High", employee1.userID)
        create_ticket("Med Bug", "Medium", employee1.userID)
        create_ticket("Low Bug", "Low", employee1.userID)
        
        login(client, tech)

    # assert
    # Filter by "Critical"
    response = client.get('/tickets/?priority=Critical')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    assert "Critical Bug" in data
    assert "High Bug" not in data
    assert "Med Bug" not in data
    assert "Low Bug" not in data
    
# test filtering tickets by high priority
def test_filter_by_priority_high(client):
    # arrange
    with app.app_context():
        # create technician
        tech = create_user('tech', 'technician')
        # create employee 1
        employee1 = create_user('employee1', 'employee')
        
        # act
        # critical tickets with different priority levels
        create_ticket("Critical Bug", "Critical", employee1.userID)
        create_ticket("High Bug", "High", employee1.userID)
        create_ticket("Med Bug", "Medium", employee1.userID)
        create_ticket("Low Bug", "Low", employee1.userID)
        
        login(client, tech)

    # assert
    # Filter by "High"
    response = client.get('/tickets/?priority=High')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    assert "Critical Bug" not in data
    assert "High Bug" in data
    assert "Med Bug" not in data
    assert "Low Bug" not in data
    
# test filtering tickets by critical priority
def test_filter_by_priority_medium(client):
    # arrange
    with app.app_context():
        # create technician
        tech = create_user('tech', 'technician')
        # create employee 1
        employee1 = create_user('employee1', 'employee')
        
        # act
        # critical tickets with different priority levels
        create_ticket("Critical Bug", "Critical", employee1.userID)
        create_ticket("High Bug", "High", employee1.userID)
        create_ticket("Med Bug", "Medium", employee1.userID)
        create_ticket("Low Bug", "Low", employee1.userID)
        
        login(client, tech)

    # assert
    # Filter by "Medium"
    response = client.get('/tickets/?priority=Medium')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    assert "Critical Bug" not in data
    assert "High Bug" not in data
    assert "Med Bug" in data
    assert "Low Bug" not in data
    
# test filtering tickets by low priority
def test_filter_by_priority_low(client):
    # arrange
    with app.app_context():
        # create technician
        tech = create_user('tech', 'technician')
        # create employee 1
        employee1 = create_user('employee1', 'employee')
        
        # act
        # critical tickets with different priority levels
        create_ticket("Critical Bug", "Critical", employee1.userID)
        create_ticket("High Bug", "High", employee1.userID)
        create_ticket("Med Bug", "Medium", employee1.userID)
        create_ticket("Low Bug", "Low", employee1.userID)
        
        login(client, tech)

    # assert
    # Filter by "Critical"
    response = client.get('/tickets/?priority=Low')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    assert "Critical Bug" not in data
    assert "High Bug" not in data
    assert "Med Bug" not in data
    assert "Low Bug" in data

# test sorting tickets by ascending
def test_sort_tickets_asc(client):
    # arrange
    with app.app_context():
        tech = create_user('tech', 'technician')
        employee1 = create_user('employee1', 'employee')
        
        # act
        ticket1 = create_ticket('abc', 'Low', employee1.userID)
        ticket2 = create_ticket('xyz', 'High', employee1.userID)
        
        login(client, tech)

    # assert
    # Sort by title ASC
    response = client.get('/tickets/?sort_by=title&order=asc')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    # Check if ticket name with "abc" appears before "xyz"
    assert data.find('abc') < data.find('xyz')
    
# test sorting tickets by descending
def test_sort_tickets_desc(client):
    # arrange
    with app.app_context():
        tech = create_user('tech', 'technician')
        employee1 = create_user('employee1', 'employee')
        
        # act
        ticket1 = create_ticket('abc', 'Low', employee1.userID)
        ticket2 = create_ticket('xyz', 'High', employee1.userID)
        
        login(client, tech)

    # assert
    # Sort by title DESC
    response = client.get('/tickets/?sort_by=title&order=desc')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    # check if "xyz" appears before "abc"
    assert data.find('xyz') < data.find('abc')

# test page splitting
def test_page1_display(client):
    # arrange
    with app.app_context():
        tech = create_user('tech', 'technician')
        employee1 = create_user('employee1', 'employee')
        
        # act
        # Create 25 tickets
        for i in range(25):
            create_ticket(f'Ticket {i}', 'Low', employee1.userID)
        
        login(client, tech)

    # assert
    # got to tickets page 1
    response = client.get('/tickets/?page=1')
    assert response.status_code == 200
    # get data
    data = response.get_data(as_text=True)
    
    # page 1 only has ticket 0 to 19
    # check if ticket 0 and 19 are on page 1
    assert 'Ticket 0' in data
    assert 'Ticket 19' in data
    # check if ticket 24 is not in page 1
    assert 'Ticket 24' not in data
    
# test page splitting
def test_page2_display(client):
    # arrange
    with app.app_context():
        tech = create_user('tech', 'technician')
        employee1 = create_user('employee1', 'employee')
        
        # act
        # Create 25 tickets
        for i in range(25):
            create_ticket(f'Ticket {i}', 'Low', employee1.userID)
        
        login(client, tech)

    # assert
    # got to tickets page 2
    response = client.get('/tickets/?page=2')
    assert response.status_code == 200
    # get data
    data = response.get_data(as_text=True)
    
    # page 1 only has ticket 0 to 19
    # check if ticket 0 and 19 are not on page 1
    assert 'Ticket 0' not in data
    assert 'Ticket 19' not in data
    # check if ticket 24 is in page 1
    assert 'Ticket 24'  in data
