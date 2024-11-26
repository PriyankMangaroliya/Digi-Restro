from datetime import datetime
from random import randint

from bson import ObjectId
from flask import Flask, request, jsonify, render_template, Blueprint, redirect, session

from api.order_routes.order_routes import order
from config import mongo
from email_utils import send_email
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

supplier = Blueprint('supplier', __name__)


@supplier.route('/dashboard', methods=['GET'], endpoint='supplier_orders')
@supplier.route('/dashboard/<supplier_id>', methods=['GET'], endpoint='supplier_dashboard_with_id')
@token_required
@role_required('supplier_dashboard', 'view')
def get_supplier_orders(current_user, supplier_id=None):
    try:
        # print(f"Fetching orders for supplier: {session['user_id']}")
        if supplier_id:
            userid = supplier_id
        else:
            userid = session['user_id']

        # Fetch assigned tasks for the supplier
        assigned_tasks = list(mongo.db.assigned_tasks.find({
            'supplier_id': ObjectId(userid),
        }).sort('assigned_date', -1))

        if not assigned_tasks:
            error = "No orders assigned to this supplier."
            return render_template('dashboard/supplier_dashboard.html', error=error)
            # return jsonify({'status': 'error', 'message': 'No orders assigned to this supplier.'}), 404

        # Create a list to hold orders details
        orders_details = []
        for task in assigned_tasks:
            # Ensure order_id is an ObjectId before querying
            order_id = task.get('order_id')
            if not order_id:
                continue  # Skip if there's no order_id

            # Fetch the corresponding order details using the order_id
            order = mongo.db.orders.find_one({'_id': order_id})
            if order:
                # Fetch the user details using user_id from the order
                user_id = order.get('user_id')
                user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

                # If user is found, extract details
                user_details = {}
                if user:
                    user_details = {
                        'name': user.get('full_name', ''),
                        'mobile': user.get('mobile', ''),
                        'city': user.get('city', ''),
                        'area': user.get('area', '')
                    }

                # Build the order detail object including user details
                order_detail = {
                    'order_id': str(order['_id']),
                    'products': order.get('products', []),  # Use get to avoid KeyError
                    'total_amount': order.get('total_amount', 0),
                    'payment_type': order.get('payment_type', ''),
                    'order_date': order.get('order_date', None),
                    'status': order.get('status', [])[-1]['status'] if order.get('status', []) else '',
                    'user_details': user_details  # Include the user details
                }
                orders_details.append(order_detail)

        if supplier_id:
            return render_template('dashboard/view_delivery.html', orders_details=orders_details)
        else:
            return render_template('dashboard/supplier_dashboard.html', orders_details=orders_details)

        # return jsonify({'status': 'success', 'orders': orders_details}), 200



    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@supplier.route('/pickup', methods=['POST'], endpoint='pickup')
