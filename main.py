import os
import sys

from a2wsgi import ASGIMiddleware
from fastapi import FastAPI
from flask import Flask, send_from_directory, url_for, render_template
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from Modules.API.API import client_api_bp, APICheckerMiddleware
from Modules.API.api_extensions import api_limiter
from Modules.DevMode.Functions import generate_dev_certificate
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
from main_extensions import csrf, limiter

settings = get_winget_Settings(True)

app = Flask(__name__)
csrf.init_app(app)
limiter.init_app(app)

app.config['SERVERNAME'] = settings['SERVERNAME']
app.secret_key = settings['SECRET_KEY'].encode()
app.config['DOWNLOAD_KEY'] = settings['DOWNLOAD_KEY'].encode()
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
app.register_blueprint(winget_routes, url_prefix='/api')


client_api = FastAPI(title="Winget-Repo REST-API")
client_api.state.limiter = api_limiter
client_api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

client_api.add_middleware(APICheckerMiddleware)
client_api.include_router(client_api_bp)

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/client/api': ASGIMiddleware(client_api)
})


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/images'),'favicon.png', mimetype='image/png')


@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("429.html"), 429


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


@app.context_processor
def global_settings():
    return {
        'app_name': app.config['SERVERNAME'],
        'app_logo': url_for('static', filename='images/logo.png')
    }


if __name__ == '__main__':
    start_up_check()

    if len(sys.argv) > 1 and sys.argv[1] == "/dev":
        status = generate_dev_certificate()
        if status:
            app.config['dev_mode'] = True
            app.run(ssl_context=('SSL/cert.pem', 'SSL/key.pem'), threaded=True)
        else:
            print("Error while starting the development server! Please check the certificates!")
    else:
        app.run()
