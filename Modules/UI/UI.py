from flask import Blueprint, request, flash, redirect, url_for, render_template, session
from uuid import uuid4
from hashlib import sha256

from Modules.Database.Database import SQLiteDatabase
from Modules.Files.Functions import delete_File
from Modules.Functions import parse_version
from Modules.Login.Functions import check_Rights
from Modules.Login.Login import logged_in, authenticate
from Modules.Store.Functions import check_for_new_Version
from settings import PATH_LOGOS, PATH_FILES

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

        return render_template("index.html", packages=packages, username=session.get('logged_in_username', ''), user_mng_btn=user_mng_btn, group_mng_btn=group_mng_btn, client_mng_btn=client_mng_btn, settings_btn=settings_btn, store=settings.get('PACKAGE_STORE', "0"), update_status=update_status, version_counter=settings.get('VERSION_COUNTER', '1.0.0'))
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/add_package', methods=['GET', 'POST'])
@logged_in
@authenticate
def add_package():
    if request.method == "POST":
        data = request.form.to_dict()

        if len(data) > 0:
            package_id = data.get("package_id", str(uuid4()))
            file = request.files.get('Logo')

            if file:
                logo_path = package_id + ".png"
                file.save(fr"{PATH_LOGOS}\{logo_path}")
            else:
                logo_path = "dummy.png"

            db = SQLiteDatabase()
            status = db.add_Package(package_id, data.get("package_name", "")[:25], data.get("package_publisher", "")[:25], data.get("package_description", "")[:150], logo_path)
            db.db_commit()
            del db

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
    db = SQLiteDatabase()
    p_exists = db.check_Package_exists(package_id)

    if not p_exists:
        flash("Package not found!", "error")
    else:
        package = db.get_Package_by_ID(package_id)

        if request.method == "POST":
            data = request.form.to_dict()

            file = request.files.get('Logo')
            if file:
                logo_path = package_id + ".png"
                file.save(fr"{PATH_LOGOS}\{logo_path}")
            else:
                logo_path = package['PACKAGE_LOGO']

            if len(data) > 0:
                status = db.add_Package(package_id, data.get("package_name", "")[:25], data.get("package_publisher", "")[:25], data.get("package_description", "")[:150], logo_path, int(data.get("package_active", 1)))
                db.db_commit()

                if status:
                    flash("Package was updated successfully!", "success")
                else:
                    flash("Changes couldn't be saved. Try again!", "error")
            else:
                flash("Error. No Data found!", "error")
            del db
            return redirect(url_for("ui_bp.index"))
        else:
            del db
            return render_template("index_edit_package.html", package_id=package_id,  name=package['PACKAGE_NAME'], publisher=package['PACKAGE_PUBLISHER'], description=package['PACKAGE_DESCRIPTION'], logo=package['PACKAGE_LOGO'], active=package['PACKAGE_ACTIVE'])
    del db
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/delete_package/<package_id>', methods=['POST'])
@logged_in
@authenticate
def delete_package(package_id):
    db = SQLiteDatabase()

    if db.check_Package_exists(package_id):
        for f in db.get_All_Versions_from_Package(package_id):
            delete_File(f['INSTALLER_URL'])
            db.delete_Package_Version(f['UID'])

        delete_File(f"{package_id}.png", PATH_LOGOS)
        db.delete_Package(package_id)
        db.db_commit()
        flash("Package was deleted successfully!", "success")
    else:
        flash("Package not found!", "error")
    del db
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/add_package_version', methods=['GET', 'POST'])
@logged_in
@authenticate
def add_package_version():
    if request.method == "POST":
        data = request.form.to_dict()
        package_id = data.get("package_id", "")

        if len(data) > 0 and 'file' in request.files:
            db = SQLiteDatabase()

            if db.check_Package_exists(package_id):
                version_uid = str(uuid4())

                file = request.files['file']
                filename = f"{version_uid}.{file.filename.split('.')[-1]}"
                file_type = data.get('file_type', 'msi').lower()
                if file and db.check_Package_Version_not_exists(package_id, data.get("package_version", "")[:25], data.get("package_local", 1), data.get("file_architect", ""), file_type, data.get("file_scope", "")):
                    file.save(fr"{PATH_FILES}\{filename}")

                    with open(fr"{PATH_FILES}\{filename}", 'rb') as f:
                        readable_hash = sha256(f.read()).hexdigest()

                    status = db.add_Package_Version(package_id, data.get("package_version", "")[:25], data.get("package_local", 1), data.get("file_architect", ""), file_type, filename, readable_hash, data.get("file_scope", ""), version_uid, data.get('file_type_nested', None).lower())

                    if status:
                        if file_type == "zip" and len(data.get('file_nested_path', '')) > 0:
                            db.add_Nested_Installer(version_uid, 'RelativeFilePath', data.get('file_nested_path', ''))

                        switches = {key.replace("switch_", ""): value for key, value in data.items() if key.startswith('switch_')}
                        for s in ["Silent", "SilentWithProgress", "Interactive", "InstallLocation", "Log", "Upgrade", "Custom", "Repair"]:
                            if s in switches.keys() and switches[s] != "":
                                db.add_Package_Version_Switch(version_uid, s, switches[s])
                        flash("Package version was added successfully!", "success")
                    else:
                        flash("Error adding the package version. Try again!", "error")
                    db.db_commit()
                else:
                    flash("Package version already exists!", "error")
            else:
                flash("Package doesnt exist!", "error")

            del db
        else:
            flash("Error. No Data found!", "error")
        return redirect(url_for("ui_bp.index"))
    else:
        db = SQLiteDatabase()
        packages = db.get_All_Packages()
        locales = db.get_All_Locales()
        del db

        if len(packages) > 0:
            return render_template("index_add_package_version.html", locales=locales, packages=packages)
        else:
            flash("No packages found!", "error")
            return redirect(url_for("ui_bp.index"))


@ui_bp.route('/delete_package_version/<package_id>', methods=['GET', 'POST'])
@logged_in
@authenticate
def delete_package_version(package_id):
    db = SQLiteDatabase()

    if request.method == "POST":
        if db.check_Package_exists(package_id):
            ids = request.form.getlist("version_select")
            if len(ids) > 0:
                for i in ids:
                    url = db.get_specfic_Versions_from_Package(i)
                    delete_File(url['INSTALLER_URL'])
                    db.delete_Package_Version(i)
                db.db_commit(True)
                flash("Packages deleted successfully!", "success")
            else:
                flash("No versions selected!", "error")
        else:
            flash("No package found!", "error")
    else:
        if db.check_Package_exists(package_id):
            versions = db.get_All_Versions_from_Package(package_id)
            versions = sorted(versions, key=lambda x: parse_version(x["VERSION"]), reverse=True)
            for v in versions:
                v['SWITCHES'] = db.get_Package_Switche(v['UID'])
            package = db.get_Package_by_ID(package_id)
            del db
            return render_template("index_delete_package_version.html", package_id=package_id, versions=versions, Package_Name=package['PACKAGE_NAME'])
        else:
            flash("No package found!", "error")
    del db
    return redirect(url_for("ui_bp.index"))
