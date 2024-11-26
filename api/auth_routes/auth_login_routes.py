import email
from flask import Blueprint, request, jsonify, session, redirect
import jwt
import datetime

from werkzeug.security import check_password_hash

from config import mongo

login = Blueprint('login', __name__)


@login.route('/', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    print(email)
    user = mongo.db.users.find_one({'email': email})
    print(user['status'])
    if user and check_password_hash(user['password'], password):
        # Create JWT token
        if user['status'] == 'true':
            token = jwt.encode({
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=10)  # Token expires in 10 hour
            }, 'your_secret_key', algorithm='HS256')

            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            session['role'] = user['role']
            session['name'] = user['full_name']
            # print(session['name'])
            # Determine the redirection URL based on user role
            if user['role'] == 'client':
                redirect_url = '/client/dashboard'  # Define client dashboard URL
            elif user['role'] == 'admin':
                redirect_url = '/admin/dashboard'
            elif user['role'] == 'manager':
                redirect_url = '/manager/dashboard'
            elif user['role'] == 'supplier':
                redirect_url = '/supplier/dashboard'
            elif user['role'] == 'employee':
                redirect_url = '/employee/dashboard'
            else:
                return jsonify({'message': 'Invalid role. Please contact dashboard.'}), 400

            return jsonify({'token': token, 'redirect_url': redirect_url})
        else:
            return jsonify({'message': 'Your are DeActive. Please contact Admin'}), 400
    else:
        return jsonify({'message': 'Invalid credentials'}), 401
