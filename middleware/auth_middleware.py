from flask import request, jsonify, redirect, url_for
from functools import wraps
import jwt


def token_required(f):
    def decorator(*args, **kwargs):
        token = request.cookies.get('token')  # Fetch the token from cookies
        if not token:
            return redirect('/')

        try:
            data = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        # print(data)
        current_user = data.get('email')
        print(current_user)
        return f(current_user, *args, **kwargs)

    return decorator
