from flask import Flask, render_template, request, jsonify, make_response
from sqlalchemy import case, asc, desc
from modules.database.database import db
from models import Ticket, User
from modules.database.seed import seed_data
import os

from modules.Auth.routes import auth_bp

app = Flask(__name__)

# db configured with sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project6.db'
app.config['SECRET_KEY'] = os.urandom(24) # for session security


db.init_app(app)

# Register the auth blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# create all tables
with app.app_context():
    # seed tables with fake data
    seed_data()

@app.route('/')
def home():
    return render_template('index.html')

# get all tickets
@app.route('/tickets', methods=['GET'])
def get_tickets():
    query = Ticket.query

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
    return render_template('tickets.html', tickets=tickets, sort_by=sort_by, order=order)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7500, debug=True)