from database import db
from models import User, Ticket
from faker import Faker
import random
import os

fake = Faker()

def seed_data():
    print("--- SEEDING DATABASE ---")
    
    # drop all existing tables
    db.drop_all()
    
    # create all tables
    db.create_all()

    print("Generating 500 random Users")
    
    users = []
    
    # generate 50 technicians
    for i in range(50):
        users.append(User(name=fake.name(), password='123', role='technician'))

    # generate 450 Employees
    for i in range(450):
        users.append(User(name=fake.name(), password='123', role='employee'))

    # add users to db
    db.session.add_all(users)
    db.session.commit()

    # Get valid id that belongs to an employee
    # use the id to assign to random ticket
    employee_ids = [u.userID for u in User.query.filter_by(role='employee').all()]

    print("Generating 1000 Tickets...")
    tickets = []
    
    # generate 1000 fake tickets
    for i in range(1000):
        # 50% chance of image blob (1KB)
        image_blob = os.urandom(1024) if i % 2 == 0 else None
        
        tickets.append(Ticket(
            title=fake.sentence(nb_words=4),
            description=fake.text(),
            priority=random.choice(['Low', 'Medium', 'High', 'Critical']),
            employeeID=random.choice(employee_ids),
            image=image_blob
        ))

    # add tickets to db
    db.session.add_all(tickets)
    db.session.commit()
    print("--- SEEDING COMPLETE ---")