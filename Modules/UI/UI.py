import sys
import os

from flask import Blueprint, request, flash, redirect, url_for, render_template, session
from uuid import uuid4
from hashlib import sha256

from Modules.Database.Database import SQLiteDatabase
from Modules.Files.Functions import delete_File
from Modules.Login.Login import logged_in

ui_bp = Blueprint('ui_bp', __name__, template_folder='templates', static_folder='static')


@ui_bp.route('/', methods=['GET', 'POST'])
@logged_in
def index():
    if request.method == "POST":
        if "selected_package_edit" in request.form:
            return redirect(url_for('ui_bp.edit_package', package_id=request.form.get("selected_package_edit", "")))
        else:
            return redirect(url_for('ui_bp.delete_package_version', package_id=request.form.get("selected_package", "")))
    else:
        db = SQLiteDatabase()
        packages = db.get_All_Packages()
        del db
        return render_template("index.html", packages=packages, username=session.get('logged_in_username', ''))


@ui_bp.route('/add_package', methods=['GET', 'POST'])
@logged_in
def add_package():
    if request.method == "POST":
        data = request.form.to_dict()

        if len(data) > 0:
            db = SQLiteDatabase()
            status = db.add_Package(str(uuid4()), data.get("package_name", "")[:25], data.get("package_publisher", "")[:25], data.get("package_description", "")[:40])
            db.db_commit()
            del db

            if status:
                flash("Package was added successfully!", "success")
            else:
                flash("Package cannot be created. Try again!", "error")
        else:
            flash("Error. No Data found!", "error")
        return redirect(url_for("ui_bp.index"))
    else:
        return render_template("index_add_package.html")


@ui_bp.route('/edit_package/<package_id>', methods=['GET', 'POST'])
@logged_in
def edit_package(package_id):
    db = SQLiteDatabase()
    p_exists = db.check_Package_exists(package_id)

    if not p_exists:
        flash("Package not found!", "error")
    else:
        if request.method == "POST":
            data = request.form.to_dict()

            if len(data) > 0:
                status = db.add_Package(package_id, data.get("package_name", "")[:25], data.get("package_publisher", "")[:25], data.get("package_description", "")[:40])
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
            package = db.get_Package_by_ID(package_id)
            del db
            return render_template("index_edit_package.html", package_id=package_id,  name=package[1], publisher=package[2], description=package[3])
    del db
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/delete_package/<package_id>', methods=['POST'])
@logged_in
def delete_package(package_id):
    db = SQLiteDatabase()

    if db.check_Package_exists(package_id):
        for f in db.get_All_Verions_from_Package(package_id):
            delete_File(f['URL'])
            db.delete_Package_Version(f['UID'])

        db.delete_Package(package_id)
        db.db_commit()
        flash("Package was deleted successfully!", "success")
    else:
        flash("Package not found!", "error")
    del db
    return redirect(url_for("ui_bp.index"))


@ui_bp.route('/add_package_version', methods=['GET', 'POST'])
@logged_in
def add_package_version():
    if request.method == "POST":
        data = request.form.to_dict()
        package_id = data.get("package_id", "")

        if len(data) > 0 and 'file' in request.files:
            db = SQLiteDatabase()

            if db.check_Package_exists(package_id):
                version_uid = str(uuid4())
                path = fr"{sys.path[0]}\Files"

                if not os.path.exists(path):
                    os.makedirs(path)

                file = request.files['file']
                filename = f"{version_uid}.{file.filename.split('.')[-1]}"
                file.save(fr"{path}\{filename}")

                with open(fr"{path}\{filename}", 'rb') as f:
                    readable_hash = sha256(f.read()).hexdigest()

                status = db.add_Package_Version(package_id, data.get("package_version", "")[:25], data.get("package_local", ""), data.get("file_architect", ""), file.filename.split('.')[-1].lower(), filename, readable_hash, data.get("file_scope", ""), version_uid)

                if status:
                    switches = {key.replace("switch_", ""): value for key, value in data.items() if key.startswith('switch_')}
                    for s in ["Silent", "SilentWithProgress", "Interactive", "InstallLocation", "Log", "Upgrade", "Custom", "Repair"]:
                        if s in switches.keys() and switches[s] != "":
                            db.add_Package_Version_Switch(version_uid, s, switches[s])
                    flash("Package version was added successfully!", "success")
                else:
                    flash("Package version couldn't be added. Try again!", "error")
                db.db_commit()
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
def delete_package_version(package_id):
    db = SQLiteDatabase()

    if request.method == "POST":
        if db.check_Package_exists(package_id):
            ids = request.form.getlist("version_select")
            if len(ids) > 0:
                for i in ids:
                    url = db.get_specfic_Verions_from_Package(i)
                    delete_File(url['URL'])
                    db.delete_Package_Version(i)
                db.db_commit()
                flash("Packages deleted successfully!", "success")
            else:
                flash("No versions selected!", "error")
        else:
            flash("No package found!", "error")
    else:
        if db.check_Package_exists(package_id):
            versions = db.get_All_Verions_from_Package(package_id)
            package = db.get_Package_by_ID(package_id)
            del db
            return render_template("index_delete_package_version.html", package_id=package_id, versions=versions, Package_Name=package[1])
        else:
            flash("No package found!", "error")
    del db
    return redirect(url_for("ui_bp.index"))
