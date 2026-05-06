import io
import os

from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session, send_file

from Modules.Database.Database import SQLiteDatabase
from Modules.Encryption import encrypt_text
from Modules.Functions import is_ip_address, check_Internet_Connection
from Modules.Login.Login import logged_in, authenticate
from Modules.PreIndexed.Certificate import generate_pfx_certificate
from settings import PATH_CERTIFICATES

settings_bp = Blueprint('settings_bp', __name__, template_folder='templates', static_folder='static')


@settings_bp.route('/', methods=['GET', 'POST'])
@logged_in
@authenticate
def index():
    with SQLiteDatabase() as db:
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
            flash("Saved settings!", "success")
            return redirect(url_for("settings_bp.index"))

        text = db.get_Fields_by_Section("SETTINGS", "EN")

    certificate_exists = os.path.exists(os.path.join(PATH_CERTIFICATES, "preindexed.pfx"))
    return render_template("index_settings.html", settings=settings, texts=text, certificate_exists=certificate_exists)


@settings_bp.route('/terms', methods=['GET'])
def terms():
    loggedin = False
    if 'logged_in' in session:
        loggedin = True

    with SQLiteDatabase() as db:
        text = db.get_Text_by_Typ("TOS")
    return render_template('index_terms_of_service.html', terms_text=text, loggedin=loggedin)


@settings_bp.route('/edit_terms', methods=['POST'])
@logged_in
@authenticate
def edit_terms():
    with SQLiteDatabase() as db:
        db.update_Text_by_Typ("TOS", request.form.get('terms_text', ''))
    flash("Successfully saved the Terms of Service!", "success")
    return redirect(url_for("settings_bp.terms"))


@settings_bp.route('/generate_certificate', methods=['POST'])
@logged_in
@authenticate
def generate_certificate():
    if current_app.config['INDEXED_DB_ACTIV'] == "1":
        data = request.get_json()
        download_only = data.get('download_only', False)
        cert_file_path = os.path.join(PATH_CERTIFICATES, "preindexed.pfx")
        cer_file_path = os.path.join(PATH_CERTIFICATES, "public_preindexed.cer")

        if download_only:
            if os.path.exists(cer_file_path):
                return send_file(cer_file_path, mimetype='application/x-x509-ca-cert', as_attachment=True, download_name='winget-repo.cer')
            else:
                return "Certificate not found", 404

        password = data.get('password') or None
        valid_days = data.get('valid_days', 365)

        pfx, cer = generate_pfx_certificate(password=password, valid_days=valid_days)

        with SQLiteDatabase() as db:
            db_pw = "0" if password is None else encrypt_text(current_app.config['ENCRYPTION_KEY'], password)
            db.update_wingetrepo_Setting("INDEXED_DB_PW", db_pw)

        with open(cert_file_path, "wb") as f:
            f.write(pfx)
        with open(cer_file_path, "wb") as f:
            f.write(cer)

        return send_file(io.BytesIO(cer), mimetype='application/x-x509-ca-cert', as_attachment=True, download_name='winget-repo.cer')
    return ""
