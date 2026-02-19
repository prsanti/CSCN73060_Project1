from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import case, asc, desc
from modules.database.database import db
from models import Ticket
from functools import wraps
from flask import abort

ticket_bp = Blueprint('tickets', __name__)

# get all tickets
@ticket_bp.route('/', methods=['GET'])
def get_tickets():
    # check if user is logged in else redirect to login page
    if 'user_id' not in session:
        return redirect(url_for('auth.login')), 302
        
    # query all tickets
    query = Ticket.query

    # If user is an employee, only show their tickets
    if session.get('role') == 'employee':
        query = query.filter(Ticket.employeeID == session.get('user_id'))

    # search for title query
    title_query = request.args.get('title')
    if title_query:
        query = query.filter(Ticket.title.ilike(f'%{title_query}%'))

    # filter by priority
    priority_query = request.args.get('priority')
    if priority_query:
        query = query.filter(Ticket.priority == priority_query)

    # sort by and order
    # default by date and desc
    sort_by = request.args.get('sort_by', 'date')  # default to date for sorting
    order = request.args.get('order', 'asc')      # default to aescending

    # sort by column
    if sort_by == 'title':
        sort_column = Ticket.title
    elif sort_by == 'priority':
        sort_column = Ticket.priority
    elif sort_by == 'id':
        sort_column = Ticket.ticketID
    else:
        sort_column = Ticket.created_at # Default


    # get query by column
    if order == 'desc':
        # apply desc
        query = query.order_by(desc(sort_column))
    else:
        # apply asc
        query = query.order_by(asc(sort_column))

    # get query
    tickets = query.all()

    # input sort_by and order to html
    return render_template('tickets.html', tickets=tickets, sort_by=sort_by, order=order), 200


@ticket_bp.route('/createtickets', methods=['POST'])
def createtickets():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.form 
    
    image_file = request.files.get('image')
    image_blob = image_file.read() if image_file else None

    new_ticket = Ticket(
        employeeID=session['user_id'],
        title=data.get('title'),
        description=data.get('description'),
        priority=data.get('priority', 'Medium'),
        image=image_blob
    )

    db.session.add(new_ticket)
    db.session.commit()
    
    return jsonify({"message": "Ticket created", "ticket": new_ticket.to_dict()}), 201

@ticket_bp.route('/<int:ticket_id>', methods=['PATCH'])
def update_ticket(ticket_id):
    """PATCH: Partial updates (claiming or completing)."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()

 
    if 'claim' in data and data['claim'] is True:
        ticket.technicianID = session['user_id']
        ticket.isAssigned = True
    

    if 'isComplete' in data:
        ticket.isComplete = data['isComplete']

    if 'priority' in data:
        ticket.priority = data['priority']

    db.session.commit()
    return jsonify({"message": "Ticket updated via PATCH", "ticket": ticket.to_dict()})

@ticket_bp.route('/', methods=['DELETE'])
def delete_ticket():
    if 'user_id' not in session:
        return redirect(url_for('auth.login')), 401
        
    ticket = Ticket.query(Ticket.ticketID)
    user = session.get('user_id')
    if session.get('role') == 'employee':
        query = session.get


    
    
    db.session.delete(ticket)
    db.session.commit()
    
    return jsonify({"message": f"Ticket {Ticket.ticketID} deleted"}), 200
    
@ticket_bp.route('/<int:ticket_id>', methods=['PUT'])
def replace_ticket(ticket_id):
    """PUT: Replaces the entire resource."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()

    ticket.title = data.get('title')
    ticket.description = data.get('description')
    ticket.priority = data.get('priority')
    
    db.session.commit()
    return jsonify({"message": "Ticket updated via PUT", "ticket": ticket.to_dict()})