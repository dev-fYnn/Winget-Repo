from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import is_ip_address, check_Internet_Connection
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

            if settings[key]['INTERNET'] == 1 and not check_Internet_Connection():
                flash(f"Setting: {key} requires an internet connection!", "error")
                continue

            if len(value) > 0:
                if settings[key]['MAX_LENGTH'] is None or len(value.strip()) <= settings[key]['MAX_LENGTH']:
                    if key in current_app.config:
                        current_app.config[key] = value
                    db.update_wingetrepo_Setting(key, value)
                else:
                    flash(f"Setting: {key} is too long!", "error")
        db.db_commit()
        del db

        flash("Saved settings!", "success")
        return redirect(url_for("settings_bp.index"))

    text = db.get_Fields_by_Section("SETTINGS", "EN")
    del db
    return render_template("index_settings.html", settings=settings, texts=text)


@settings_bp.route('/terms', methods=['GET'])
def terms():
    loggedin = False
    if 'logged_in' in session:
        loggedin = True

    db = SQLiteDatabase()
    text = db.get_Text_by_Typ("TOS")
    del db
    return render_template('index_terms_of_service.html', terms_text=text, loggedin=loggedin)


@settings_bp.route('/edit_terms', methods=['POST'])
@logged_in
@authenticate
def edit_terms():
    db = SQLiteDatabase()
    db.update_Text_by_Typ("TOS", request.form.get('terms_text', ''))
    del db
    flash("Successfully saved the Terms of Service!", "success")
    return redirect(url_for("settings_bp.terms"))
