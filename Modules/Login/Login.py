from functools import wraps
from flask import Blueprint, request, render_template, session, flash, url_for, redirect
import uuid

from Modules.Login.Functions import check_Credentials, check_Rights
from Modules.User.Functions import user_setup_finished
from Modules.Keycloak.KeycloakAuth import keycloak_auth

login_bp = Blueprint('login_bp', __name__, template_folder='templates', static_folder='static')


@login_bp.route('/', methods=["GET"])
def index():
    if user_setup_finished():
        if "logged_in" in session and len(session['logged_in']) > 0:
            return redirect(url_for("ui_bp.index"))
        
        # Check if Keycloak is enabled and should be the primary login method
        if keycloak_auth.is_enabled():
            # Generate state for Keycloak CSRF protection
            keycloak_state = str(uuid.uuid4())
            session['keycloak_state'] = keycloak_state
            keycloak_auth_url = keycloak_auth.get_auth_url(state=keycloak_state)
            
            # If SSO is configured, redirect directly to Keycloak
            if keycloak_auth_url:
                return redirect(keycloak_auth_url)
        
        # Fallback to traditional login form if SSO is not available
        return render_template("index_login.html", 
                             keycloak_enabled=False,
                             keycloak_auth_url=None)
    else:
        return redirect(url_for("user_bp.add_user", back=False))


@login_bp.route('/local', methods=["GET"])
def local_login():
    """Force local login form display, bypassing SSO redirect"""
    if user_setup_finished():
        if "logged_in" in session and len(session['logged_in']) > 0:
            return redirect(url_for("ui_bp.index"))
        
        # Always show traditional login form regardless of SSO configuration
        return render_template("index_login.html", 
                             keycloak_enabled=False,
                             keycloak_auth_url=None)
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


@login_bp.route('/keycloak/callback')
def keycloak_callback():
    """Handle Keycloak OAuth2 callback"""
    if not keycloak_auth.is_enabled():
        flash("Keycloak authentication is not enabled", "error")
        return redirect(url_for("login_bp.index"))
    
    # Get the authorization code from the callback
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    if error:
        flash(f"Keycloak authentication error: {error}", "error")
        return redirect(url_for("login_bp.index"))
    
    if not code:
        flash("No authorization code received from Keycloak", "error")
        return redirect(url_for("login_bp.index"))
    
    # Verify state parameter for CSRF protection
    if state != session.get('keycloak_state'):
        flash("Invalid state parameter. Possible CSRF attack.", "error")
        return redirect(url_for("login_bp.index"))
    
    # Exchange code for token
    token = keycloak_auth.exchange_code_for_token(code)
    if not token:
        flash("Failed to exchange code for token", "error")
        return redirect(url_for("login_bp.index"))
    
    # Get user information
    user_info = keycloak_auth.get_user_info(token)
    if not user_info:
        flash("Failed to get user information from Keycloak", "error")
        return redirect(url_for("login_bp.index"))
    
    # Create or update user in local database
    success, user_id = keycloak_auth.create_or_update_user(user_info)
    if not success or not user_id:
        flash("Failed to create or update user", "error")
        return redirect(url_for("login_bp.index"))
    
    # Set session variables
    session['logged_in'] = user_id
    session['logged_in_username'] = user_info.get('preferred_username') or user_info.get('sub')
    session['keycloak_token'] = token
    session['keycloak_user'] = True
    
    # Clear the state
    if 'keycloak_state' in session:
        session.pop('keycloak_state')
    
    flash("Login successful!", "success")
    return redirect(url_for("ui_bp.index"))


@login_bp.route('/logout')
def logout():
    # If user was logged in via Keycloak, redirect to Keycloak logout
    if 'keycloak_user' in session and keycloak_auth.is_enabled():
        # Clean up local session data
        session.pop('keycloak_user', None)
        session.pop('keycloak_token', None)
        if 'logged_in' in session:
            session.pop('logged_in')
        if 'logged_in_username' in session:
            session.pop('logged_in_username')
        if 'keycloak_state' in session:
            session.pop('keycloak_state')
        
        # Get Keycloak logout URL and redirect
        keycloak_logout_url = keycloak_auth.get_logout_url()
        if keycloak_logout_url:
            return redirect(keycloak_logout_url)
    
    # For local users, clean up session and redirect to login page
    if 'logged_in' in session:
        flash("Logout successfully!", "success")
        session.pop('logged_in')
    if 'logged_in_username' in session:
        session.pop('logged_in_username')
    if 'keycloak_state' in session:
        session.pop('keycloak_state')
    
    return redirect(url_for("login_bp.index"))


def logged_in(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for("login_bp.index"))
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
