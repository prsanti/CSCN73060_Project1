from modules.database.database import db
from models import User, Ticket
from faker import Faker
import random
import os

fake = Faker()

def load_images(files):
    images = []
    
    base_dir = os.path.dirname(__file__)
    # set directory to images
    images_dir = os.path.join(base_dir, 'images')
    
    for fname in files:
        # set directory path
        full_path = os.path.join(images_dir, fname)
        
        try:
            with open(full_path, 'rb') as f:
                images.append(f.read())
                print(f"Loaded {fname} successfully.")
        except FileNotFoundError:
            print(f"WARNING: {fname} not found.")
    
    return images

def seed_data():
    print("--- SEEDING DATABASE ---")
    
    # load test images
    target_files = ['test-img.png', 'test-img-2.jpg']
    images = load_images(target_files)
    
    # create random binary if images do not load
    if not images:
        print("No real images found. Using random noise as fallback.")
        images.append(os.urandom(1024))
    
    # drop all existing tables
    db.drop_all()
    
    # create all tables
    db.create_all()

    print("Generating 500 random Users")
    
    users = []
    
    # manually create technician and employee accounts for testing
    test_user = User(username='testguy', password='123', role='technician')
    users.append(test_user)
    
    test_employee_user = User(username='testemployee', password='123', role='employee')
    users.append(test_employee_user)
   
    # generate 50 technicians
    for i in range(50):
        users.append(User(username=fake.name(), password='123', role='technician'))

    # generate 450 Employees
    for i in range(450):
        users.append(User(username=fake.name(), password='123', role='employee'))

    # add users to db
    db.session.add_all(users)
    db.session.commit()

    # Get valid id that belongs to an employee
    # use the id to assign to random ticket
    employee_ids = [u.userID for u in User.query.filter_by(role='employee').all()]
    technician_ids = [u.userID for u in User.query.filter_by(role='technician').all()]
    
    # Get specific IDs for testing
    test_technician_id = User.query.filter_by(username='testguy').first().userID
    test_employee_id = User.query.filter_by(username='testemployee').first().userID

    print("Generating 1000 Tickets...")
    tickets = []
    
    # create specific tickets for testemployee
    # Completed ticket
    tickets.append(Ticket(
        title="Test Employee Completed Ticket",
        description="This is a completed ticket created by testemployee.",
        priority="Low",
        employeeID=test_employee_id,
        technicianID=test_technician_id,
        isAssigned=True,
        isComplete=True
    ))
    
    # Unassigned ticket
    tickets.append(Ticket(
        title="Test Employee Unassigned Ticket",
        description="This is an unassigned ticket created by testemployee.",
        priority="Medium",
        employeeID=test_employee_id,
        isAssigned=False,
        isComplete=False
    ))
    
    # Assigned to testguy ticket
    tickets.append(Ticket(
        title="Test Employee Assigned Ticket",
        description="This ticket is assigned to testguy.",
        priority="High",
        employeeID=test_employee_id,
        technicianID=test_technician_id,
        isAssigned=True,
        isComplete=False
    ))
    
    # generate 1000 fake tickets
    for i in range(1000):
        image_blob = None
      
        # 50% of tickets have a random image
        if i % 2 == 0:
            image_blob = random.choice(images)
            
        isComplete = False
        
        # 33% of tickets are completed
        if i % 3 == 0:
            isComplete = True
        
        technicianID = None
        isAssigned = False
        
        # 70% of tickets assigned to random technician
        if random.random() < 0.7:
            technicianID = random.choice(technician_ids)
            isAssigned = True

        tickets.append(Ticket(
            # generate random title
            title=fake.sentence(nb_words=4),
            # random text
            description=fake.text(),
            priority=random.choice(['Low', 'Medium', 'High', 'Critical']),
            employeeID=random.choice(employee_ids),
            technicianID=technicianID,
            isAssigned=isAssigned,
            image=image_blob,
            isComplete=isComplete
        ))

    # add tickets to db
    db.session.add_all(tickets)
    db.session.commit()
    print("--- SEEDING COMPLETE ---")