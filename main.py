import os

from flask import Flask, send_from_directory, url_for

from Modules.Functions import start_up_check
from Modules.Clients.Clients import client_bp
from Modules.Groups.Functions import groups_bp
from Modules.Login.Login import login_bp
from Modules.Settings.Settings import settings_bp
from Modules.Store.store import store_bp
from Modules.UI.UI import ui_bp
from Modules.User.User import user_bp
from Modules.Winget.Functions import get_winget_Settings
from Modules.Winget.winget_Routes import winget_routes
from Modules.API.API import api_bp

settings = get_winget_Settings(True)

app = Flask(__name__)
app.config['SERVERNAME'] = settings['SERVERNAME']
app.secret_key = settings['SECRET_KEY'].encode()
app.config['SESSION_COOKIE_NAME'] = app.config['SERVERNAME']
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['active_downloads'] = {}
app.jinja_env.add_extension('jinja2.ext.do')

app.register_blueprint(login_bp, url_prefix='/')
app.register_blueprint(ui_bp, url_prefix='/ui')
app.register_blueprint(user_bp, url_prefix='/ui/user')
app.register_blueprint(groups_bp, url_prefix='/ui/groups')
app.register_blueprint(client_bp, url_prefix='/ui/clients')
app.register_blueprint(settings_bp, url_prefix='/ui/settings')
app.register_blueprint(store_bp, url_prefix='/ui/store')
app.register_blueprint(api_bp, url_prefix='/client/api')
app.register_blueprint(winget_routes, url_prefix='/api')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),'favicon.png', mimetype='image/png')


@app.context_processor
def global_settings():
    return {
        'app_name': app.config['SERVERNAME'],
        'app_logo': url_for('static', filename='images/logo.png')
    }


if __name__ == '__main__':
    start_up_check()
    app.run()
