import json
import os
from uuid import uuid4
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app

from Modules.Database.Database import SQLiteDatabase
from Modules.Login.Login import logged_in, authenticate
from settings import PATH_PLUGINS

groups_bp = Blueprint('groups_bp', __name__, template_folder='templates', static_folder='static')


@groups_bp.route('/', methods=['GET'])
@logged_in
@authenticate
def index():
    current_section = "PERMISSIONS"
    current_lang = "EN"

    with SQLiteDatabase() as db:
        groups = db.get_All_Permission_Groups()
        text = db.get_Fields_by_Section(current_section, current_lang)

    if os.path.exists(PATH_PLUGINS):
        for folder in os.listdir(PATH_PLUGINS):
            translation_path = os.path.join(PATH_PLUGINS, folder, "translation.json")
            if os.path.isdir(os.path.join(PATH_PLUGINS, folder)) and os.path.exists(translation_path):
                try:
                    with open(translation_path, "r", encoding="utf-8") as f:
                        plugin_translations = json.load(f)
                        for field_id, info in plugin_translations.items():
                            if info.get("SECTION") == current_section and info.get("LANGUAGE") == current_lang:
                                text[field_id.upper()] = info.get("TEXT")
                                text[field_id.lower()] = info.get("TEXT")
                except Exception as e:
                    pass

    all_plugin_perms = current_app.config.get('ALL_PLUGIN_PERMISSIONS', [])
    cached_plugin_assignments = current_app.config.get('PLUGIN_PERMISSIONS', {})
    combined_groups = []

    for group in groups:
        group_dict = dict(group)
        group_id = group_dict["ID"]

        for plugin_perm in all_plugin_perms:
            group_dict[plugin_perm] = 0

        allowed_for_this_group = cached_plugin_assignments.get(group_id, [])
        for perm in allowed_for_this_group:
            if perm in group_dict:
                group_dict[perm] = 1
        combined_groups.append(group_dict)
    return render_template("index_manage_groups.html", groups=combined_groups, texts=text)


@groups_bp.route('/add_group', methods=['POST'])
@logged_in
@authenticate
def add_group():
    group_name = request.form.get('group_name', '')

    if 15 >= len(group_name) > 0:
        with SQLiteDatabase() as db:
            status = db.add_New_Group(group_name, str(uuid4()))

        if status:
            flash("Successfully added!", "success")
        else:
            flash("Failed!", "error")
    else:
        flash("Error!", "error")
    return redirect(url_for("groups_bp.index"))


@groups_bp.route('/save', methods=['POST'])
@logged_in
@authenticate
def save():
    with SQLiteDatabase() as db:
        groups = db.get_All_Permission_Groups()
        perm_groups = [g['ID'] for g in groups]
        perm_names = {p: "" for g in groups for p in g if p not in ("ID", "NAME")}
        for g in groups:
            for p in perm_names:
                db.update_Permission(g["ID"], p, 0)

    all_plugin_perms = current_app.config.get('ALL_PLUGIN_PERMISSIONS', [])
    plugin_write_data = {}
    if os.path.exists(PATH_PLUGINS):
        for folder in os.listdir(PATH_PLUGINS):
            if os.path.isdir(os.path.join(PATH_PLUGINS, folder)) and not folder.startswith('__'):
                plugin_write_data[folder] = {g["ID"]: [] for g in groups}

    current_app.config['PLUGIN_PERMISSIONS'] = {g["ID"]: [] for g in groups}
    for d in request.form:
        if d.startswith("right="):
            group_id, right = d.split("§")
            group_id = group_id.replace("right=", "")
            if group_id in perm_groups:
                if right in all_plugin_perms:
                    folder_target = right.split('.')[0].replace('_bp', '').upper()
                    actual_folder = None
                    for folder in plugin_write_data.keys():
                        if folder.upper() == folder_target:
                            actual_folder = folder
                            break

                    if actual_folder:
                        plugin_write_data[actual_folder][group_id].append(right)
                        current_app.config['PLUGIN_PERMISSIONS'][group_id].append(right)

                elif right in perm_names:
                    with SQLiteDatabase() as db:
                        db.update_Permission(group_id, right, 1)

    for folder, mapping in plugin_write_data.items():
        with open(os.path.join(PATH_PLUGINS, folder, "permissions.json"), "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
    flash("Saved successfully!", "success")
    return redirect(url_for("groups_bp.index"))


@groups_bp.route('/delete_group/<group_id>', methods=['POST'])
@logged_in
@authenticate
def delete_group(group_id):
    if group_id == "f4b8b5af-a414-466f-aad9-184e7e386425":
        flash("Admin group can't be deleted!", "error")
        return redirect(url_for("groups_bp.index"))

    with SQLiteDatabase() as db:
        db.delete_Group(group_id)

    if group_id in current_app.config.get('PLUGIN_PERMISSIONS', {}):
        del current_app.config['PLUGIN_PERMISSIONS'][group_id]

    if os.path.exists(PATH_PLUGINS):
        for folder in os.listdir(PATH_PLUGINS):
            perm_path = os.path.join(PATH_PLUGINS, folder, "permissions.json")
            if os.path.isdir(os.path.join(PATH_PLUGINS, folder)) and os.path.exists(perm_path):
                try:
                    with open(perm_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if group_id in data:
                        del data[group_id]
                        with open(perm_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    pass

    flash("Successfully deleted!", "success")
    return redirect(url_for("groups_bp.index"))
