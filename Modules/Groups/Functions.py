from uuid import uuid4
from flask import Blueprint, render_template, redirect, url_for, request, flash

from Modules.Database.Database import SQLiteDatabase
from Modules.Login.Login import logged_in, authenticate

groups_bp = Blueprint('groups_bp', __name__, template_folder='templates', static_folder='static')


@groups_bp.route('/', methods=['GET'])
@logged_in
@authenticate
def index():
    db = SQLiteDatabase()
    groups = db.get_All_Permission_Groups()
    del db
    return render_template("index_manage_groups.html", groups=groups)


@groups_bp.route('/add_group', methods=['POST'])
@logged_in
@authenticate
def add_group():
    group_name = request.form.get('group_name', '')

    if 15 >= len(group_name) > 0:
        db = SQLiteDatabase()
        db.add_New_Group(group_name, str(uuid4()))
        del db
        flash("Successfully added!", "success")
    else:
        flash("Error!", "error")
    return redirect(url_for("groups_bp.index"))


@groups_bp.route('/save', methods=['POST'])
@logged_in
@authenticate
def save():
    db = SQLiteDatabase()
    groups = db.get_All_Permission_Groups()

    perm_names = {}
    for group in groups:
        group_id = group["ID"]
        for perm in group:
            if perm not in ("ID", "NAME"):
                perm_names[perm] = ""
                db.update_Permission(group_id, perm, 0)

    for d in request.form:
        if d.startswith("right="):
            group, right = d.split("§")
            group = group.replace("right=", "")
            if right in perm_names.keys():
                db.update_Permission(group, right, 1)

    db.db_commit()
    del db
    flash("Saved successfully!", "success")
    return redirect(url_for("groups_bp.index"))


@groups_bp.route('/delete_group/<group_id>', methods=['POST'])
@logged_in
@authenticate
def delete_group(group_id):
    if group_id != "f4b8b5af-a414-466f-aad9-184e7e386425":
        db = SQLiteDatabase()
        db.delete_Group(group_id)
        del db
        flash("Successfully deleted!", "success")
    else:
        flash("Admin group can't be deleted!", "error")
    return redirect(url_for("groups_bp.index"))
