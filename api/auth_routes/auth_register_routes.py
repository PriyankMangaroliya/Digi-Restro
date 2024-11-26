import random
from flask import Blueprint, request, jsonify, render_template, session, redirect
from werkzeug.security import generate_password_hash

from config import mongo
from email_utils import send_email
from middleware.auth_middleware import token_required

register = Blueprint('register', __name__)

@register.route('/', methods=['POST'])
def register_user():
    # data = request.get_json()
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')

    user = mongo.db.users.find_one({'email': email})
    #
    if user:
        return jsonify({'message': 'User already exists!'}), 400

    otp = random.randint(1000, 9999)

    # Save OTP in session temporarily
    session['otp'] = otp
    session['full_name'] = full_name
    session['email'] = email
    session['password'] = password

    subject = "Your OTP for Registration"

    body = f"""
    <!DOCTYPE html>
<html lang="en">
<head>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet"/>
</head>
<body style="margin: 0; font-family: 'Poppins', sans-serif; background: #ffffff; font-size: 14px;">
<div style="max-width: 680px;margin: 0 auto;padding: 45px 30px 60px;background: #f4f7ff;
        background-image: url(https://archisketch-resources.s3.ap-northeast-2.amazonaws.com/vrstyler/1661497957196_595865/email-template-background-banner);
        background-repeat: no-repeat;background-size: 800px 452px;background-position: top center;font-size: 14px;color: #434343;">
    <header>
        <table style="width: 100%;">
            <tbody>
            <tr style="height: 0;">
                <td>
                    <h1>WMS</h1>
                </td>
                <td style="text-align: right;">
                    <span style="font-size: 16px; line-height: 30px; color: #ffffff;">Warehouse Management System</span>
                </td>
            </tr>
            </tbody>
        </table>
    </header>

    <main>
        <div style="margin: 0;margin-top: 70px;padding: 92px 30px 115px;background: #ffffff;border-radius: 30px;text-align: center;">
            <div style="width: 100%; max-width: 489px; margin: 0 auto;">
                <h1 style="margin: 0;font-size: 24px;font-weight: 500;color: #1f1f1f;">Your OTP</h1>
                <p style="margin: 0;margin-top: 17px;font-size: 16px;font-weight: 500;">
                    Hi {full_name},
                </p>
                <p style="margin: 0;margin-top: 17px;font-weight: 500;letter-spacing: 0.56px;">
                    Thank you for choosing WMS. Use the following OTP to verify your email address. OTP is
                    valid for <span style="font-weight: 600; color: #1f1f1f;">5 minutes</span>.
                    Do not share this code with others, including WMS employees.
                </p>
                <p style="margin: 0;margin-top: 60px;font-size: 40px;font-weight: 600;letter-spacing: 25px;color: #ba3d4f;">
                    {otp}
                </p>
            </div>
        </div>

        <p style="max-width: 400px; margin: 0 auto;margin-top: 90px;text-align: center;font-weight: 500;color: #8c8c8c;">
            Need help? Ask at
            <a href="mailto:wms@gmail.com" style="color: #499fb6; text-decoration: none;">wms@gmail.com</a>
        </p>
    </main>

    <footer style="width: 100%;max-width: 490px;margin: 20px auto 0;text-align: center;border-top: 1px solid #e6ebf1;">
        <p style="margin: 0;margin-top: 40px;font-size: 16px;font-weight: 600;color: #434343;">
            Warehouse Management System
        </p>
        <p style="margin: 0; margin-top: 8px; color: #434343;"></p>
        <div style="margin: 0; margin-top: 16px;">
            <a href="" target="_blank" style="display: inline-block;">
                <img width="36px" alt="Facebook"
                     src="https://archisketch-resources.s3.ap-northeast-2.amazonaws.com/vrstyler/1661502815169_682499/email-template-icon-facebook"/>
            </a>
            <a href="" target="_blank" style="display: inline-block; margin-left: 8px;">
                <img width="36px" alt="Instagram"
                     src="https://archisketch-resources.s3.ap-northeast-2.amazonaws.com/vrstyler/1661504218208_684135/email-template-icon-instagram"/>
            </a>
            <a href="" target="_blank" style="display: inline-block; margin-left: 8px;">
                <img width="36px" alt="Twitter"
                     src="https://archisketch-resources.s3.ap-northeast-2.amazonaws.com/vrstyler/1661503043040_372004/email-template-icon-twitter"/>
            </a>
            <a href="" target="_blank" style="display: inline-block; margin-left: 8px;">
                <img width="36px" alt="Youtube"
                     src="https://archisketch-resources.s3.ap-northeast-2.amazonaws.com/vrstyler/1661503195931_210869/email-template-icon-youtube"/>
            </a>
        </div>
        <p style="margin: 0; margin-top: 16px; color: #434343;">
            Copyright © 2024 WMS. All rights reserved.
        </p>
    </footer>
</div>
</body>
</html>
"""
   
    # body = f"Your OTP is {otp}. Please enter this to complete your registration."
    send_email(subject, email, body)

    # print(full_name, email, password)
    # user = mongo.db.users.find_one({'email': data['email']})
    #
    # if user:
    #     return jsonify({'message': 'User already exists!'}), 400
    #
    # user_id = mongo.db.users.insert_one({
    #     'email': data['email'],
    #     'password': data['password']  # Hash this in production
    # }).inserted_id

    # return jsonify({'message': 'User registered successfully!'})
    return redirect('/register/verify-otp')

@register.route('/', methods=['GET'])
def register_user2():
    return render_template('auth/signup.html')

# OTP Verification Page
@register.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        # Check if the OTP matches
        if 'otp' in session and int(entered_otp) == session['otp']:
            # OTP matched, save user to the database
            user_data = {
                'full_name': session['full_name'],
                'email': session['email'],
                'password': generate_password_hash(session['password']),
                'role': "client",
                'status': "true"
            }

            # Insert the user data into MongoDB
            mongo.db.users.insert_one(user_data)

            # Clear session data
            session.pop('otp', None)
            session.pop('full_name', None)
            session.pop('email', None)
            session.pop('password', None)

            return redirect('/')
        else:
            return jsonify({'error': 'Invalid OTP'}), 400

    return render_template('auth/otp.html')

# admin and manager
@register.route('/profile', methods=['GET'], endpoint='profile')
@token_required
def profile(current_user):
    user = list(mongo.db.users.find({'email': current_user}))
    print(user)
    return render_template('auth/profile.html', user=user)

# client suppliers or employess
@register.route('/profile/update/<user_id>', methods=['POST'],endpoint='update_profile')
@token_required
def profile_update(current_user , user_id):
    print(request.form)
    full_name = request.form.get('full_name')
    mobile = request.form.get('mobile')
    city = request.form.get('city')
    area = request.form.get('area')
    address = request.form.get('address')

    mongo.db.users.update_one(
        {'email': current_user},
        {
            '$set': {
                'full_name': full_name,
                'mobile': mobile,
                'city': city,
                'area': area,
                'address': address,
            }
        }
    )

    return redirect('/register/profile')