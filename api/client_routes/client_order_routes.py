from datetime import datetime

import razorpay
from bson import ObjectId
from flask import Blueprint, render_template, request, jsonify, redirect, session, send_file
from config import mongo

from email_utils import send_email
from middleware.auth_middleware import token_required
from api.client_routes.client_dashboard_routes import client

from . import client

razorpay_client = razorpay.Client(auth=("rzp_test_51mQEdclvr946E", "SJWkJRepFPjAMUFRaNwqWR0p"))


# client add
@client.route('/dashboard', methods=['GET'], endpoint='orderProducts')
@token_required
# @role_required('order_routes')
def order_products(current_user):
    try:
        products = mongo.db.products.find()
        # print(list(products))
        product_list = []
        for product in products:
            stock_record = mongo.db.stock.find({'sku': product['sku']}).sort('date', -1).limit(1)

            stock_record = list(stock_record)

            if stock_record:
                stock_qty = stock_record[0]['total_qty']
            else:
                stock_qty = 0

            product_list.append({
                'image': product['image'],
                'name': product['product_name'],
                'unit': product['unit'],
                'sku': product['sku'],
                'price': product['price'],
                'stock_qty': stock_qty
            })
        print(product_list)
        return render_template("client/client_dashboard.html", products=product_list)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@client.route('/createRazorpayOrder', methods=['POST'], endpoint='createRazorpayOrder')
@token_required
def create_razorpay_order(current_user):
    try:
        order_details = request.json
        total_amount = order_details['totalAmount'] * 100  # Convert to paise (1 INR = 100 paise)

        print(type(total_amount))
        # Create the Razorpay order
        razorpay_order = razorpay_client.order.create(dict(
            amount=total_amount,  # Amount in paise
            currency='INR',
            payment_capture='1',  # Auto-capture payment after payment completion
        ))

        return jsonify({
            'status': 'success',
            'razorpay_order_id': razorpay_order['id'],
            'amount': total_amount / 100  # Amount in INR
        }), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@client.route('/submitOrder', methods=['POST'], endpoint='submitOrder')
