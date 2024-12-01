from flask import Flask

from Modules.Login.Login import login_bp
from Modules.UI.UI import ui_bp
from Modules.User.User import user_bp
from Modules.Winget.Functions import get_winget_Settings
from Modules.Winget.winget_Routes import winget_routes

app = Flask(__name__)
app.secret_key = get_winget_Settings(True)['SECRET_KEY'].encode()

app.register_blueprint(login_bp, url_prefix='/')
app.register_blueprint(ui_bp, url_prefix='/ui')
app.register_blueprint(user_bp, url_prefix='/ui/users')
app.register_blueprint(winget_routes, url_prefix='/api')

if __name__ == '__main__':
    app.run()
