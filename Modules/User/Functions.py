from uuid import uuid4
from werkzeug.security import generate_password_hash

from Modules.Database.Database import SQLiteDatabase


def user_setup_finished() -> bool:
    db = SQLiteDatabase()
    data = db.get_All_User()
    del db

    if len(data) > 0:
        return True
    return False


def add_User(username: str, password: str, group: str, deletable: int = 1) -> bool:
    password = generate_password_hash(password)

    db = SQLiteDatabase()
    status = db.add_User(str(uuid4()), username, password, group, deletable)
    db.db_commit()
    del db
    return status


def edit_User(uid: str, username: str, group: list) -> bool:
    db = SQLiteDatabase()
    status, attributes = db.check_Username_exists("", uid)

    if status and attributes.get('DELETABLE', 0) == 1:
        status = db.update_User(uid, username, group)
        db.db_commit()
    del db
    return status


def change_User_Password(username: str, password: str, second_pw: str) -> bool:
    if password == second_pw and len(password) >= 10:
        password = generate_password_hash(password)

        db = SQLiteDatabase()
        db.update_User_Password(username, password)
        db.db_commit()
        del db
        return True
    else:
        return False


def check_User_Exists(username: str, user_id: str = "") -> bool | tuple:
    db = SQLiteDatabase()

    if user_id == "":
        status, attributes= db.check_Username_exists(username)
    else:
        status, attributes = db.check_Username_exists("", user_id)
    del db
    return status, attributes


def check_Group_Exists(group_id: str) -> bool:
    db = SQLiteDatabase()
    status = db.check_Group_exists(group_id)
    del db
    return status


def delete_User(user_id: str) -> bool:
    db = SQLiteDatabase()
    status, attributes = db.check_Username_exists("", user_id)

    if status and attributes.get('DELETABLE', 0) == 1:
        db.delete_User(user_id)
        status = True
    else:
        status = False

    del db
    return status
