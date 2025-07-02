from functools import wraps
from flask import Blueprint, request, render_template, session, flash, url_for, redirect

from Modules.Login.Functions import check_Credentials, check_Rights
from Modules.User.Functions import user_setup_finished

login_bp = Blueprint('login_bp', __name__, template_folder='templates', static_folder='static')


@login_bp.route('/', methods=["GET"])
def index():
    if user_setup_finished():
        if "logged_in" in session and len(session['logged_in']) > 0:
            return redirect(url_for("ui_bp.index"))
        return render_template("index_login.html")
    else:
        return redirect(url_for("user_bp.add_user", back=False))


@login_bp.route('/login', methods=["POST"])
def login():
    data = request.form

    if "username" in data and "password" in data:
        exists, user_id = check_Credentials(data['username'], data['password'])

        if exists:
            session['logged_in'] = user_id
            session['logged_in_username'] = data['username']
            flash("Login successfully!", "success")
            return redirect(url_for("ui_bp.index"))
        else:
            if 'logged_in' in session:
                session.pop('logged_in')
            if 'logged_in_username' in session:
                session.pop('logged_in_username')

            flash("Wrong credentials!", "error")
    return redirect(url_for("login_bp.index"))


@login_bp.route('/logout')
def logout():
    if 'logged_in' in session:
        flash("Logout successfully!", "success")
        session.pop('logged_in')
    if 'logged_in_username' in session:
        session.pop('logged_in_username')
    return redirect(url_for("login_bp.index"))


def logged_in(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for("login_bp.logout"))
        return f(*args, **kwargs)
    return decorator


def authenticate(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if check_Rights(session['logged_in'], request.endpoint) is False:
            flash("Missing permissions!", "error")
            return redirect(url_for("ui_bp.index"))
        return f(*args, **kwargs)
    return decorator
