import io
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file, make_response

from sqlalchemy import case, asc, desc
from modules.database.database import db
from models import Ticket
from sqlalchemy.orm import defer

ticket_bp = Blueprint('tickets', __name__)

# get all tickets
@ticket_bp.route('/', methods=['GET'])
def get_tickets():
    # check if user is logged in else redirect to login page
    if 'user_id' not in session:
        return redirect(url_for('auth.login')), 302
        
    # query all tickets
    #defer (lazy load) ticket images to increase performance
    # only show non deleted tickets
    query = Ticket.query.filter(Ticket.is_deleted == False).options(defer(Ticket.image))

    # If user is an employee, only show their tickets
    if session.get('role') == 'employee':
        query = query.filter(Ticket.employeeID == session.get('user_id'))

    # search for title query
    title_query = request.args.get('title')
    if title_query:
        query = query.filter(Ticket.title.ilike(f'%{title_query}%'))

    # filter by priority
    #altered to utilize database indexes
    priority_query = request.args.get('priority')
    if priority_query:
        query = query.filter(Ticket.priority == priority_query.lower())

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

    # Pagination
    per_page = 20
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1

    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    if total_pages < 1:
        total_pages = 1
    if page > total_pages:
        page = total_pages

    tickets = query.offset((page - 1) * per_page).limit(per_page).all()

    start_item = 0 if total == 0 else (page - 1) * per_page + 1
    end_item = min(page * per_page, total)

    # input sort_by and order to html
    return render_template('tickets.html', tickets=tickets, sort_by=sort_by, order=order, page=page, total_pages=total_pages, total=total, start_item=start_item, end_item=end_item
    ), 200

# create ticket route
@ticket_bp.route('/', methods=['POST'])
def create_ticket():
    # check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    # get title, desc, and priority
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', '').strip().lower()

    if not title or not description or not priority:
        return jsonify({'error': 'Missing required fields'}), 400

    image_data = None
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file and file.filename != '':
            image_data = file.read()

    new_ticket = Ticket(
        title=title,
        description=description,
        priority=priority,
        employeeID=session.get('user_id'),
        image=image_data
    )
    db.session.add(new_ticket)
    db.session.commit()

    return jsonify({'message': 'Ticket created successfully', 'ticket_id': new_ticket.ticketID}), 201

# get individual ticket route
@ticket_bp.route('/<int:ticket_id>', methods=['GET', 'OPTIONS'])
def get_ticket_detail(ticket_id):
    # options method
    if request.method == 'OPTIONS':
        options_data = {
            "resource": "Ticket",
            "ticket_id": ticket_id,
            "description": "Operations for individual ticket",
            "methods": {
                "GET": "Fetch full ticket details (HTML)",
                "PATCH": "Update ticket priority or description (JSON)",
                "DELETE": {
                    "description": "Delete this ticket from database"
                }
            },
            "allowed_headers": ["Content-Type", "Authorization"]
        }

        # CORS headers
        response = make_response(jsonify(options_data), 200)
        response.headers.add("Access-Control-Allow-Methods", "GET, PATCH, DELETE, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
 
        return response
        
    # check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login')), 302
    
    # query ticket by id
    ticket = Ticket.query.get(ticket_id)
    if not ticket or ticket.is_deleted is True:
        return redirect(url_for('tickets.get_tickets'))
        
    # render ticket page
    return render_template('ticket_detail.html', ticket=ticket, current_user_id=session.get('user_id'), role=session.get('role'))

# patch route for priority level or description
@ticket_bp.route('/<int:ticket_id>', methods=['PATCH'])
def update_ticket(ticket_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_user_id = session.get('user_id')
    role = session.get('role')
    
    # check permissions if user is the creator or a technician
    # if role == 'employee' and ticket.employeeID != current_user_id:
    #      return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    # create updated ticket data before getting ticket from database
    update_data = {}
    if 'description' in data:
        update_data['description'] = data['description'].strip()
    
    if 'priority' in data:
        priority = data['priority'].strip().lower()
        if priority in ['low', 'medium', 'high', 'critical']:
            update_data['priority'] = priority
            
    if not update_data:
        return jsonify({'message': 'No changes provided'}), 400
    
    # combine check for ticket and update ticket
    query = Ticket.query.filter(Ticket.ticketID == ticket_id, Ticket.is_deleted == False)
    
    # check perms using sql filter
    if role == 'employee':
        query = query.filter(Ticket.employeeID == current_user_id)

    #check if ticket updated
    updated_count = query.update(update_data)
    if updated_count == 0:
        return jsonify({'error': 'Ticket not found or Unauthorized'}), 404
    
    try:
        db.session.commit()
        return jsonify({'message': 'Ticket updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# assign ticket route
@ticket_bp.route('/<int:ticket_id>/assign', methods=['PUT'])
def assign_ticket(ticket_id):
    # check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # check if user is a technician
    if session.get('role') != 'technician':
        return jsonify({'error': 'Unauthorized: Only technicians can assign tickets'}), 403
    
    # assign ticket to user id without fully loading it in the db
    db.session.query(Ticket).filter_by(ticketID=ticket_id, is_deleted=False).update({
            "technicianID": session.get('user_id'),
            "isAssigned": True
        })
        
    try:
        # commit to db
        db.session.commit()
        return jsonify({'message': 'Ticket assigned successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# delete ticket route
@ticket_bp.route('/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    # check if user is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # get ticket
    # ticket = Ticket.query.get(ticket_id)
    # if not ticket:
    #     return jsonify({'error': 'Ticket not found'}), 404
        
    # get user role and id
    current_user_id = session.get('user_id')
    role = session.get('role')
    
    query = Ticket.query.filter(Ticket.ticketID == ticket_id, Ticket.is_deleted == False)

    # Check permissions if user is the creator or a technician
    # if role == 'employee' and ticket.employeeID != current_user_id:
    #     return jsonify({'error': 'Unauthorized'}), 403
    if role == 'employee':
        query = query.filter(Ticket.employeeID == current_user_id)
    
    #update ticket directly in db
    updated_count = query.update({"is_deleted": True})
    if updated_count == 0:
        return jsonify({'error': 'Ticket not found or Unauthorized'}), 404
    
    try:
        # delete ticket from db
        db.session.commit()
        return jsonify({'message': 'Ticket deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@ticket_bp.route('/<int:ticket_id>/image')
def get_ticket_image(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.image:
        return send_file(
            io.BytesIO(ticket.image),
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=f'ticket_{ticket_id}.jpg'
        )
    return jsonify({'error': 'Cannot upload image'}), 500