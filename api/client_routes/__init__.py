from flask import Blueprint

# Initialize the 'client' blueprint
client = Blueprint('client', __name__)

# Import views from other modules (dashboard, orders)
from .client_dashboard_routes import *
from .client_order_routes import *
