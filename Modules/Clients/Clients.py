from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, current_app
from uuid import uuid4

from Modules.Database.Database import SQLiteDatabase
from Modules.Functions import get_ip_from_hostname, generate_Client_INI
from Modules.Login.Login import logged_in, authenticate
from Modules.Winget.Functions import get_winget_Settings

client_bp = Blueprint('client_bp', __name__, template_folder='templates', static_folder='static')


@client_bp.route('/', methods=['GET'])
@logged_in
@authenticate
def index():
    db = SQLiteDatabase()
    clients = db.get_All_Clients()
    groups = db.get_All_Blacklist_Groups()
    del db
    return render_template("index_clients.html", clients=clients, groups=groups)


@client_bp.route('/add', methods=['POST'])
@logged_in
@authenticate
def add_client():
    name = request.form.get('client_name', "")

    if len(name) > 0:
        dev_mode = current_app.config.get('dev_mode', False)

        if dev_mode:
            ip = "127.0.0.1"
            name = "LOCALHOST"
        else:
            settings = get_winget_Settings()
            ip = get_ip_from_hostname(name, settings.get('DNS_SUFFIX', ''), settings.get('DNS_SERVER', '192.168.1.1'))

        if len(ip) > 0:
            c_id = str(uuid4())

            db = SQLiteDatabase()
            status = db.add_New_Client(c_id, name.upper()[:25], ip, str(uuid4()))
            del db

            if status:
                flash("Client was added successfully!", "success")
                return redirect(url_for("client_bp.setup_client", client_id=c_id))
            else:
                flash("Hostname alreay exists!", "error")
        else:
            flash("Can't get ip from entered hostname! Check the input or dns config!", "error")
    else:
        flash("Error. No Data found!", "error")
    return redirect(url_for('client_bp.index'))


@client_bp.route('/block/<client_id>', methods=['POST'])
@logged_in
@authenticate
def block_client(client_id):
    db = SQLiteDatabase()
    client = db.get_Client_by_ID(client_id)

    if client:
        if client['ENABLED'] == 1:
            status = 0
            flash("Client successfully disabled!", "success")
        else:
            status = 1
            flash("Client successfully enabled!", "success")

        db.update_Client_Enable_Status(client_id, status)
    else:
        flash("Client not found!", "error")
    del db
    return redirect(url_for("client_bp.index"))


@client_bp.route('/delete/<client_id>/<auth_token>', methods=['POST'])
@logged_in
@authenticate
def delete_client(client_id, auth_token):
    if len(client_id) > 0 and len(auth_token) > 0:
        db = SQLiteDatabase()
        db.delete_Client(client_id, auth_token)
        del db
        flash("Client was removed successfully!", "success")
    else:
        flash("Error. No Data found!", "error")
    return redirect(url_for('client_bp.index'))


@client_bp.route('/setup/<client_id>', methods=['GET', 'POST'])
@logged_in
@authenticate
def setup_client(client_id):
    db = SQLiteDatabase()
    data = db.get_Client_by_ID(client_id)
    settings = db.get_winget_Settings()
    del db

    if data:
        if request.method == "POST":
            ini = generate_Client_INI(data.get('TOKEN', ''), request.host)
            return send_file(ini, as_attachment=True, download_name='config.ini', mimetype='text/plain')

        return render_template("index_clients_setup.html", client=data, authentication=settings.get('CLIENT_AUTHENTICATION', '0'), host_url=request.host)
    flash("No client found!", "error")
    return redirect(url_for("client_bp.index"))


@client_bp.route('/logs/<client_id>', methods=['GET'])
@logged_in
@authenticate
def view_logs(client_id):
    db = SQLiteDatabase()
    logs = db.get_Logs_for_Client(client_id)
    client = db.get_Client_by_ID(client_id)
    del db

    if client_id == "EXTERN":
        client = client_id

    if not client:
        flash("Client not found!", "error")
        return redirect(url_for("client_bp.index"))
    return render_template("index_clients_logs.html", logs=logs, client=client, client_id=client_id)


@client_bp.route('/logs/<client_id>/clear', methods=['GET'])
@logged_in
@authenticate
def clear_logs(client_id):
    db = SQLiteDatabase()
    db.remove_logs(client_id)
    del db

    flash("Successfully cleared logs!", "success")
    return redirect(url_for("client_bp.view_logs", client_id=client_id))


@client_bp.route('/blacklist/<client_id>/<auth_token>', methods=['GET', 'POST'])
@logged_in
@authenticate
def blacklist(client_id, auth_token):
    db = SQLiteDatabase()

    if request.method == 'POST':
        selected_packages = request.form.getlist('blacklist')
        selected_groups = request.form.getlist('group_blacklist')

        db.update_Blacklist_Package(auth_token, selected_packages)
        db.update_Blacklist_Groups_Clients(auth_token, selected_groups)

        flash("Blacklist successfully updated!", "success")
        return redirect(url_for('client_bp.index'))

    client = db.get_Client_by_ID(client_id)

    if not client:
        flash("Client not found!", "error")
        return redirect(url_for('client_bp.index'))

    packages = db.get_All_Packages()
    blacklisted_packages = db.get_Blacklist_for_client(auth_token, False)
    blacklist_groups = db.get_All_Blacklist_Groups()
    blacklisted_groups = db.get_Blacklist_Groups_for_Client(auth_token)
    del db

    if len(packages) == 0:
        flash("No packages found!", "error")
        return redirect(url_for('client_bp.index'))

    return render_template('index_clients_blacklist.html', client=client, packages=packages, blacklisted_packages=blacklisted_packages, blacklist_groups=blacklist_groups, blacklisted_groups=blacklisted_groups)


@client_bp.route('/blacklist/groups/<action>', methods=['GET', 'POST'])
@logged_in
@authenticate
def blacklist_groups(action):
    action = action.upper()
    if action not in ("CREATE", "EDIT"):
        flash("Action is not available!", "error")
        return redirect(url_for('client_bp.index'))

    db = SQLiteDatabase()

    if request.method == 'POST':
        g_id = request.form.get('group_id', str(uuid4()))
        group_name = request.form.get('group_name', 'Dummy')
        selected_packages = request.form.getlist('blacklist')
        db.insert_update_Blacklist_Group(g_id, group_name[:30], selected_packages)

        if action == "CREATE":
            flash("Blacklist group successfully created!", "success")
        else:
            flash("Blacklist group successfully updated!", "success")

        del db
        return redirect(url_for('client_bp.index'))

    packages = db.get_All_Packages()

    if action == "EDIT":
        g_id = request.args.get('group_id', '')

        if "remove" in request.args:
            db.remove_Blacklist_Group(g_id)
            flash("Blacklist group successfully removed!", "success")
            return redirect(url_for('client_bp.index'))

        group = db.get_Blacklist_Group(g_id)
        blacklisted_packages = db.get_Packages_from_Blacklist_Group(g_id)

        if len(group) == 0:
            flash("Group not found!", "error")
            return redirect(url_for('client_bp.index'))

        del db
        return render_template('index_clients_blacklist_groups.html', packages=packages, action=action, group=group, blacklisted_packages=blacklisted_packages)
    else:
        del db
        return render_template('index_clients_blacklist_groups.html', packages=packages, action=action)
