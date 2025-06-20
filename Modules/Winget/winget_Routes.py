import sys
import json

from functools import wraps
from flask import Blueprint, jsonify, request, send_file

from Modules.Winget.Functions import generate_search_Manifest, generate_Installer_Manifest, get_winget_Settings, \
    filter_entries_by_package_match_field, authenticate_Client

winget_routes = Blueprint('winget_routes', __name__)


def check_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        settings = get_winget_Settings()
        if bool(int(settings.get('CLIENT_AUTHENTICATION', '0'))):
            header_value = request.headers.get('Windows-Package-Manager')
            if not header_value:
                return jsonify({"ErrorCode": 401, "ErrorMessage": "Unauthorized"}), 401
            try:
                token_data = json.loads(header_value.replace("'", '"'))
                if not authenticate_Client(token_data.get("Token"), request.remote_addr, settings):
                    return jsonify({"ErrorCode": 401, "ErrorMessage": "Unauthorized"}), 401
            except Exception:
                return jsonify({"ErrorCode": 400, "ErrorMessage": "Invalid token format"}), 400
        return f(*args, **kwargs)
    return decorated_function


@winget_routes.route('/information', methods=["GET"])
@check_authentication
def information():
    settings = get_winget_Settings()
    data = {"Data": {
            "SourceIdentifier": settings.get('SERVER_NAME', 'Winget-Repo'),
            "ServerSupportedVersions": settings.get('CLIENT_VERSIONS', '1.9.0').split(","),
            "SourceAgreements": {
                "AgreementsIdentifier": "v1",
                "Agreements": [
                    {
                        "AgreementLabel": "Terms of Use",
                        "Agreement": "Please accept the terms of use.",
                        "AgreementUrl": f"https://{request.host}"
                    }
                ]
            }
        }
    }
    return jsonify(data)


@winget_routes.route('/packageManifests/<package_id>', methods=['GET'])
@check_authentication
def get_package_manifest(package_id):
    version = request.args.get("Version")
    result = generate_Installer_Manifest(package_id, version)
    return jsonify({"Data": result})


@winget_routes.route('/manifestSearch', methods=['POST'])
@check_authentication
def manifestSearch():
    result = {"Data": []}
    if 'Query' in (data := request.json):
        result['Data'] = generate_search_Manifest(data['Query'].get('KeyWord', ''), data['Query'].get('MatchType', 'Substring'), "PackageName")
    else:
        key = ""

        if 'Inclusions' in data:
            key = 'Inclusions'
        elif 'Filters' in data:
            key = 'Filters'

        if key != "":
            temp = []
            for d in filter_entries_by_package_match_field(data[key]):
                dum = generate_search_Manifest(d['RequestMatch'].get('KeyWord', ''), d['RequestMatch'].get('MatchType', 'CaseInsensitive'), d.get('PackageMatchField', 'PackageIdentifier'))
                for du in dum:
                    if du['PackageIdentifier'] not in [t['PackageIdentifier'] for t in temp]:
                        temp.append(du)
            result['Data'] = temp
    return jsonify(result)


@winget_routes.route('/download/<package_name>', methods=['GET'])
def download(package_name):
    return send_file(fr"{sys.path[0]}\Files\{package_name}")
