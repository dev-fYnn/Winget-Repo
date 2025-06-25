from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import is_ip_address
from Modules.Login.Login import logged_in, authenticate

settings_bp = Blueprint('settings_bp', __name__, template_folder='templates', static_folder='static')


@settings_bp.route('/', methods=['GET', 'POST'])
@logged_in
@authenticate
def index():
    db = SQLiteDatabase()
    settings = db.get_Settings_for_View()

    if request.method == "POST":
        for key in settings.keys():
            form_key = f"setting_{key}"
            if settings[key]['TYPE'] == "CHECKBOX":
                value = "1" if form_key in request.form else "0"
            elif settings[key]['TYPE'] == "IP":
                value = request.form.get(form_key, "")
                if not is_ip_address(value):
                    flash("IP couldn't be saved!", "error")
                    continue
            else:
                value = request.form.get(form_key, "")

            if len(value) > 0:
                if key in current_app.config:
                    current_app.config[key] = value
                db.update_wingetrepo_Setting(key, value)
        db.db_commit()
        del db

        flash("Saved settings!", "success")
        return redirect(url_for("settings_bp.index"))

    text = db.get_Fields_by_Section("SETTINGS", "EN")
    del db
    return render_template("index_settings.html", settings=settings, texts=text)
