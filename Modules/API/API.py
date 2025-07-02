from functools import wraps
from flask import Blueprint, jsonify, request

from Modules.Database.Database import SQLiteDatabase
from Modules.Winget.Functions import get_winget_Settings, authenticate_Client

api_bp = Blueprint('api_bp', __name__)


def check_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        settings = get_winget_Settings()
        if bool(int(settings.get('CLIENT_AUTHENTICATION', '0'))):
            auth_key = request.form.get('Auth-Token')
            if not auth_key:
                return jsonify({"Error": "Unauthorized"}), 401
            try:
                if not authenticate_Client(auth_key, request.remote_addr, settings):
                    return jsonify({"Message": "Unauthorized"}), 401
            except Exception:
                return jsonify({"Message": "Invalid token format"}), 400
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/get_packages', methods=["POST"])
@check_authentication
def get_packages():
    db = SQLiteDatabase()
    auth_key = request.form.get('Auth-Token', '')

    if auth_key == '':
        data = db.get_All_Packages()
    else:
        data = db.get_All_Packages()
        blacklist = db.get_Blacklist_for_client(auth_key)
        data = [d for d in data if d['PACKAGE_ID'] not in blacklist]

    del db
    return jsonify(data), 200
