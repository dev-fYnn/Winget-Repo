from flask import Blueprint, render_template, redirect, url_for, request, flash, session

from Modules.Database.Database import SQLiteDatabase
from Modules.User.Functions import user_setup_finished, add_User, check_User_Exists, delete_User
from Modules.Login.Login import logged_in

user_bp = Blueprint('user_bp', __name__, template_folder='templates', static_folder='static')


@user_bp.route('/', methods=['GET'])
@logged_in
def index():
    db = SQLiteDatabase()
    users = db.get_All_Users()
    del db
    return render_template("index_manage_user.html", users=users)


@user_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'logged_in' not in session and user_setup_finished() is False:
        flag = 0
    elif 'logged_in' in session:
        flag = 1
    else:
        return redirect(url_for("login_bp.logout"))

    if request.method == "POST":
        data = request.form
        if "username" in data and "password" in data:
            if check_User_Exists(data['username']) is False:
                if len(data['password']) >= 10 and len(data['username']) > 0:
                    status = add_User(data['username'], data['password'], flag)
                    if status:
                        flash("User has been created. Please login!", "success")
                    else:
                        flash("Error creating the user! Try again!", "error")
                else:
                    flash("Invalid submissions!", "error")
            else:
                flash("Username already exists!", "error")
        if flag == 0:
            return redirect(url_for("login_bp.logout"))
        else:
            return redirect(url_for("user_bp.index"))
    return render_template("index_add_user.html", back=request.args.get("back", ""))


@user_bp.route('/delete_user/<user_id>', methods=['POST'])
@logged_in
def delete_user(user_id):
    status = delete_User(user_id)

    if status:
        flash("User was deleted successfully!", "success")
    else:
        flash("User cannot be deleted!", "error")
    return redirect(url_for("user_bp.index"))
