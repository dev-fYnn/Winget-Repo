from flask import Blueprint, render_template, redirect, url_for, request, flash, session

from Modules.Database.Database import SQLiteDatabase
from Modules.Login.Functions import check_Rights
from Modules.User.Functions import user_setup_finished, add_User, check_User_Exists, delete_User, check_Group_Exists, change_User_Password, edit_User
from Modules.Login.Login import logged_in, authenticate

user_bp = Blueprint('user_bp', __name__, template_folder='templates', static_folder='static')


@user_bp.route('/', methods=['GET'])
@logged_in
@authenticate
def index():
    db = SQLiteDatabase()
    user = db.get_All_User()
    del db
    return render_template("index_manage_user.html", user=user)


@user_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'logged_in' not in session and user_setup_finished() is False:
        flag = 0
    elif 'logged_in' in session and check_Rights(session['logged_in'], request.endpoint):
        flag = 1
    else:
        return redirect(url_for("ui_bp.index"))

    if request.method == "POST":
        data = request.form

        if "username" in data and "password" in data:
            if flag == 0:
                group = ["f4b8b5af-a414-466f-aad9-184e7e386425"]
            else:
                group = data.getlist('group')

            if len(group) == 1 and check_Group_Exists(group[0]):
                if check_User_Exists(data['username']) is False:
                    if len(data['password']) >= 10 and len(data['username']) > 0:
                        status = add_User(data['username'], data['password'], group[0], flag)
                        if status:
                            flash("User has been created. Please login!", "success")
                        else:
                            flash("Error creating the user! Try again!", "error")
                    else:
                        flash("Invalid submissions!", "error")
                else:
                    flash("Username already exists!", "error")
            else:
                flash("Select only one group at a time!", "error")
        if flag == 0:
            return redirect(url_for("login_bp.logout"))
        else:
            return redirect(url_for("user_bp.index"))

    db = SQLiteDatabase()
    groups = db.get_All_Permission_Groups()
    del db
    return render_template("index_add_user.html", back=request.args.get("back", ""), groups=groups)


@user_bp.route('/edit_user/<user_id>', methods=['GET', 'POST'])
@logged_in
@authenticate
def edit_user(user_id):
    u_status, c_username, deletable, p_group = check_User_Exists("", user_id, False)

    if u_status is True and deletable == 1:
        if request.method == 'POST':
            data = request.form
            group = data.getlist('group')
            username = data.get("username", '')

            if len(username) == 0 or c_username == username:
                username = None

            if (len(group) == 1 and check_Group_Exists(group[0])) or len(group) == 0:
                if check_User_Exists(username) is False:
                    status = edit_User(user_id, username, group)

                    if status:
                        flash("User was edited successfully!", "success")
                    else:
                        flash("User couldn't be changed!", "error")

                    if user_id == session['logged_in'] and status:
                        return redirect(url_for("login_bp.logout"))
                else:
                    flash("Username already exists!", "error")
            else:
                flash("Select only one group at a time!", "error")
        else:
            db = SQLiteDatabase()
            groups = db.get_All_Permission_Groups()
            del db
            return render_template("index_edit_user.html", user_id=user_id, username=c_username, groups=groups, current_group=p_group)
    elif u_status is True and deletable == 0:
        flash("User can't be changed!", "error")
    else:
        flash("User doesn't exist!", "error")
    return redirect(url_for("user_bp.index"))


@user_bp.route('/change_password/<user_id>', methods=['GET', 'POST'])
@logged_in
@authenticate
def change_password(user_id):
    if request.method == 'POST':
        data = request.form
        status = change_User_Password(user_id, data.get("password", ''), data.get('confirm_password', ''))

        if status:
            flash("Password was changed successfully!", "success")
        else:
            flash("Password can't be changed!", "error")

        if user_id == session['logged_in'] and status:
            return redirect(url_for("login_bp.logout"))
        else:
            return redirect(url_for("user_bp.index"))
    else:
        return render_template("index_change_password.html", user_id=user_id)


@user_bp.route('/delete_user/<user_id>', methods=['POST'])
@logged_in
@authenticate
def delete_user(user_id):
    if user_id != session['logged_in']:
        status = delete_User(user_id)

        if status:
            flash("User was deleted successfully!", "success")
        else:
            flash("User can't be deleted!", "error")
    else:
        flash("You can't delete yourself!", "error")
    return redirect(url_for("user_bp.index"))
