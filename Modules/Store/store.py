from flask import Blueprint, render_template, request, flash, redirect, url_for
from uuid import uuid4
from hashlib import sha256
from functools import wraps
from pathlib import Path

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import parse_version, check_Internet_Connection
from Modules.Login.Login import logged_in, authenticate
from Modules.Store.Functions import get_All_Packages_from_DB, download_source_msix, get_package_path, download_file, get_All_InstallerInfos_from_Manifest
from Modules.Winget.Functions import get_winget_Settings
from settings import PATH_FILES, PATH_LOGOS

store_bp = Blueprint('store_bp', __name__, template_folder='templates', static_folder='static')


def store_enabled(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        settings = get_winget_Settings()
        if settings['PACKAGE_STORE'] == "0":
            flash("The Package Store is disabled!", "error")
            return redirect(url_for("ui_bp.index"))
        return f(*args, **kwargs)
    return decorator


@store_bp.route("/", methods=["GET"])
@logged_in
@authenticate
@store_enabled
def index():
    if not check_Internet_Connection():
        flash("Internet connection is required!", "error")
        return redirect(url_for("ui_bp.index"))

    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page
    search = request.args.get("search", "").strip()

    packages_raw = get_All_Packages_from_DB(search=search)

    db = SQLiteDatabase()
    current_packages = [p['PACKAGE_ID'] for p in db.get_All_Packages()]
    del db

    grouped = {}
    for row in packages_raw:
        if row[0] not in grouped:
            grouped[row[0]] = {
                "PACKAGE_ID": row[0],
                "PACKAGE_NAME": row[1],
                "PACKAGE_PUBLISHER": row[2],
                "VERSIONS": []
            }
        grouped[row[0]]["VERSIONS"].append(row[3])

    result = []
    for pkg in grouped.values():
        pkg["VERSIONS"] = sorted(pkg["VERSIONS"], key=parse_version, reverse=True)
        result.append(pkg)

    total_packages = len(result)
    result_paginated = result[offset:offset + per_page]
    total_pages = (total_packages + per_page - 1) // per_page
    return render_template("index_store.html", packages=result_paginated, current_page=page, total_pages=total_pages, search=search, current_packages=current_packages)


@store_bp.route("/refresh_source", methods=["POST"])
@logged_in
@authenticate
@store_enabled
def refresh_source():
    status = download_source_msix(True)

    if status:
        flash("Successfully updated winget source!", "success")
    else:
        flash("Error!", "success")
    return redirect(url_for("store_bp.index"))


@store_bp.route("/add_package/<package_id>", methods=["GET", "POST"])
@logged_in
@authenticate
@store_enabled
def add_package(package_id):
    if request.method == "POST":
        f_a_data = request.form
    else:
        f_a_data = request.args

    version = f_a_data.get("version", "")
    back = f_a_data.get("main", 0, int)
    search = f_a_data.get("search", '')
    page = f_a_data.get("page", 1, int)

    if bool(back):
        redir = "ui_bp.index"
    else:
        redir = "store_bp.index"

    package_path, manifest_name = get_package_path(package_id, version)
    if not package_path:
        flash("No package found!", "error")
        return redirect(url_for(redir))

    p_infos = get_All_InstallerInfos_from_Manifest(package_path, manifest_name)
    if not p_infos:
        flash("No versions found!", "error")
        return redirect(url_for(redir))

    db = SQLiteDatabase()
    package_exists = db.check_Package_exists(package_id)

    if request.method == "POST":
        data = request.form.to_dict()
        installer_ids = [int(i) for i in request.form.getlist('installer_ids')]

        if not data:
            flash("No data found!", "error")
            return redirect(url_for(redir))

        if not package_exists:
            file = request.files.get('Logo')
            logo_filename = f"{package_id}.png" if file else "dummy.png"
            if file:
                file.save(Path(PATH_LOGOS) / logo_filename)

            db.add_Package(package_id, data.get("package_name", "")[:25], data.get("package_publisher", "")[:25], data.get("package_description", "")[:150], logo_filename)
            db.db_commit()

            if len(installer_ids) == 0:
                flash("Successfully added package. No versions found!", "success")
                return redirect(url_for(redir))

        for i in installer_ids:
            if i > (len(p_infos['Installers']) - 1) < i:
                continue

            installer = p_infos['Installers'][i]
            locale_id = db.get_Locale_ID_by_Value(p_infos.get('Locale', 'en-US'))
            version_already_exists = not db.check_Package_Version_not_exists(package_id, version, locale_id, installer.get('Architecture', 'x64'), installer.get('InstallerType', 'msi'), p_infos.get('Scope', 'machine'))
            if version_already_exists:
                flash(f"Version {i + 1} from list already exists!", "error")
                continue

            version_uid = str(uuid4())
            filename = f"{version_uid}.{installer['InstallerUrl'].split('.')[-1]}"
            download_file(installer['InstallerUrl'], filename)

            file_path = Path(PATH_FILES) / filename
            with open(file_path, 'rb') as f:
                file_hash = sha256(f.read()).hexdigest()

            db.add_Package_Version(package_id, version, locale_id, installer.get('Architecture', 'x64'), installer.get('InstallerType', 'msi'), filename, file_hash, installer.get('Scope', 'machine'), version_uid, installer.get('NestedInstallerType', None))

            if installer.get('InstallerType', '') == "zip":
                for i_n in installer.get('NestedInstallerFiles', []):
                    for key, value in i_n.items():
                        db.add_Nested_Installer(version_uid, key, value)

            for switch_key in ["Silent", "SilentWithProgress", "Interactive", "InstallLocation", "Log", "Upgrade", "Custom", "Repair"]:
                switch_value = installer['InstallerSwitches'].get(switch_key, "")
                if switch_value:
                    db.add_Package_Version_Switch(version_uid, switch_key, switch_value)

        if len(installer_ids) > 0:
            db.db_commit(True)
            flash("Successfully added package and/or versions!", "success")
        else:
            flash("No versions found!", "error")
        del db
        return redirect(url_for(redir))

    for p in p_infos['Installers']:
        locale_id = db.get_Locale_ID_by_Value(p_infos.get('Locale', 'en-US'))
        p['EXISTS'] = not db.check_Package_Version_not_exists(package_id, version, locale_id, p.get('Architecture', 'x64'), p.get('InstallerType', 'msi'), p_infos.get('Scope', 'machine'))
    del db
    return render_template("index_add_store_package.html", package_id=package_id, p_infos=p_infos, version=request.args.get("version", ""), p_exists=package_exists, back=back, search=search, page=page)
