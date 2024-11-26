from email.mime.text import MIMEText
from flask_mail import Message, Mail
from flask import current_app

mail = Mail()

def send_email(subject, recipient_email, body_html):
    try:
        # Create the Flask-Mail message object
        msg = Message(subject=subject,
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[recipient_email])

        # Attach the HTML body to the message
        msg.html = body_html

        # Send the email using Flask-Mail
        mail.send(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
