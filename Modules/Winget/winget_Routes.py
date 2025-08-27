import json

from flask import Blueprint, jsonify, request, send_from_directory, current_app, redirect
from datetime import timedelta, datetime
from functools import wraps

from Modules.Functions import get_Auth_Token_from_Header
from Modules.Winget.Functions import generate_search_Manifest, generate_Installer_Manifest, get_winget_Settings, filter_entries_by_package_match_field, authenticate_Client, write_log
from main_extensions import csrf
from settings import PATH_FILES, URL_PACKAGE_DOWNLOAD

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

    data = {
        "Data": {
            "SourceIdentifier": settings.get('SERVERNAME', 'Winget-Repo'),
            "ServerSupportedVersions": settings.get('CLIENT_VERSIONS', '1.9.0').split(",")
        }
    }

    if settings.get('TOS') == '1':
        data["Data"]["SourceAgreements"] = {
            "AgreementsIdentifier": "v1",
            "Agreements": [
                {
                    "AgreementLabel": "Terms of Use",
                    "Agreement": "Please accept the terms of use.",
                    "AgreementUrl": f"https://{request.host}/ui/settings/terms"
                }
            ]
        }
    return jsonify(data)


@winget_routes.route('/packageManifests/<package_id>', methods=['GET'])
@check_authentication
def get_package_manifest(package_id):
    client_auth_token = get_Auth_Token_from_Header(request.headers)
    version = request.args.get("Version")
    result = generate_Installer_Manifest(package_id, version, client_auth_token)
    return jsonify(result)


@winget_routes.route('/manifestSearch', methods=['POST'])
@csrf.exempt
@check_authentication
def manifestSearch():
    client_auth_token = get_Auth_Token_from_Header(request.headers)

    result = {"Data": []}
    if 'Query' in (data := request.json):
        result['Data'] = generate_search_Manifest(data['Query'].get('KeyWord', ''), data['Query'].get('MatchType', 'Substring'), "PackageName", client_auth_token)
    else:
        key = ""

        if 'Inclusions' in data:
            key = 'Inclusions'
        elif 'Filters' in data:
            key = 'Filters'

        if key != "":
            temp = []
            for d in filter_entries_by_package_match_field(data[key]):
                dum = generate_search_Manifest(d['RequestMatch'].get('KeyWord', ''), d['RequestMatch'].get('MatchType', 'CaseInsensitive'), d.get('PackageMatchField', 'PackageIdentifier'), client_auth_token)
                for du in dum:
                    if du['PackageIdentifier'] not in [t['PackageIdentifier'] for t in temp]:
                        temp.append(du)
            result['Data'] = temp
    return jsonify(result)


@winget_routes.route('/download/<package_name>', methods=['GET'])
def download(package_name):
    key = (request.remote_addr, package_name)
    now = datetime.now()

    if key not in current_app.config['active_downloads'] or (now - current_app.config['active_downloads'][key]) > timedelta(seconds=30):
        write_log(key[0], key[1], "INSTALLATION/UPDATE")
    current_app.config['active_downloads'][key] = now

    if URL_PACKAGE_DOWNLOAD.upper() == "DEFAULT" or not URL_PACKAGE_DOWNLOAD.upper().startswith("HTTPS://"):
        return send_from_directory(PATH_FILES, package_name, as_attachment=True)
    else:
        dummy_url = URL_PACKAGE_DOWNLOAD
        if not dummy_url.endswith("/"):
            dummy_url += "/"
        dummy_url += package_name
        return redirect(dummy_url, code=302)
