from functools import wraps
from flask import Blueprint, jsonify, request, send_file

from Modules.Database.Database import SQLiteDatabase
from Modules.Winget.Functions import get_winget_Settings, authenticate_Client
from settings import PATH_LOGOS

api_bp = Blueprint('api_bp', __name__)


def check_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        settings = get_winget_Settings()
        if bool(int(settings.get('CLIENT_AUTHENTICATION', '0'))):
            auth_key = request.form.get('Auth-Token')
            client = request.form.get('Client', 0)
            if not auth_key:
                return jsonify({"Error": "Unauthorized"}), 401
            try:
                if not authenticate_Client(auth_key, request.remote_addr, settings, client):
                    return jsonify({"Message": "Unauthorized"}), 401
            except Exception:
                return jsonify({"Message": "Invalid token format"}), 400
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/client_version', methods=["POST"])
@check_authentication
def client_version():
    return jsonify({"Version": "2.0.0.0"}), 200


@api_bp.route('/get_packages', methods=["POST"])
@check_authentication
def get_packages():
    db = SQLiteDatabase()
    auth_key = request.form.get('Auth-Token', '')

    data = db.get_All_Packages(False)

    for d in data:
        d['VERSIONS'] = [v['VERSION'] for v in db.get_All_Versions_from_Package(d['PACKAGE_ID'])]

    if len(auth_key) > 0:
        blacklist = db.get_Blacklist_for_client(auth_key)
        data = [d for d in data if d['PACKAGE_ID'] not in blacklist]

    del db
    return jsonify(data), 200


@api_bp.route('/get_logo/<logo_name>', methods=["GET"])
def get_logo(logo_name):
    return send_file(fr"{PATH_LOGOS}\{logo_name}")
