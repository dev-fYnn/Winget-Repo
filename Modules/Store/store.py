import io
import requests

from flask import Blueprint, render_template, request, flash, redirect, url_for
from functools import wraps
from pathlib import Path

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import parse_version, check_Internet_Connection, process_package_logo
from Modules.Login.Login import logged_in, authenticate
from Modules.Store.Functions import get_All_Packages_from_DB, download_source_msix, load_store_manifest, build_installer_overview, add_installer_version
from settings import PATH_LOGOS

store_bp = Blueprint('store_bp', __name__, template_folder='templates', static_folder='static')


def store_enabled(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        with SQLiteDatabase() as db:
            settings = db.get_winget_Settings()

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

    with SQLiteDatabase() as db:
        current_packages = [p['PACKAGE_ID'] for p in db.get_All_Packages()]

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

    p_infos, error = load_store_manifest(package_id, version)
    if error:
        flash(error, "error")
        return redirect(url_for(redir))

    with SQLiteDatabase() as db:
        package_exists = db.check_Package_exists(package_id)

        if request.method == "POST":
            data = request.form.to_dict()
            installer_ids = [int(i) for i in request.form.getlist('installer_ids')]

            if not data:
                flash("No data found!", "error")
                return redirect(url_for(redir))

            if not package_exists:
                icon_choice = data.get("icon_choice", "custom")
                logo_filename = f"{package_id}.png"

                if icon_choice and icon_choice != "custom":
                    try:
                        r = requests.get(icon_choice, timeout=10)
                        r.raise_for_status()
                        icon_bytes = io.BytesIO(r.content)
                        process_package_logo(icon_bytes, Path(PATH_LOGOS) / logo_filename)
                    except Exception as e:
                        flash("Icon from manifest could not be loaded!","error")
                        logo_filename = "dummy.png"
                else:
                    file = request.files.get('Logo')
                    if file:
                        process_package_logo(file, Path(PATH_LOGOS) / logo_filename)
                    else:
                        logo_filename = "dummy.png"

                db.add_Package(package_id, data.get("package_name", "")[:50], data.get("package_publisher", "")[:50], data.get("package_description", "")[:200], logo_filename)
                if len(installer_ids) == 0:
                    flash("Successfully added package. No versions found!", "success")
                    return redirect(url_for(redir))

            for i in installer_ids:
                if i < 0 or i > (len(p_infos['Installers']) - 1):
                    continue

                installer = p_infos['Installers'][i]
                success, message = add_installer_version(db, package_id, version, installer, p_infos)
                if not success:
                    flash(f"Installer {i + 1}: {message}", "error")
                    if message == "Error downloading installer!":
                        break

            if len(installer_ids) > 0:
                flash("Successfully added package and/or versions!", "success")
            else:
                flash("No versions found!", "error")
            return redirect(url_for(redir))

        p_infos['Installers'] = build_installer_overview(db, package_id, version, p_infos)
    return render_template("index_add_store_package.html", package_id=package_id, p_infos=p_infos, version=request.args.get("version", ""), p_exists=package_exists, back=back, search=search, page=page)
