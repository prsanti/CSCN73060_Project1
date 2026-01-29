from modules.database.database import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'

    ticketID = db.Column(db.Integer, primary_key=True)
    employeeID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=False)
    technicianID = db.Column(db.Integer, db.ForeignKey('users.userID'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.Enum('Low', 'Medium', 'High', 'Critical', name='ticket_priority'), default='Medium')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Large Binary = Blob
    image = db.Column(db.LargeBinary, nullable=True)

    isAssigned = db.Column(db.Boolean, default=False)
    
    isComplete = db.Column(db.Boolean, default=False)

    # relationship helpers
    employee = db.relationship('User', foreign_keys=[employeeID], backref='created_tickets')
    technician = db.relationship('User', foreign_keys=[technicianID], backref='assigned_tickets')

    def to_dict(self):
        return {
            "ticketID": self.ticketID,
            "employeeID": self.employeeID,
            "technicianID": self.technicianID,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "isAssigned": self.isAssigned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "isComplete": self.isComplete,
        }