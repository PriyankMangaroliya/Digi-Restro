from bson import ObjectId
from flask import Flask, request, jsonify, render_template, Blueprint, session

from config import mongo
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required
from . import client
from ..order_routes.order_routes import order


@client.route('/order/history', methods=['GET'], endpoint='history')
@token_required
@role_required('client_dashboard', 'view')
def history(current_user):
    user_id = session.get('user_id')

    # Fetch the orders for the current user
    orders = mongo.db.orders.find({"user_id": ObjectId(user_id)})

    order_list = []

    for order in orders:
        # Assuming you have a 'transaction' collection for payment details
        transaction = mongo.db.transactions.find_one({"order_id": order['_id']})

        order_data = {
            'order_id': order['_id'],
            "total_amount": order.get("total_amount", 0),
            "payment_type": order.get("payment_type", "N/A"),
            'status': order.get('status', [])[-1]['status'] if order.get('status', []) else '',
            "products": order.get("products", []),
            "order_date": order.get("order_date", ""),
            "payment_status": transaction.get("payment_status", "N/A") if transaction else "N/A"
            # Link with transaction collection
        }

        order_list.append(order_data)

    # print(order_list)
    # Pass the data to the template
    return render_template('client/view_orders.html', orders_details=order_list)


@client.route('/order/history/timeline/<order_id>', methods=['GET'], endpoint='timeline')
@token_required
@role_required('client_dashboard', 'view')
def history(current_user, order_id):
    # Fetch the orders for the current user
    orders = list(mongo.db.orders.find({"_id": ObjectId(order_id)}))

    return render_template('client/timeline.html', timeline=orders[0]['status'])
