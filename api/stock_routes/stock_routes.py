from flask import Blueprint, request, jsonify, render_template
from config import mongo
from datetime import datetime

from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

stock = Blueprint('stock', __name__)


@stock.route('/managestock', methods=['GET'], endpoint='addstock')
@stock.route('/product/managestock/<stock_id>', methods=['GET'], endpoint='addstockproducts')
@token_required
@role_required('stocks', 'create')
def stock_home(current_user, stock_id=None):
    if stock_id:
        return render_template('stock/add_stock.html', stock_id=stock_id)
    else:
        return render_template('stock/add_stock.html', stock_id=stock_id)


# @stock.route('/removestock', methods=['GET'], endpoint='stock_remove')
# @token_required
# def remove_stock(current_user):
#     return render_template('stock/remove_stock.html')


# @stock.route('/viewstock', methods=['GET'], endpoint='stock_view')
# @token_required
# @role_required('stocks', 'view')
# def view_stock(current_user):
#     return render_template('stock/view_stock.html')


@stock.route('/addstock', methods=['POST'], endpoint='addStock')
@token_required
@role_required('stocks', 'create')
def add_stock(current_user):
    try:
        # Fetch item_id and quantity to add
        sku = int(request.json.get('sku'))
        qty_to_add = request.json.get('qty')

        # Fetch current stock for the item
        stock_entry = mongo.db.stock.find_one({"sku": sku}, sort=[("date", -1)])

        new_total_qty = stock_entry['total_qty'] + qty_to_add if stock_entry else qty_to_add

        # Insert new stock entry
        new_stock_entry = {
            "sku": int(sku),
            "date": datetime.now(),
            "+qty": qty_to_add,
            "-qty": 0,  # Since we're adding, -qty is 0
            "total_qty": new_total_qty
        }

        mongo.db.stock.insert_one(new_stock_entry)

        return jsonify({"message": "Stock added successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@stock.route('/removestock', methods=['POST'], endpoint='removeStock')
@token_required
def remove_stock(current_user):
    try:
        sku = int(request.json.get('sku'))
        qty_to_remove = request.json.get('qty')
        print(qty_to_remove)
        print(sku)
        # Fetch current stock for the item
        stock_entry = mongo.db.stock.find_one({"sku": sku}, sort=[("date", -1)])
        print(stock_entry)
        if not stock_entry or stock_entry['total_qty'] < qty_to_remove:
            return jsonify({"error": "Not enough stock available 1"}), 400

        # Calculate new total quantity
        new_total_qty = stock_entry['total_qty'] - qty_to_remove

        # Insert new stock removal entry
        new_stock_entry = {
            "sku": int(sku),
            "date": datetime.now(),
            "+qty": 0,  # Since we're removing, +qty is 0
            "-qty": qty_to_remove,
            "total_qty": new_total_qty
        }

        mongo.db.stock.insert_one(new_stock_entry)

        return jsonify({"message": "Stock removed successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@stock.route('/<sku>', methods=['GET'], endpoint='get_stock')
@token_required
# @role_required('stock')
def get_stock(current_user, sku):
    try:
        # Fetch and sort stock entries for the given SKU
        stock_entries = mongo.db.stock.find({"sku": int(sku)}).sort('date', -1)
        stock_list = list(stock_entries)

        # Convert ObjectId to string for JSON serialization
        for stock in stock_list:
            stock['_id'] = str(stock['_id'])

        # Return the list of stock entries
        return jsonify(stock_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
