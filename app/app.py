from flask import Flask, render_template, request, jsonify, make_response
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
    tickets = Ticket.query.all()
    # return all tickets as a json
    return jsonify([t.to_dict() for t in tickets]), 200
  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7500, debug=True)