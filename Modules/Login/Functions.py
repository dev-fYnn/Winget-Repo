from werkzeug.security import check_password_hash

from Modules.Database.Database import SQLiteDatabase


def check_Credentials(username: str, password: str) -> tuple[bool, str]:
    db = SQLiteDatabase()
    data = db.check_User_Credentials(username)
    del db

    if len(data) > 0 and check_password_hash(data['hash'], password):
        return True, data['id']
    return False, ""