@token_required
def pickup_multiple_orders(current_user):
    try:
        # print("1")
        # print(request.form)
        # Get the list of order IDs from the form
        order_ids = request.form.getlist('order_ids')

        # Check if any order is selected
        if not order_ids:
            return jsonify({'status': 'error', 'message': 'No orders selected for pickup.'}), 400

        for order_id in order_ids:
            # Step 1: Update each order status to 'Out for Delivery'
            # mongo.db.orders.update_one(
            #     {'_id': ObjectId(order_id), 'assigned_supplier_id': ObjectId(current_user['_id'])},
            #     {'$set': {'status': 'Out for Delivery', 'pickup_date': datetime.now()}}
            # )

            mongo.db.orders.update_one(
                {'_id': ObjectId(order_id)},
                {'$push': {
                    'status': {
                        'status': 'Out for Delivery',
                        'updated_at': datetime.now()
                    }
                }}
            )

            mongo.db.assigned_tasks.update_one(
                {'order_id': ObjectId(order_id)},
                {
                    '$set': {
                        'status': 'Out for Delivery'  # Update the current status
                    }
                }
            )

            # Step 2: Generate an OTP and update the order
            otp = randint(100000, 999999)

            mongo.db.orders.update_one(
                {'_id': ObjectId(order_id)},
                {'$set': {'otp': otp}}
            )

            # Step 3: Send OTP to the customer via email or SMS (assuming email here)
            order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
            client = mongo.db.users.find_one({'_id': ObjectId(order['user_id'])})
            # body = str(otp)  # You need to implement this function

            subject = "Order Confirmation OTP"

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

            send_email(subject, client['email'], body)

        # return redirect('/supplier/dashboard')
        return jsonify({'status': 'success', 'message': 'Orders picked up and OTP sent to customers.',
                        'url': "/supplier/dashboard"}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@supplier.route('/deliver/<order_id>', methods=['POST'], endpoint='deliver')
@token_required
def deliver_order(current_user, order_id):
    try:
        print("deliver", order_id)
        otp_entered = request.form.get('otp')
        cash_collected = request.form.get('cash_collected')  # For COD orders

        # Fetch the order from the database
        order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})

        # Verify OTP
        if otp_entered != str(order['otp']):
            return jsonify({'status': 'error', 'message': 'Invalid OTP'}), 400

        # If the order is COD, ensure cash is collected
        if order['payment_type'] == 'Cash' and not cash_collected:
            return jsonify({'status': 'error', 'message': 'Cash not collected for COD order'}), 400

        # Mark the order as delivered
        # mongo.db.orders.update_one({'_id': ObjectId(order_id)},
        #                            {"$set": {'status': 'Delivered', 'delivery_date': datetime.now()}})

        mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$push': {
                'status': {
                    'status': 'Delivered',
                    'delivery_date': datetime.now()
                }
            }}
        )

        mongo.db.assigned_tasks.update_one(
            {'order_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': 'Delivered'  # Update the current status
                }
            }
        )

        # Insert cash collection record for WMS manager if COD
        if order['payment_type'] == 'Cash':
            cash_entry = {
                'order_id': ObjectId(order_id),
                'supplier_id': ObjectId(session['user_id']),
                'amount': int(order['total_amount']),
                "submission_date": None,
                'collection_date': datetime.now(),
                "status": "Collected",
            }

            # status : "Pending," "Collected," or "Submitted"
            mongo.db.cash_collections.insert_one(cash_entry)

            mongo.db.transactions.update_one(
                {'order_id': ObjectId(order_id)},
                {
                    '$set': {
                        'payment_status': 'Paid',
                        'transaction_date': datetime.now()  # Update the current status
                    }
                }
            )

        print("cash")

        return redirect('/supplier/dashboard')

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


#
# Route to submit cash to WMS manager
@supplier.route('/submit_multiple_cash', methods=['POST'], endpoint='submit_multiple_cash')
@token_required
def submit_multiple_cash(current_user):
    try:
        data = request.get_json()
        cash_ids = data.get('cash_ids', [])

        if not cash_ids:
            return jsonify({'status': 'error', 'message': 'No cash orders selected'}), 400

        # Update all selected cash orders with submission date, status, and submitted_by
        result = mongo.db.cash_collections.update_many(
            {'_id': {'$in': [ObjectId(cash_id) for cash_id in cash_ids]}},
            {
                "$set": {
                    'submission_date': datetime.now(),
                    'submitted_by': "manager",  # Assuming "manager" submits the cash
                    'status': "Submitted"
                }
            }
        )

        if result.modified_count == 0:
            return jsonify({'status': 'error', 'message': 'Failed to submit cash orders'}), 400

        return jsonify({'status': 'success', 'message': f'Successfully submitted {result.modified_count} cash orders'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@supplier.route('/codorders/<supplier_id>', methods=['GET'], endpoint='cod_orders')
@token_required
def get_cod_orders(current_user, supplier_id):
    try:
        # Fetch COD cash collections for the supplier
        cod_orders = list(mongo.db.cash_collections.find({
            'supplier_id': ObjectId(supplier_id)
        }))

        # Transform data for the frontend
        orders_data = [
            {
                'order_id': str(order['order_id']),
                'total_amount': order.get('amount', 0),
                'submission_date': order.get('submission_date'),
                'status': order.get('status', "Pending"),
                'cash_id': str(order['_id'])
            }
            for order in cod_orders
        ]

        return render_template('order/COD_Orders.html', orders_data=orders_data)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
