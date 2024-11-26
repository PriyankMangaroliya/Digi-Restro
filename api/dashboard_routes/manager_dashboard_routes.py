from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template, Blueprint

from config import mongo
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

manager = Blueprint('manager', __name__)


@manager.route('/dashboard', methods=['GET'])
@token_required
@role_required('manager_dashboard', 'view')
def dashboard_home(current_user):
    totalClients = list(mongo.db.users.aggregate([
        {"$match": {"role": "client"}},
        {"$count": "totalClients"}
    ]))
    # print(totalClients[0]['totalClients'])

    totalSuppliers = list(mongo.db.users.aggregate([
        {"$match": {"role": "supplier"}},
        {"$count": "totalSuppliers"}
    ]))
    # print(totalSuppliers[0]['totalSuppliers'])

    totalEmployee = list(mongo.db.users.aggregate([
        {"$match": {"role": "employee"}},
        {"$count": "totalEmployee"}
    ]))
    # print(totalEmployee[0]['totalEmployee'])

    now = datetime.now()
    start_of_month = datetime(now.year, now.month, 1)  # Start of the current month
    end_of_month = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)  # Last second of the current month
    # Run the query to find the total number of orders for the current month
    totalOrders = list(mongo.db.orders.aggregate([
        # Match orders where the order_date is in the current month
        {"$match": {
            "order_date": {
                "$gte": start_of_month,
                "$lt": end_of_month
            }
        }},
        # Count the total number of matched orders
        {"$count": "totalOrders"}
    ]))
    # print(totalOrders[0]['totalOrders'])

    recently_product = recently_added_products()
    recently_stock = list(recently_added_products_stock())

    return render_template('dashboard/admin_dashboard.html',
                           recently_product=recently_product,
                           recently_stock=recently_stock,
                           totalClients=totalClients[0]['totalClients'],
                           totalSuppliers=totalSuppliers[0]['totalSuppliers'],
                           totalEmployee=totalEmployee[0]['totalEmployee'],
                           totalOrders = totalOrders[0]['totalOrders'],)


def recently_added_products():
    # Get the current date and time
    now = datetime.now()

    # Define the time window for "recent" products (e.g., last 7 days)
    seven_days_ago = now - timedelta(days=7)

    # Run the query to find products added in the last 7 days
    recent_products = mongo.db.products.find({
        "created_at": {"$gte": seven_days_ago}
    }).limit(4)

    return recent_products


def recently_added_products_stock():
    recent_product_with_plus_qty = mongo.db.stock.aggregate([
        # Match products where +qty is greater than 0
        {"$match": {"+qty": {"$gt": 0}}},

        # Sort by date field in descending order (most recent first)
        {"$sort": {"date": -1}},

        # Limit to 4 results to get only the most recent ones
        {"$limit": 4},

        # Lookup the 'products' collection to fetch product name and image using sku
        {"$lookup": {
            "from": "products",  # The products collection
            "localField": "sku",  # The sku field in the stock collection
            "foreignField": "sku",  # The sku field in the products collection
            "as": "product_details"  # Alias for the joined data
        }},

        # Unwind the product_details array to get the product details directly
        {"$unwind": "$product_details"},

        # Project the desired fields: SKU, +qty, name, and image URL
        {"$project": {
            "_id": 0,
            "sku": 1,
            "quantity": "$+qty",
            "product_name": "$product_details.product_name",  # Get name from the joined product_details
            "image": "$product_details.image"  # Get image from the joined product_details
        }}
    ])

    return recent_product_with_plus_qty
