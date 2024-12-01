from uuid import uuid4
from werkzeug.security import generate_password_hash

from Modules.Database.Database import SQLiteDatabase


def user_setup_finished() -> bool:
    db = SQLiteDatabase()
    data = db.get_All_Users()
    del db

    if len(data) > 0:
        return True
    return False


def add_User(username: str, password: str, deletable: int = 1) -> bool:
    password = generate_password_hash(password)

    db = SQLiteDatabase()
    status = db.add_User(str(uuid4()), username, password, deletable)
    db.db_commit()
    del db
    return status


def check_User_Exists(username: str) -> bool:
    db = SQLiteDatabase()
    status, _ = db.check_Username_exists(username)
    del db
    return status


def delete_User(user_id: str) -> bool:
    db = SQLiteDatabase()
    status, deletable = db.check_Username_exists("", user_id)

    if status and deletable == 1:
        db.delete_User(user_id)
        db.db_commit()
        status = True
    else:
        status = False

    del db
    return status
