from flask import Blueprint, request, flash, redirect, url_for, render_template, session, current_app, send_from_directory

from Modules.Database.Database import SQLiteDatabase
from Modules.Login.Functions import check_Rights
from Modules.Login.Login import logged_in, authenticate
from Modules.Packages.Functions import add_package_service, get_package_service, edit_package_service, delete_package_service, add_package_version_service, get_all_packages_and_locales_service, delete_package_versions_service, get_package_versions_service
from Modules.Store.Functions import check_for_new_Version, update_store_db, download_file
from settings import PATH_FILES


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


@ui_bp.route('/add_package_version/<p_type>', methods=['GET', 'POST'])
@logged_in
@authenticate
def add_package_version(p_type):
    p_type = p_type.lower()
    if p_type not in ["package", "font"]:
        p_type = "package"

    if request.method == "POST":
        data = request.form.to_dict()
        file = request.files.get('file')
        installer_url = data.get("installer_url", "").strip()
        package_id = data.get("package_id", "")

        has_file = file and file.filename
        has_url = bool(installer_url)

        if not has_file and not has_url:
            flash("Please upload a file or provide a URL!", "error")
            return redirect(url_for("ui_bp.index"))

        if not has_file and has_url:
            filename = installer_url.split("/")[-1].split("?")[0]
            try:
                file = download_file(installer_url, filename, return_filestorage=True)
                if not file:
                    flash("Error downloading file from URL!", "error")
                    return redirect(url_for("ui_bp.index"))
            except Exception as e:
                flash(f"Download error: {str(e)}", "error")
                return redirect(url_for("ui_bp.index"))

        if len(data) > 0 and file:
            if p_type == "font":
                if data.get('file_type', 'ZIP') == "ZIP":
                    fnp = request.form.getlist('file_nested_path')
                    data['file_nested_path'] = fnp
                else:
                    del data['file_type_nested'], data['file_nested_path']
                data['file_architect'] = "neutral"
                data['file_scope'] = "machine"
            else:
                pkg_identifiers = request.form.getlist("dep_pkg_identifier")
                pkg_min_versions = request.form.getlist("dep_pkg_min_version")

                data["dep_windows_features"] = [v for v in request.form.getlist("dep_windows_features") if v.strip()]
                data["dep_windows_libraries"] = [v for v in request.form.getlist("dep_windows_libraries") if v.strip()]
                data["dep_external"] = [v for v in request.form.getlist("dep_external") if v.strip()]
                data["dep_package_dependencies"] = [
                    {"PackageIdentifier": ident, "MinimumVersion": ver}
                    for ident, ver in zip(pkg_identifiers, pkg_min_versions)
                    if ident.strip()
                ]

            status, message = add_package_version_service(package_id, data, file)
            if status:
                if p_type == "font":
                    flash("Font version was added successfully!", "success")
                else:
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

        if p_type == "font":
            return render_template("index_add_font_version.html", locales=locales, packages=packages, p_type=p_type)
        return render_template("index_add_package_version.html", locales=locales, packages=packages, p_type=p_type)


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


@ui_bp.route("/files/<package_name>")
@logged_in
def serve_files(package_name):
    return send_from_directory(PATH_FILES, package_name, as_attachment=True)
