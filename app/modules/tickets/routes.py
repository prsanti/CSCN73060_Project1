from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
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