import os
import subprocess

# from flask_uploads import UploadSet, configure_uploads, IMAGES


from api.products_routes.area_routes import area
from apscheduler.schedulers.background import BackgroundScheduler
from config import init_app, mongo
from api.auth_routes.auth_login_routes import login
from api.auth_routes.forgot_password_routes import forgotpassword
from api.auth_routes.auth_register_routes import register
from api.products_routes.products_routes import product
from api.dashboard_routes.admin_dashboard_routes import admin
from api.dashboard_routes.manager_dashboard_routes import manager
from api.dashboard_routes.supplier_dashboard_routes import supplier
from api.dashboard_routes.employee_dashboard_routes import employee
from api.client_routes import client
from api.stock_routes.stock_routes import stock
from api.user_routes.user_routes import user
from api.order_routes.order_routes import order
from api.page_visibility_routes.page_visibility import settings
from flask import Flask, render_template, jsonify, redirect, send_from_directory, session
from flask_mail import Mail

from middleware.monitor_stock_levels import monitor_stock_levels

# from middleware.monitor_stock_levels import monitor_stock_levels

app = Flask(__name__)
# crontab = Crontab(app)
# Initialize MongoDB
init_app(app)

# Set a secret key for the session
app.config['SECRET_KEY'] = 'your_secure_random_key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Register blueprints (routes)
app.register_blueprint(login, url_prefix='/login')
app.register_blueprint(area, url_prefix='/area')
app.register_blueprint(forgotpassword, url_prefix='/forgotpassword')
app.register_blueprint(register, url_prefix='/register')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(manager, url_prefix='/manager')
app.register_blueprint(supplier, url_prefix='/supplier')
app.register_blueprint(employee, url_prefix='/employee')
app.register_blueprint(client, url_prefix='/client')

app.register_blueprint(product, url_prefix='/product')
app.register_blueprint(order, url_prefix='/order')
app.register_blueprint(stock, url_prefix='/stock')
app.register_blueprint(user, url_prefix='/user')
app.register_blueprint(settings, url_prefix='/settings')
# A protected route using token authentication

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'shubhamlathiya2021@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'tqerujnjzuvgdjho'  # Your email password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

# Initialize the mail object
mail = Mail(app)


@app.route('/')
def home():
    return render_template("auth/signin.html")


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    response = jsonify({'message': 'Logged out successfully!'})
    response.set_cookie('token', '', expires=0)
    response = redirect('/')# Clear the cookie
    return response

@app.errorhandler(404)
def handle_404_error(e):
    return render_template('error_handler/error_404.html')
    # return jsonify({'status': 'error shubham', 'message': 'Resource not found (404)'}), 404


@app.errorhandler(500)
def handle_500_error(e):
    return render_template('error_handler/error_500.html')
    # return jsonify({'status': 'error', 'message': 'Internal server error (500)'}), 500


@app.route('/scan', methods=['GET'])
def scan():
    try:
        # Run the qr.py script and capture its output
        result = subprocess.run(['python', 'qr.py'], capture_output=True, text=True)
        output = result.stdout.strip()  # Get the output from qr.py

        # Return the result as JSON
        return jsonify({'barcode': output})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
scheduler.add_job(monitor_stock_levels, 'cron', minute='*/10')
scheduler.start()

if __name__ == '__main__':
    # try:
    # app.run(debug=True)
    app.run(debug=True, use_reloader=False)
# except (KeyboardInterrupt, SystemExit):
# Shutdown the scheduler gracefully
# scheduler.shutdown()
# print("Scheduler shutdown.")
