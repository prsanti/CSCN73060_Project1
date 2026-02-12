from flask import Flask, render_template, request, jsonify, make_response
from sqlalchemy import case, asc, desc
from modules.database.database import db
from models import Ticket, User
from modules.database.seed import seed_data
import os

from modules.Auth.routes import auth_bp
from modules.tickets.routes import ticket_bp

app = Flask(__name__)

# db configured with sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project6.db'
app.config['SECRET_KEY'] = os.urandom(24) # for session security


db.init_app(app)

# Register the auth blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# register tickets blueprint
app.register_blueprint(ticket_bp, url_prefix='/tickets')

# create all tables
with app.app_context():
    # seed tables with fake data
    seed_data()

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7500, debug=True)