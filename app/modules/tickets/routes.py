import io
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file

from sqlalchemy import case, asc, desc
from modules.database.database import db
from models import Ticket

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
        query = query.filter(Ticket.priority.ilike(priority_query))

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

@ticket_bp.route('/', methods=['POST'])
def create_ticket():
    if 'user_id' not in session:
        return redirect(url_for('auth.login')), 302

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', '').strip().lower()

    if not title or not description or not priority:
        # simplest behavior: send them back
        return redirect(url_for('tickets.get_tickets'))

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

    # Go back to tickets list after submit
    return redirect(url_for('tickets.get_tickets'))

@ticket_bp.route('/<int:ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login')), 302
    
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return redirect(url_for('tickets.get_tickets'))
        
    return render_template('ticket_detail.html', ticket=ticket, current_user_id=session.get('user_id'), role=session.get('role'))

@ticket_bp.route('/<int:ticket_id>', methods=['PATCH'])
def update_ticket(ticket_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    current_user_id = session.get('user_id')
    role = session.get('role')
    
    # Check permissions: only allow if user is the creator or a technician
    if role == 'employee' and ticket.employeeID != current_user_id:
         return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    
    if 'description' in data:
        ticket.description = data['description'].strip()
    
    if 'priority' in data:
        priority = data['priority'].strip().lower()
        if priority in ['low', 'medium', 'high', 'critical']:
            ticket.priority = priority
            
    try:
        db.session.commit()
        return jsonify({'message': 'Ticket updated successfully'}), 200
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
    return '', 404