@token_required
def submit_order(current_user):
    try:
        # Parse order details
        userdata = mongo.db.users.find_one({'email': current_user})
        # print(userdata)
        if userdata['city'] is None and userdata['area'] is None and userdata['address'] is None:
            return jsonify(
                {'status': 'error', 'message': 'please update your profile in area'}
            )

        order_details = request.json  # Expecting JSON data
        total_amount = float(order_details['totalAmount'])  # Parse the total amount
        payment_type = order_details['paymentType']  # Payment type (Cash, Razorpay, etc.)
        ordered_products = []

        # Iterate through each product in the order
        for product in order_details['products']:
            product_id = product['id']
            quantity = int(product['qty'])  # Quantity ordered

            # Find the product by SKU in the database
            product_record = mongo.db.products.find_one({'sku': int(product_id)})
            if not product_record:
                return jsonify({'status': 'error', 'message': f"Product with SKU {product_id} not found."}), 400

            # Fetch the latest stock record for the product
            stock_record = mongo.db.stock.find_one({'sku': product_record['sku']}, sort=[('date', -1)])
            if not stock_record or stock_record['total_qty'] < quantity:
                return jsonify({'status': 'error', 'message': f"Not enough stock for {product_record['name']}"}), 400

            # Update stock and create a new stock record
            new_total_qty = stock_record['total_qty'] - quantity
            new_stock_entry = {
                "sku": product_record['sku'],
                "date": datetime.now(),
                "+qty": 0,
                "-qty": quantity,
                "total_qty": new_total_qty
            }

            # Insert new stock record into the stock collection
            new_stock_record = mongo.db.stock.insert_one(new_stock_entry)

            # Append product to the ordered products list
            ordered_products.append({
                'product_id': str(product_record['_id']),  # Convert ObjectId to string
                'product_name': product_record['product_name'],
                'quantity': quantity,
                'price': product_record['price'],
                'amount': product_record['price'] * quantity,
                'stock_record_id': str(new_stock_record.inserted_id)  # Track the stock record ID
            })

        # Create the order object with status array
        order = {
            'user_id': ObjectId(session['user_id']),  # Replace with `current_user` if available
            'products': ordered_products,
            'total_amount': total_amount,
            'payment_type': payment_type,
            'order_date': datetime.now(),
            'status': [  # Status array to track the order lifecycle
                {'status': 'Submitted', 'timestamp': datetime.now()}
            ]
        }

        # Insert the order into the orders collection
        order_new = mongo.db.orders.insert_one(order)

        # Handle payment processing
        if payment_type == 'Cash':
            transaction_status = 'Pending'
        else:
            transaction_status = 'Paid'

        transaction = {
            'order_id': ObjectId(str(order_new.inserted_id)),  # Convert ObjectId to string
            'amount': total_amount,
            'payment_type': payment_type,
            'payment_status': transaction_status,  # 'completed' for cash, 'pending' for online
            'transaction_date': datetime.now()
        }

        # Insert the transaction record into the transactions collection
        mongo.db.transactions.insert_one(transaction)

        # Step 1: Assign employee to the order (without adding to status)
        assign_order_to_employee(order_new.inserted_id)

        # Step 2: Update the order status to 'assigned' in the statuses array (without employee info)
        mongo.db.orders.update_one(
            {'_id': order_new.inserted_id},
            {'$push': {'status': {'status': 'Assigned', 'timestamp': datetime.now()}}}
        )

        # Send email to the client with order details
        client_email = session['email']  # Assuming the user's email is in `session`
        send_order_confirmation_email(client_email, order, ordered_products)

        return jsonify(
            {'status': 'success', 'message': 'Order placed and assigned successfully',
             'order_id': str(order_new.inserted_id),
             'url': "/client/dashboard"}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def assign_order_to_employee(order_id):
    # Fetch the queue of employees who have role "employee" and status "true"
    employees = list(mongo.db.users.find(
        {'role': 'employee', 'status': 'true'}))  # Assuming the role and status are in 'users' collection
    if not employees:
        return None

    # Fetch the current queue pointer (index of the last assigned employee)
    queue_data = mongo.db.queue.find_one({})  # Assuming the queue information is stored in a 'queue' collection

    if not queue_data:
        # If no queue data exists, initialize it with the first employee
        queue_data = {
            'current_employee_index': 0
        }
        mongo.db.queue.insert_one(queue_data)

    # Get the current employee index
    current_employee_index = queue_data['current_employee_index']

    # Find the next employee in the queue
    next_employee_index = (current_employee_index + 1) % len(employees)  # Round-robin logic

    # Assign the next employee
    assigned_employee = employees[next_employee_index]

    # Update the queue pointer to the new employee
    mongo.db.queue.update_one({}, {'$set': {'current_employee_index': next_employee_index}})

    # Create an assignment record in the 'assignments' collection
    assignment = {
        'order_id': ObjectId(order_id),
        'employee_id': assigned_employee['_id'],
        'assigned_date': datetime.now(),
        'status': 'Assigned'
    }
    mongo.db.assigned_tasks.insert_one(assignment)

    return assigned_employee


def send_order_confirmation_email(email, order, products):
    try:
        product_details = "\n".join(
            [f"{p['product_name']} - {p['quantity']} x {p['price']} = {p['amount']}" for p in products]
        )

        msg_body = f"""
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
                        <h1 style="margin: 0;font-size: 24px;font-weight: 500;color: #1f1f1f;">Order Details</h1>
                        <p style="margin: 0;margin-top: 17px;font-size: 16px;font-weight: 500;">
                            Hi Dear,
                        </p>
                        <p style="margin: 0;margin-top: 17px;font-weight: 500;letter-spacing: 0.56px;">
                            Thank you for your order!<br/>
                            
                            <b>Products:</b> {product_details}<br/><br/>
                            <b>Total Amount:</b> {order['total_amount']}<br/>
                            <b>Payment Type:</b> {order['payment_type']}<br/>
                            <b>Order Date:</b> {order['order_date'].strftime('%Y-%m-%d')}
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

        # msg_body = f"""
        # Hello,
        #
        # Thank you for your order!
        #
        # Order Details:
        # Order ID: {str(order['_id'])}
        # Total Amount: {order['total_amount']}
        # Payment Type: {order['payment_type']}
        # Order Date: {order['order_date'].strftime('%Y-%m-%d')}
        #
        # Products:
        # {product_details}
        #
        # Regards,
        # Your Company Name
        # """

        subject = "Order Confirmation"

        send_email(subject, email, msg_body)

        print("Email sent successfully!")

    except Exception as e:
        print(f"Failed to send email: {str(e)}")


@client.route('/download_bill/<order_id>', methods=['GET'], endpoint='download_bill')
# @token_required
def download_bill(order_id):
    try:
        # Fetch the order details from the database
        order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
        # print(order)
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404

        # Ensure 'products' is iterable (a list) before passing to the template
        # if 'products' not in order or not isinstance(order['products'], list):
        #     return jsonify({'status': 'error', 'message': 'No products found in the order'}), 400

        # Render the bill template with order data
        return render_template('order/bill_template.html', order=order)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
