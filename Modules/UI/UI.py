from flask import Blueprint, request, flash, redirect, url_for, render_template, session, current_app

from Modules.Database.Database import SQLiteDatabase
from Modules.Login.Functions import check_Rights
from Modules.Login.Login import logged_in, authenticate
from Modules.Packages.Functions import add_package_service, get_package_service, edit_package_service, delete_package_service, add_package_version_service, get_all_packages_and_locales_service, delete_package_versions_service, get_package_versions_service
from Modules.Store.Functions import check_for_new_Version, update_store_db


ui_bp = Blueprint('ui_bp', __name__, template_folder='templates', static_folder='static')


@ui_bp.route('/', methods=['GET', 'POST'])
@logged_in
def index():
    if request.method == "POST":
        package_id = request.form.get("selected_package", "")

        if len(package_id) > 0:
            match request.form.get('action', ''):
                case "edit":
                    return redirect(url_for('ui_bp.edit_package', package_id=package_id))
                case "open_versions":
                    return redirect(url_for('ui_bp.delete_package_version', package_id=package_id))
                case _:
                    flash("Action not found!", "error")
        flash("Package not found!", "error")
    else:
        db = SQLiteDatabase()
        packages = db.get_All_Packages()
        settings = db.get_winget_Settings()
        del db

        update_status=False
        if settings['PACKAGE_STORE'] == "1":
            update_store_db()
            packages, update_status = check_for_new_Version(packages)

        user_mng_btn = False
        group_mng_btn = False
        client_mng_btn = False
        settings_btn = False

        if check_Rights(session['logged_in'], "USER_BP.INDEX"):
            user_mng_btn = True
        if check_Rights(session['logged_in'], "GROUPS_BP.INDEX"):
            group_mng_btn = True
        if check_Rights(session['logged_in'], "CLIENT_BP.INDEX"):
            client_mng_btn = True
        if check_Rights(session['logged_in'], "SETTINGS_BP.INDEX"):
            settings_btn = True

        return render_template("index.html", packages=packages, username=session.get('logged_in_username', ''), user_mng_btn=user_mng_btn, group_mng_btn=group_mng_btn, client_mng_btn=client_mng_btn, settings_btn=settings_btn, store=settings.get('PACKAGE_STORE', "0"), update_status=update_status, version_counter=settings.get('VERSION_COUNTER', '1.0.0'), dev_mode=current_app.config.get('dev_mode', False))
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/add_package', methods=['GET', 'POST'])
@logged_in
@authenticate
def add_package():
    if request.method == "POST":
        data = request.form.to_dict()
        file = request.files.get('Logo')

        package = get_package_service(data.get("package_id", ''))
        if package:
            flash("Package ID already exists!", "error")
            return redirect(url_for("ui_bp.index"))

        if len(data) > 0:
            status, package_id = add_package_service(data, file)
            if status:
                flash("Package was added successfully!", "success")
            else:
                flash("Package can't be created. Try again!", "error")
        else:
            flash("Error. No Data found!", "error")
        return redirect(url_for("ui_bp.index"))
    else:
        return render_template("index_add_package.html")


@ui_bp.route('/edit_package/<package_id>', methods=['GET', 'POST'])
@logged_in
@authenticate
def edit_package(package_id):
    package = get_package_service(package_id)
    if not package:
        flash("Package not found!", "error")
        return redirect(url_for("ui_bp.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        file = request.files.get('Logo')

        status, _ = edit_package_service(package_id, data, file)
        if status:
            flash("Package was updated successfully!", "success")
        else:
            flash("Changes couldn't be saved. Try again!", "error")
        return redirect(url_for("ui_bp.index"))
    return render_template("index_edit_package.html", package_id=package_id, name=package['PACKAGE_NAME'], publisher=package['PACKAGE_PUBLISHER'], description=package['PACKAGE_DESCRIPTION'], logo=package['PACKAGE_LOGO'], active=package['PACKAGE_ACTIVE'])


@ui_bp.route('/delete_package/<package_id>', methods=['POST'])
@logged_in
@authenticate
def delete_package(package_id):
    status = delete_package_service(package_id)
    if status:
        flash("Package was deleted successfully!", "success")
    else:
        flash("Package not found!", "error")
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/add_package_version', methods=['GET', 'POST'])
@logged_in
@authenticate
def add_package_version():
    if request.method == "POST":
        data = request.form.to_dict()
        file = request.files.get('file')
        package_id = data.get("package_id", "")

        if len(data) > 0 and file:
            status, message = add_package_version_service(package_id, data, file)
            if status:
                flash("Package version was added successfully!", "success")
            else:
                flash(message, "error")
        else:
            flash("Error. No Data found!", "error")
        return redirect(url_for("ui_bp.index"))
    else:
        packages, locales = get_all_packages_and_locales_service()
        if len(packages) == 0:
            flash("No packages found!", "error")
            return redirect(url_for("ui_bp.index"))
        return render_template("index_add_package_version.html", locales=locales, packages=packages)


@ui_bp.route('/delete_package_version/<package_id>', methods=['GET', 'POST'])
@logged_in
@authenticate
def delete_package_version(package_id):
    package = get_package_service(package_id)
    if not package:
        flash("No package found!", "error")
        return redirect(url_for("ui_bp.index"))

    if request.method == "POST":
        ids = request.form.getlist("version_select")
        if len(ids) > 0:
            delete_package_versions_service(ids)
            flash("Packages deleted successfully!", "success")
        else:
            flash("No versions selected!", "error")
        return redirect(url_for("ui_bp.index"))
    versions = get_package_versions_service(package_id)
    return render_template("index_delete_package_version.html", package_id=package_id, versions=versions, Package_Name=package['PACKAGE_NAME'])
