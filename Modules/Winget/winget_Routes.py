import json
import os

from flask import Blueprint, jsonify, request, send_from_directory, current_app, redirect, Response, send_file
from datetime import timedelta, datetime
from functools import wraps

from Modules.PreIndexed.Manifests import rest_response_to_manifests
from Modules.Functions import get_Auth_Token_from_Header, get_serializer
from Modules.Winget.Functions import generate_search_Manifest, generate_Installer_Manifest, get_winget_Settings, filter_entries_by_package_match_field, authenticate_Client, write_log, authorize_IP_Range
from main_extensions import csrf
from settings import PATH_FILES, URL_PACKAGE_DOWNLOAD, PATH_LOGOS, PATH_CERTIFICATES

winget_routes = Blueprint('winget_routes', __name__)


@winget_routes.before_request
def before_request():
    if not authorize_IP_Range(request.remote_addr):
        return "Unauthorized", 403
    return None


def check_authentication(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        settings = get_winget_Settings()
        if bool(int(settings.get('INDEXED_DB_ACTIV', '0'))):
            return jsonify({"ErrorCode": 404, "ErrorMessage": "Not found"}), 404

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
    channel = request.args.get("Channel")
    result = generate_Installer_Manifest(package_id, version, channel, client_auth_token, get_serializer(current_app.config["DOWNLOAD_KEY"]))
    return jsonify(result)


@winget_routes.route('/manifestSearch', methods=['POST'])
@csrf.exempt
@check_authentication
def manifestSearch():
    def run_match(entry: dict, client_auth_token: str) -> list:
        rm = entry['RequestMatch']
        return generate_search_Manifest(
            str(rm.get('KeyWord', '')),
            str(rm.get('MatchType', 'CaseInsensitive')),
            entry.get('PackageMatchField', 'PackageIdentifier'),
            client_auth_token)

    client_auth_token = get_Auth_Token_from_Header(request.headers)
    result = {"Data": []}

    try:
        data = request.get_json(force=True, silent=True)
    except OSError:
        return jsonify(result), 400

    if data is None:
        return jsonify(result), 400

    query = data.get('Query')
    if isinstance(query, dict):
        keyword = str(query.get('KeyWord', ''))
        match_type = str(query.get('MatchType', 'Substring'))
        found = {}
        for field in ("PackageName", "PackageIdentifier"):
            for p in generate_search_Manifest(keyword, match_type, field, client_auth_token):
                found.setdefault(p['PackageIdentifier'], p)
        result['Data'] = list(found.values())
        return jsonify(result)

    inclusions = filter_entries_by_package_match_field(data.get('Inclusions') or [])
    filters = filter_entries_by_package_match_field(data.get('Filters') or [])

    found = {}
    if inclusions:
        for entry in inclusions:
            for p in run_match(entry, client_auth_token):
                found.setdefault(p['PackageIdentifier'], p)
    elif filters:
        for p in run_match(filters[0], client_auth_token):
            found.setdefault(p['PackageIdentifier'], p)
        filters = filters[1:]

    for entry in filters:
        ids = {p['PackageIdentifier'] for p in run_match(entry, client_auth_token)}
        found = {k: v for k, v in found.items() if k in ids}

    result['Data'] = list(found.values())
    return jsonify(result)


@winget_routes.route('/indexed/source.msix', methods=['GET', 'HEAD'])
def source():
    if current_app.config['INDEXED_DB_ACTIV'] == "1":
        file_path = os.path.join(PATH_CERTIFICATES, "source.msix")
        return send_file(file_path, mimetype='application/octet-stream', as_attachment=True, download_name='source.msix')
    return jsonify({"ErrorCode": 404, "ErrorMessage": "Not found"}), 404


@winget_routes.route('/indexed/source2.msix', methods=['GET', 'HEAD'])
def source2():
    if current_app.config['INDEXED_DB_ACTIV'] == "1":
        file_path = os.path.join(PATH_CERTIFICATES, "source.msix")
        return send_file(file_path, mimetype='application/octet-stream', as_attachment=True, download_name='source.msix')
    return jsonify({"ErrorCode": 404, "ErrorMessage": "Not found"}), 404


@winget_routes.route('/indexed/manifest/<package_id>/<version>/<channel>/<hash>', methods=['GET'])
def indexed_manifest(package_id, version, channel, hash):
    if current_app.config['INDEXED_DB_ACTIV'] == "1":
        data = generate_Installer_Manifest(package_id, version, channel, "", use_serializer=False)
        installer, installer_bytes = rest_response_to_manifests(data)
        return Response(installer, mimetype='text/yaml')
    return jsonify({"ErrorCode": 404, "ErrorMessage": "Not found"}), 404


@winget_routes.route('/download/<package_name>', methods=['GET'])
def download(package_name):
    try:
        serializer = get_serializer(current_app.config["DOWNLOAD_KEY"])
        package_name = serializer.loads(package_name, max_age=3600)
    except:
        if not os.path.exists(os.path.join(PATH_FILES, package_name)) or current_app.config['INDEXED_DB_ACTIV'] != "1":
            return "Link expired!", 403

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


@winget_routes.route('/logo/<logo_name>', methods=['GET'])
def get_package_logo(logo_name):
    try:
        serializer = get_serializer(current_app.config["DOWNLOAD_KEY"])
        logo_name = serializer.loads(logo_name, max_age=600)
    except:
        if not os.path.exists(os.path.join(PATH_LOGOS, logo_name)) or current_app.config['INDEXED_DB_ACTIV'] != "1":
            return "Link expired!", 403

    return send_from_directory(PATH_LOGOS, logo_name)
