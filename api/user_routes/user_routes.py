import os
from datetime import datetime

from bson import ObjectId
from flask import Flask, request, jsonify, render_template, Blueprint, redirect
from werkzeug.security import generate_password_hash
from config import mongo
from email_utils import send_email
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

user = Blueprint('user', __name__)


@user.route('/adduser' ,methods = ['GET'], endpoint='user')
@token_required
@role_required('users', 'create')
def add_user(current_user):
    return render_template("user/add_user.html")


@user.route('/updateuser/<string:user_id>', methods=['GET'], endpoint='update_user_home')
@token_required
@role_required('users', 'edit')
def update_user_home(current_user, user_id):
    # print("user_id")
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    return render_template("user/update_user.html", user=user)


@user.route('/viewuser', methods=['GET'], endpoint='viewuser')
@token_required
@role_required('users', 'view')
def view_user(current_user):
    try:
        users_list = list(mongo.db.users.find({'role': {'$in': ['manager', 'employee', 'admin']}}))
        return render_template("user/view_user.html", users_list=users_list)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@user.route('/viewclient', methods=['GET'], endpoint='viewclient')
@token_required
@role_required('users', 'view')
def view_client(current_user):
    try:
        users_list = list(mongo.db.users.find({'role': 'client'}))
        return render_template("user/view_client.html", users_list=users_list)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@user.route('/viewsupplier', methods=['GET'], endpoint='viewsupplier')
@token_required
@role_required('users', 'view')
def supplier_client(current_user):
    try:
        users_list = list(mongo.db.users.find({'role': 'supplier'}))
        return render_template("user/view_supplier.html", users_list=users_list)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@user.route('/adduser', methods=['POST'], endpoint='adduser')
@token_required
@role_required('users', 'create')
def add_personnel(current_user):
    try:
        data = request.form
        # print(data)
        name = data.get('full_name')
        mobile = data.get('mobile')
        email = data.get('email')
        password = generate_password_hash(data.get('password'))
        role = data.get('role')
        city = data.get('city')
        area = data.get('area')


        # if not name or not mobile or not email or not password:
        #     return jsonify({"error": "All fields are required"}), 400
        #
        # photo = request.files['photo']
        # ext = photo.filename.rsplit('.', 1)[1].lower()
        # new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        # from app import app
        # filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'users', new_filename)
        # normalized_path = filepath.replace('\\', '/')
        # print(normalized_path)
        # try:
        #     photo.save(normalized_path)
        #     print(f'File saved at: {normalized_path}')
        # except Exception as e:
        #     return jsonify({'error': str(e)}), 500
        # Create a personnel document
        personnel = {
            'full_name': name,
            'mobile': mobile,
            'email': email,
            'password': password,  # Store the hashed password
            'role': role,
            'city': city,
            'area': area,
            # 'image': normalized_path,
            'status': "true"
        }

        # Insert into MongoDB
        mongo.db.users.insert_one(personnel)
#
#         # Prepare email details
        subject = f'{role} Details'

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
                <h1 style="margin: 0;font-size: 24px;font-weight: 500;color: #1f1f1f;">User Added</h1>
                <p style="margin: 0;margin-top: 17px;font-size: 16px;font-weight: 500;">
                    Hello {name},
                </p>
                <p style="margin: 0;margin-top: 17px;font-weight: 500;letter-spacing: 0.56px;">
                    Your details have been successfully registered.<br/>
                    User Id : <span style="font-weight: 600; color: #1f1f1f;">{email}</span><br/>
                    Mobile : <span style="font-weight: 600; color: #1f1f1f;">{mobile}</span><br/>
                    Password : <span style="font-weight: 600; color: #1f1f1f;">{data.get('password')}</span><br/>
                    Role : <span style="font-weight: 600; color: #1f1f1f;">{role}</span>.
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

        # Send email
        if send_email(subject, email, body):
            return redirect('/user/viewuser')
        else:
            return jsonify({"error": "Failed to send email."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user.route('/updateuser/<string:user_id>', methods=['POST'], endpoint='update_user')
@token_required
@role_required('users', 'edit')
def update_user(current_user, user_id):
    try:
        # print(user_id)
        name = request.form.get('full_name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        role = request.form.get('role')
        city = request.form.get('city')
        area = request.form.get('area')

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'full_name': name,
                    'mobile': mobile,
                    'email': email,
                    'role': role,
                    'city': city,
                    'area': area,
                }
            }
        )

        return redirect('/user/viewuser')

    except Exception as e:
        # flash(f"Error updating user: {str(e)}", 'error')
        return redirect('/user/viewuser')


@user.route('/user_status', methods=['POST'],endpoint='userStatus')
@token_required
def user_status(current_user):
    data = request.get_json()

    user_id = data.get('user_id')  # User ID passed from the client-side
    new_status = data.get('status')  # New status (true/false)

    if user_id and new_status:
        # Update the user's status in the database
        result = mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'status': new_status}}
        )

        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Status update failed'})
    return jsonify({'success': False, 'message': 'Invalid request'}), 400


