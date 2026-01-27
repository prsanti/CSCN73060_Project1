from flask import Flask, render_template, request, jsonify, make_response
from database import db
from models import Ticket, User

app = Flask(__name__)

# db configured with sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project6.db'

db.init_app(app)

# create all tables
with app.app_context():
    db.create_all()

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