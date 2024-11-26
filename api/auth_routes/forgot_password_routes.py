from flask import Blueprint, render_template, url_for, flash, redirect, request
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

from config import mongo
from email_utils import send_email

forgotpassword = Blueprint('forgotpassword', __name__)

s = URLSafeTimedSerializer("SECRET_KEY")


@forgotpassword.route('/', methods=['GET'])
def forgot_password():
    return render_template('auth/forgetpassword.html')


@forgotpassword.route('/reset', methods=['POST'])
def reset_password():
    try:
        email = request.form.get('email')
        # print(email)
        user = mongo.db.users.find_one({'email': email})
        # print(user)
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            # print(token)  # Generate token
            base_url = "http://127.0.0.1:5000/forgotpassword/"

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
                <h1 style="margin: 0;font-size: 24px;font-weight: 500;color: #1f1f1f;">Password Forget Request</h1>
                <p style="margin: 0;margin-top: 17px;font-weight: 500;letter-spacing: 0.56px;">
                    Forget Your Password?<br/>
                    We received a request to reset the password for your account.<br/><br/>
                    To reset your password, click on the link below:<br/>
                    <span style="font-weight: 600; color: #1065f6;">{base_url}/reset-password/{token}</span><br/>
                    If you did not forget your password you can safely ignore this email.
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

            # reset_link = f"{base_url}/reset-password/{token}"
            # print(reset_link)
            subject = "Password Forget Request"
            # Send email with reset link

            send_email(subject, email, body)

            print('A password reset link has been sent to your email.', 'success')
        else:
            flash('Email not found', 'danger')
        return redirect('/')

    except Exception as e:
        return redirect('/forgotpassword')


#
@forgotpassword.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_home(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=1800)  # Token expires in 30 minutes
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        # Hash the password before storing
        hashed_password = generate_password_hash(new_password)  # Implement password hashing
        # Update the user's password in the database
        mongo.db.users.update_one(
            {'email': email},
            {
                '$set': {
                    'password': hashed_password,
                }
            }
        )
        flash('Your password has been updated.', 'success')
        return redirect('/')

    return render_template('auth/reset_password.html')
