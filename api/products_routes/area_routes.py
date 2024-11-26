from bson import ObjectId
from flask import Blueprint, render_template, request, jsonify, redirect

from config import mongo
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

area = Blueprint('area', __name__)


@area.route('/viewarea', methods=['GET'], endpoint='view')
@token_required
@role_required('areas', 'view')
def area_home(current_user):
    area = list(mongo.db.areas.find())
    return render_template('product/area.html', area=area)


@area.route('/addarea', methods=['POST'] , endpoint='add')
@token_required
@role_required('areas', 'create')
def add_area(current_user):
    try:
        # print(current_user)
        name = request.form.get('areaName')
        no_box = request.form.get('boxNo')
        # print(name)
        found = mongo.db.areas.find_one({'area_name': name})
        # print(list(found))
        # if found:
        #     # error = 'Area already exists'
        #     # return redirect('product/area.html', error=error)
        #     return jsonify({'message': 'area already exists'}), 400

        area_record = {
            "area_name": name,
            "no_box": int(no_box),
            "status": 'true'
        }

        # Insert the product into MongoDB
        mongo.db.areas.insert_one(area_record)
        return redirect('/area/viewarea')

    except Exception as e:
        return redirect('/area/viewarea')


@area.route('/updatearea/<area_id>', methods=['GET', 'POST'] , endpoint='update')
@token_required
@role_required('areas', 'edit')
def update_area(current_user, area_id):
    try:
        print(current_user)

        # Handle GET request to display the current area details
        if request.method == 'GET':
            area_record = mongo.db.areas.find_one({'_id': ObjectId(area_id)})
            if not area_record:
                return jsonify({'message': 'Area not found'}), 404

            # Render a template to edit the area (assuming you have an 'edit_area.html' template)
            return render_template('product/area.html', area_record=area_record)

        # Handle POST request to update the area details
        name = request.form.get('areaName')
        no_box = request.form.get('boxNo')

        # Check if the area exists
        area_record = mongo.db.areas.find_one({'_id': ObjectId(area_id)})
        if not area_record:
            return jsonify({'message': 'Area not found'}), 404

        # Prepare the update data
        update_data = {
            "$set": {
                "area_name": name,
                "no_box": int(no_box),
                "status": 'true'  # You can modify this as needed
            }
        }

        # Update the area in MongoDB
        mongo.db.areas.update_one({'_id': ObjectId(area_id)}, update_data)
        return redirect('/area/viewarea')

    except Exception as e:
        print(e)  # Log the error for debugging
        return redirect('/area/viewarea')

@area.route('/area_status', methods=['POST'])
@token_required
def user_status():
    data = request.get_json()

    user_id = data.get('user_id')  # User ID passed from the client-side
    new_status = data.get('status')  # New status (true/false)

    if user_id and new_status:
        # Update the user's status in the database
        result = mongo.db.areas.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'status': new_status}}
        )

        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Status update failed'})
    return jsonify({'success': False, 'message': 'Invalid request'}), 400
