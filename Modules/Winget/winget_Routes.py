import sys

from flask import Blueprint, jsonify, request, send_file

from Modules.Winget.Functions import generate_search_Manifest, generate_Installer_Manifest, get_winget_Settings, \
    filter_entries_by_package_match_field

winget_routes = Blueprint('winget_routes', __name__)


@winget_routes.route('/information', methods=["GET"])
def information():
    data = get_winget_Settings()
    data = {"Data": {
                    "SourceIdentifier": data.get('SERVER_NAME', 'Winget-Repo'),
                    "ServerSupportedVersions": data.get('CLIENT_VERSIONS', '1.9.0').split(","),
                 }
            }
    return jsonify(data)


@winget_routes.route('/packageManifests/<package_id>', methods=['GET'])
def get_package_manifest(package_id):
    version = request.args.get("Version")
    result = generate_Installer_Manifest(package_id, version)
    return jsonify({"Data": result})


@winget_routes.route('/manifestSearch', methods=['POST'])
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
