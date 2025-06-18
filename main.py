import os

from flask import Flask, send_from_directory

from Modules.Clients.Clients import client_bp
from Modules.Groups.Functions import groups_bp
from Modules.Login.Login import login_bp
from Modules.UI.UI import ui_bp
from Modules.User.User import user_bp
from Modules.Winget.Functions import get_winget_Settings
from Modules.Winget.winget_Routes import winget_routes

settings = get_winget_Settings(True)

app = Flask(__name__)
app.secret_key = settings['SECRET_KEY'].encode()
app.config['SESSION_COOKIE_NAME'] = settings['SERVER_NAME']
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.jinja_env.add_extension('jinja2.ext.do')

app.register_blueprint(login_bp, url_prefix='/')
app.register_blueprint(ui_bp, url_prefix='/ui')
app.register_blueprint(user_bp, url_prefix='/ui/users')
app.register_blueprint(groups_bp, url_prefix='/ui/groups')
app.register_blueprint(client_bp, url_prefix='/ui/clients')
app.register_blueprint(winget_routes, url_prefix='/api')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run()
