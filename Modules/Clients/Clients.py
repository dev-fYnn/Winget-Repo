from uuid import uuid4
from flask import Blueprint, render_template, redirect, url_for, request, flash

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import get_ip_from_hostname
from Modules.Login.Login import logged_in, authenticate
from Modules.Winget.Functions import get_winget_Settings

client_bp = Blueprint('client_bp', __name__, template_folder='templates', static_folder='static')


@client_bp.route('/', methods=['GET'])
@logged_in
@authenticate
def index():
    db = SQLiteDatabase()
    clients = db.get_All_Clients()
    del db
    return render_template("index_clients.html", clients=clients)


@client_bp.route('/add', methods=['POST'])
@logged_in
@authenticate
def add_client():
    name = request.form.get('client_name', "")

    if len(name) > 0:
        settings = get_winget_Settings()
        ip = get_ip_from_hostname(name, settings.get('DNS_SUFFIX', ''), settings.get('DNS_SERVER', '192.168.1.1'))

        if len(ip) > 0:
            db = SQLiteDatabase()
            db.add_New_Client(str(uuid4()), name.upper()[:25], ip, str(uuid4()))
            db.db_commit()
            del db
            flash("Client was added successfully!", "success")
        else:
            flash("Can't get ip from entered hostname! Check the input or dns config!", "error")
    else:
        flash("Error. No Data found!", "error")
    return redirect(url_for('client_bp.index'))


@client_bp.route('/delete/<client_id>', methods=['POST'])
@logged_in
@authenticate
def delete_client(client_id):
    if len(client_id) > 0:
        db = SQLiteDatabase()
        db.delete_Client(client_id)
        db.db_commit()
        del db
        flash("Client was removed successfully!", "success")
    else:
        flash("Error. No Data found!", "error")
    return redirect(url_for('client_bp.index'))


@client_bp.route('/logs/<client_id>', methods=['GET'])
@logged_in
@authenticate
def view_logs(client_id):
    db = SQLiteDatabase()
    logs = db.get_Logs_for_Client(client_id)
    client = db.get_Client_by_ID(client_id)
    del db

    if len(client) == 1:
        client = client[0]
    elif client_id == "EXTERN":
        client = client_id
    else:
        flash("Client not found!", "error")
        return redirect(url_for("client_bp.index"))


    return render_template("index_clients_logs.html", logs=logs, client=client)
