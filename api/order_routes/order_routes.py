from bson import ObjectId
from flask import Blueprint, render_template, request, jsonify, redirect, session
from config import mongo
from middleware.auth_middleware import token_required

# Initialize blueprint
order = Blueprint('order', __name__)


# @order.route('/order', methods=['GET'], endpoint='order')
# @token_required
# def order_home(current_user):
#     all_orders = mongo.db.orders.find()
#
#     return render_template('order/orders.html')


@order.route('/getorders', methods=['GET'] , endpoint='getorders')
@token_required
def get_orders(current_user):
    try:
        # Fetch all orders from the database
        all_orders = mongo.db.orders.find()

        orders_list = []
        for order in all_orders:
            # Fetch the user details using user_id from the order
            user = mongo.db.users.find_one({'_id': ObjectId(order['user_id'])})
            user_details = {
                'user_id': str(user['_id']),
                'name': user['full_name'],
                'email': user['email'],
                'phone': user['mobile']
            }

            # Fetch transaction details using order_id
            transaction = mongo.db.transactions.find_one({'order_id': ObjectId(order['_id'])})
            transaction_details = {
                'transaction_id': str(transaction['_id']),
                'payment_method': transaction['payment_type'],
                'payment_status': transaction['payment_status'],
                'transaction_date': transaction['transaction_date'].strftime('%Y-%m-%d')
            }

            # Create an order dictionary with basic order info, user, and transaction details
            order_dict = {
                'order_id': str(order['_id']),
                'user': user_details,
                'total_amount': order['total_amount'],
                'status': order.get('status', [])[-1]['status'] if order.get('status', []) else '',
                'order_date': order['order_date'].strftime('%Y-%m-%d'),
                'transaction': transaction_details,
                'products': []  # List of products in the order
            }

            # Add product details to the order
            for product in order['products']:
                product_info = {
                    'product_name': product['product_name'],
                    'quantity': product['quantity'],
                    'price': product['price'],
                    'amount': product['amount']
                }
                order_dict['products'].append(product_info)

            orders_list.append(order_dict)

        # print(orders_list)
        # Return the order list with user and transaction details
        return render_template("order/orders.html", orders_list=orders_list), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@order.route('/packages', methods=['GET'])
@token_required
def get_all_packages(current_user):
    try:
        # Assigned , Shipment Ready,Out for Delivery,Delivered,Cancelled
        not_shipped_packages = list(mongo.db.orders.aggregate([
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_info'
                }
            },
            {
                '$addFields': {
                    # Extract the last status from the status array
                    'last_status': {
                        '$arrayElemAt': ['$status', -1]  # Fetch the last element in the status array
                    }
                }
            },
            {
                '$match': {
                    'last_status.status': 'Assigned'  # Check if the last status is 'Not Shipped'
                }
            }
        ]))

        shipped_packages = list(mongo.db.orders.aggregate([
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_info'
                }
            },
            {
                '$addFields': {
                    # Extract the last status from the status array
                    'last_status': {
                        '$arrayElemAt': ['$status', -1]  # Fetch the last element in the status array
                    }
                }
            },
            {
                '$match': {
                    'last_status.status': 'Shipment Ready'  # Check if the last status is 'Not Shipped'
                }
            }
        ]))

        delivered_packages = list(mongo.db.orders.aggregate([
            {
                '$lookup': {
                    'from': 'users',
                    'localField': 'user_id',
                    'foreignField': '_id',
                    'as': 'user_info'
                }
            },
            {
                '$addFields': {
                    # Extract the last status from the status array
                    'last_status': {
                        '$arrayElemAt': ['$status', -1]  # Fetch the last element in the status array
                    }
                }
            },
            {
                '$match': {
                    'last_status.status': 'Out for Delivery'  # Check if the last status is 'Not Shipped'
                }
            }
        ]))

        # Render template with grouped packages
        return render_template(
            'order/packages.html',
            not_shipped=not_shipped_packages,
            shipped=shipped_packages,
            delivered=delivered_packages
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
