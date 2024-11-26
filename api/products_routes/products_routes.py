# import os
# from datetime import datetime
import os
from datetime import datetime

# from cachelib import file
from flask import Blueprint, request, redirect, jsonify, render_template, session

# from app import app
# from flask_uploads import UploadSet, configure_uploads, IMAGES

# from app import app
from middleware.auth_middleware import token_required
from config import mongo
from bson import ObjectId
from middleware.page_visibility_middleware import role_required

product = Blueprint('product', __name__)


@product.route('/addproduct', methods=['GET'])
@token_required
@role_required('products', 'create')
def view_add_product(current_user):
    areas = list(mongo.db.areas.find({'status': 'true'}))

    used_area_ids = mongo.db.products.distinct('area_id')  # Fetch areas that are already used by products

    # Filter out areas that are already in use by products
    available_areas = [area for area in areas if area['_id'] not in used_area_ids]
    # print(available_areas)  # Debugging purpose to see which areas are available

    return render_template('product/add_product.html', areas=available_areas)


@product.route('/updateproduct/<int:sku>', methods=['GET'], endpoint='updateproduct')
@token_required
@role_required('products', 'edit')
def view_update_product(current_user, sku):
    areas = list(mongo.db.areas.find({'status': 'true'}))
    used_area_ids = mongo.db.products.distinct('area_id')

    products = list(mongo.db.products.aggregate([
        {
            '$lookup': {
                'from': 'areas',
                'localField': 'area_id',
                'foreignField': '_id',
                'as': 'area_info'
            }
        },
        {
            '$match': {'sku': sku}
        }
    ]))

    available_areas = [area for area in areas if area['_id'] not in used_area_ids]
    # print(products[0]['area_info'][0]['area_name'])
    if not products:
        return jsonify({'status': 'error', 'message': 'Products not found'}), 404

    return render_template("product/update_product.html", products=products, available_areas=available_areas)


@product.route('/addproduct', methods=['POST'], endpoint='addproduct')
@token_required
@role_required('products', 'create')
def add_product(current_user):
    try:
        # check products are extsting or not
        # sku = request.form.get('sku')
        # found = mongo.db.products.find({'sku': sku})
        # if found:
        #     return jsonify({'message': 'Products already exists'}), 400

        photo = request.files['photo']
        ext = photo.filename.rsplit('.', 1)[1].lower()
        new_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        from app import app
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'products', new_filename)
        normalized_path = filepath.replace('\\', '/')
        print(normalized_path)
        try:
            photo.save(normalized_path)
            print(f'File saved at: {normalized_path}')
        except Exception as e:
            return jsonify({'error': str(e)}), 500

        # # Get form data
        product_name = request.form.get('productName')
        sku = request.form.get('sku')
        unit = request.form.get('unit')
        price = request.form.get('price')
        status = request.form.get('status')
        description = request.form.get('description')
        min = request.form.get('min')
        max = request.form.get('max')
        area = request.form.get('area')
        #
        found = list(mongo.db.products.find({'sku': sku}))
        if found:
            print(found)
            return jsonify({'message': 'Product already exists'}), 400
        # created_by = request.form.get('createdBy')
        role = session.get('role')
        product = {
            'product_name': product_name,
            'sku': int(sku),
            'unit': int(unit),
            'min': int(min),
            'max': int(max),
            'price': float(price),
            'status': status,
            'description': description,
            'created_by': role,
            'area_id': ObjectId(area),
            'image': normalized_path,
            'created_at': datetime.now()
        }

        # Insert the product into MongoDB
        mongo.db.products.insert_one(product)

        # On success, redirect to the dashboard
        print('Product added successfully!')
        return redirect('/product/viewproduct')

    except Exception as e:
        # Handle errors and provide feedback
        print(f'An error occurred: {str(e)}')
        return redirect('/product/viewproduct')


@product.route('/viewproduct', methods=['GET'], endpoint='product_list')
@token_required
@role_required('products', 'view')
def get_all_products(current_user):
    try:
        # Fetch all products from the products collection
        # products_list = list(mongo.db.products.find())
        # print(current_user)

        products_list = list(mongo.db.products.aggregate([
            {
                '$lookup': {
                    'from': 'areas',
                    'localField': 'area_id',
                    'foreignField': '_id',
                    'as': 'area_info'
                }
            }
        ]))

        # print(products_list)
        return render_template("product/view_product.html", products_list=products_list)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@product.route('/updateproduct/<int:sku>', methods=['POST'], endpoint='update_product')
@token_required
@role_required('products', 'edit')
def update_user(current_user, sku):
    try:
        # print(sku)
        product_name = request.form.get('productName')
        price = request.form.get('price')
        status = request.form.get('status')
        description = request.form.get('description')
        min = request.form.get('min')
        max = request.form.get('max')
        area = request.form.get('area')

        role = session.get('role')
        # print(role)
        mongo.db.products.update_one(
            {'sku': sku},
            {
                '$set': {
                    'product_name': product_name,
                    'min': int(min),
                    'max': int(max),
                    'price': float(price),
                    'status': status,
                    'description': description,
                    'update_by': role,
                    'area_id': ObjectId(area),
                }
            }
        )
        # print("sku")
        return redirect('/product/viewproduct')

    except Exception as e:
        # flash(f"Error updating user: {str(e)}", 'error')
        return redirect('/product/viewproduct')


@product.route('/scan/<int:sku>', methods=['GET'], endpoint='productsscan')
# @token_required
def fetch_product_by_sku(sku):  # Reorder parameters, so current_user is the first argument
    try:
        # print(f"Current User: {current_user}")  # Debug to ensure current_user is received
        # print(f"SKU: {sku}")  # Debug to ensure sku is received
        product = mongo.db.products.find_one({"sku": sku})
        # print(product)
        if product:
            return jsonify({
                "product_name": product['product_name'],
                "sku": product['sku']
            }), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
