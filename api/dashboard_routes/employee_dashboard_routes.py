# from crypt import methods
from datetime import datetime
# from email.policy import default

from flask import Flask, request, jsonify, render_template, Blueprint, session
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

from config import mongo
from bson.objectid import ObjectId

employee = Blueprint('employee', __name__)


@employee.route('/dashboard', methods=['GET'], endpoint='employee_dashboard')
@employee.route('/dashboard/<employee_id>', methods=['GET'], endpoint='employee_dashboard_with_id')
@token_required
@role_required('employee_dashboard', 'view')
def dashboard(current_user, employee_id=None):
    try:
        if employee_id:
            userid = employee_id
        else:
            userid = session['user_id']

        # print(userid)
        assigned_tasks = list(mongo.db.assigned_tasks.aggregate([
            {
                '$match': {
                    'employee_id': ObjectId(userid),  # Match the employee_id
                }
            },
            {
                '$lookup': {
                    'from': 'orders',  # Join with the orders collection
                    'localField': 'order_id',  # Field in assignments collection
                    'foreignField': '_id',  # Field in orders collection
                    'as': 'order_details'
                }
            },
            {
                '$unwind': '$order_details'  # Unwind the order details array
            },
            {
                '$lookup': {
                    'from': 'users',  # Join with the users collection
                    'localField': 'order_details.user_id',  # Field in order details
                    'foreignField': '_id',  # Field in users collection
                    'as': 'user_details'
                }
            },
            {
                '$unwind': '$user_details'  # Unwind the user details array
            },
            {
                '$unwind': '$order_details.products'  # Unwind products
            },
            {
                '$addFields': {
                    'order_details.products.product_id': {
                        '$convert': {
                            'input': '$order_details.products.product_id',
                            'to': 'objectId',
                            'onError': None  # Avoid conversion failures
                        }
                    }
                }
            },
            {
                '$lookup': {
                    'from': 'products',  # Join with the products collection
                    'localField': 'order_details.products.product_id',  # Field in order details products
                    'foreignField': '_id',  # Field in products collection
                    'as': 'product_details'
                }
            },
            {
                '$unwind': '$product_details'  # Unwind the product details array
            },
            {
                '$lookup': {
                    'from': 'areas',  # Join with the areas collection
                    'localField': 'product_details.area_id',  # Field in products collection (area_id)
                    'foreignField': '_id',  # Field in areas collection
                    'as': 'area_details'
                }
            },
            {
                '$unwind': '$area_details'  # Unwind the area details array
            },
            {
                '$group': {
                    '_id': {
                        'assignment_id': '$_id',
                        'order_id': '$order_id',
                        'employee_id': '$employee_id',
                        'assigned_date': '$assigned_date',
                        'status': '$status',
                        'order_details': '$order_details._id',
                        'user_id': '$order_details.user_id',
                        'user_full_name': '$user_details.full_name'
                    },
                    'products': {
                        '$push': {
                            'product_id': '$order_details.products.product_id',
                            'product_name': '$order_details.products.product_name',
                            'quantity': '$order_details.products.quantity',
                            'price': '$order_details.products.price',
                            'area_name': '$area_details.area_name'
                        }
                    }
                }
            },
            {
                '$sort': {
                    'assigned_date': -1
                }
            },
            {
                '$project': {
                    '_id': 0,  # Hide the default _id from the output
                    'assignment_id': '$_id.assignment_id',
                    'order_id': '$_id.order_id',
                    'employee_id': '$_id.employee_id',
                    'assigned_date': '$_id.assigned_date',
                    'status': '$_id.status',
                    'order_details._id': '$_id.order_details',
                    'order_details.user_id': '$_id.user_id',
                    'products': 1,  # Output the array of products
                    'user_details.full_name': '$_id.user_full_name'
                }
            }
        ]))

        # print(assigned_tasks[0].user_details.full_name)
        # print(assigned_tasks)
        if employee_id:
            return render_template('dashboard/view_task.html', assigned_tasks=assigned_tasks)
        else:
            return render_template('dashboard/employee_dashboard.html', assigned_tasks=assigned_tasks)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

    # return render_template('dashboard/employee_dashboard.html')


@employee.route('/update/<order_id>', methods=['POST'], endpoint='update')
@token_required
@role_required('employee_dashboard', 'edit')
def update_order_status(current_user, order_id):
    try:
        # print(f"updated : {order_id}")

        # Step 1: Update order status to 'Shipment Ready' in the orders collection
        mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$push': {
                'status': {
                    'status': 'Shipment Ready',
                    'updated_at': datetime.now()
                }
            }}
        )
        # print("1")

        # Step 2: Update the assigned_tasks collection
        mongo.db.assigned_tasks.update_one(
            {'order_id': ObjectId(order_id)},
            {
                '$set': {
                    'status': 'Shipment Ready'  # Set current status directly
                }
            }
        )

        # print("2")
        # Fetch the order details
        order = mongo.db.orders.find_one({'_id': ObjectId(order_id)})
        if not order:
            return jsonify({'status': 'error', 'message': 'Order not found'}), 404

        # Fetch the client (user) information
        client = mongo.db.users.find_one({'_id': ObjectId(order['user_id'])})
        if not client:
            return jsonify({'status': 'error', 'message': 'Client not found'}), 404

        client_city = client['city']
        # print("3")

        # Step 3: Find available suppliers in the client's city
        available_suppliers = list(mongo.db.users.find({
            'city': client_city,
            'role': 'supplier',
            'status': 'true'  # Only get active suppliers
        }))

        if not available_suppliers:
            return jsonify({'status': 'error', 'message': 'No available suppliers in the client\'s city'}), 404

        # print("4")

        # Step 4: Assign the order to the first available supplier
        assigned_supplier = available_suppliers[0]

        # Step 5: Push the supplier assignment into assigned_tasks
        mongo.db.assigned_tasks.update_one(
            {'order_id': ObjectId(order_id)},
            {
                '$set': {
                    'supplier_id': ObjectId(assigned_supplier['_id']),  # Add supplier ID
                    'status': 'Assigned to Supplier'  # Update the current status
                }
            }
        )

        # Update the orders collection again to add the assignment status
        mongo.db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {'$push': {
                'status': {
                    'status': 'Assigned to Supplier',
                    'updated_at': datetime.now()
                }
            }}
        )
        # print("5")
        return jsonify({'status': 'success', 'message': 'Order assigned to supplier successfully.'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
