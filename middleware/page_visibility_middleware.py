from functools import wraps
from flask import session, redirect, jsonify, render_template
from config import mongo


def role_required(page_name, action):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Fetch user role from session (assuming it's stored in the session)
            role = session.get('role')  # This could be 'manager', 'employee', etc.

            if not role:
                # If no role is found, redirect to login or show a message
                return redirect('/')  # Assuming you have a login route

            # Fetch role information for the specific page
            visibility = mongo.db.page_visibility.find_one({"page_name": page_name})

            if visibility:
                # Get the permissions for the user's role
                role_permissions = visibility.get('roles', {}).get(role, {}).get('permissions', {})

                # Check if the specific action is allowed
                if role_permissions.get(action) == 1:
                    # If the user has the required permission, proceed to the page
                    return f(*args, **kwargs)
                else:
                    # If the user does not have the required permission, show an error message
                    return render_template('error_handler/access_denied.html' , action=action, page_name=page_name)

                    # return jsonify(
                    #     {"message": f"Access Denied: You do not have permission to {action} on {page_name}"}), 403
            else:
                # return jsonify({"message": "Page visibility settings not found"}), 404
                return render_template('error_handler/error_404.html' , page_name=page_name)

        return decorated_function

    return decorator