from bson import ObjectId
from flask import Flask, request, jsonify, render_template, Blueprint
from config import mongo
from middleware.auth_middleware import token_required
from middleware.page_visibility_middleware import role_required

settings = Blueprint('settings', __name__)


@settings.route('/settings', methods=['GET'])
# @role_required('stock_page')
@token_required
def settings_home(current_user):
    roles_data = mongo.db.users.distinct('role')
    print(roles_data)
    # return render_template("page_visibility/page_visibility.html")
    return render_template('page_visibility/page_visibility.html', roles=roles_data)


@settings.route('/roles/<string:role>', methods=['GET'] ,endpoint='roles')
@token_required
def show_roles(current_user, role):
    # Fetch roles and page access data for the specified role
    roles_data = mongo.db.page_visibility.find()

    role_permissions = {}
    for page in roles_data:
        page_name = page['page_name']
        permissions = page['roles'].get(role, {}).get('permissions', {})
        role_permissions[page_name] = {
            "permissions": permissions
        }

    print(role_permissions)
    return render_template('page_visibility/page.html', role=role, role_permissions=role_permissions)


@settings.route('/update_permission', methods=['POST'],endpoint='update_permission')
@token_required
def update_permission(current_user):
    data = request.get_json()
    print(data)
    page_name = data['page_name']
    role = data['role']
    permission_type = data['permission_type']
    value = data['value']

    # Update the permission in the database
    updated = mongo.db.page_visibility.update_one(
        {'page_name': page_name, f'roles.{role}': {'$exists': True}},
        {'$set': {f'roles.{role}.permissions.{permission_type}': value}}
    )
    print(updated)

    return jsonify({"message": "Permission updated successfully!"})