from werkzeug.security import check_password_hash

from Modules.Database.Database import SQLiteDatabase


def check_Credentials(username: str, password: str) -> tuple[bool, str]:
    db = SQLiteDatabase()
    data = db.check_User_Credentials(username)
    del db

    if len(data) > 0 and check_password_hash(data['PW'], password):
        return True, data['ID']
    return False, ""


def check_Rights(userid: str, endpoint: str) -> bool:
    db = SQLiteDatabase()
    data = db.check_User_Authentication(userid)
    del db

    if len(data) > 0:
        if data.get(endpoint.upper(), 0) == 1:
            return True
    return False
