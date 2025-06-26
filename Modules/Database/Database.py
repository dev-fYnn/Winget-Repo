import sqlite3
import sys

from Modules.Functions import generate_random_string, select_to_dict


class SQLiteDatabase:
    def __init__(self, db_file=rf"{sys.path[0]}\Modules\Database\Database.db"):
        self.__conn = sqlite3.connect(db_file)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        if self.__conn:
            self.__conn.close()

    def db_commit(self, without: bool = False):
        if self.__conn and (self.__cursor.rowcount > 0 or without):
            self.__conn.commit()

    def get_Fields_by_Section(self, section: str, lang: str) -> dict:
        self.__cursor.execute("SELECT FIELD_ID, TEXT FROM tbl_FIELDS WHERE SECTION = ? AND LANGUAGE = ?", (section, lang))
        data = self.__cursor.fetchall()
        return {d[0]: d[1] for d in data}

    def authenticate_client(self, token: str) -> list:
        self.__cursor.execute("""SELECT * FROM tbl_CLIENTS WHERE TOKEN = ?""", (token,))
        client = self.__cursor.fetchone()

        if client is not None and len(client) > 0:
            return client
        return []

    def get_All_Clients(self) -> list:
        self.__cursor.execute("SELECT * FROM tbl_CLIENTS")
        data = self.__cursor.fetchall()
        return select_to_dict(data, self.__cursor.description)

    def add_New_Client(self, uid: str, client_name: str, ip: str, token: str):
        self.__cursor.execute("""INSERT INTO tbl_CLIENTS (UID, NAME, IP, TOKEN) VALUES (?, ?, ?, ?)""", (uid, client_name, ip, token))
        self.db_commit()

    def update_Client_Informations(self, ip: str, last_seen: str, uid: str):
        self.__cursor.execute("""UPDATE tbl_CLIENTS SET IP = ?, LASTSEEN = ? WHERE UID = ?""", (ip, last_seen, uid))
        self.db_commit()

    def delete_Client(self, client_id: str):
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS WHERE UID = ?""", (client_id,))

    def get_All_Packages(self) -> list:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES""")
        data = self.__cursor.fetchall()
        return [{"id": d[0], "name": d[1], "publisher": d[2], "description": d[3]} for d in data]

    def get_All_Locales(self) -> list:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES_LOCALE""")
        data = self.__cursor.fetchall()
        return [{"id": d[0], "name": d[1]} for d in data]

    def get_All_Permission_Groups(self) -> list:
        self.__cursor.execute("SELECT * FROM tbl_USER_RIGHTS")
        data = self.__cursor.fetchall()
        data = select_to_dict(data, self.__cursor.description)
        return data

    def check_Package_exists(self, package_id: str) -> bool:
        self.__cursor.execute("""SELECT PACKAGE_ID FROM tbl_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))
        data = self.__cursor.fetchone()
        if data is not None and len(data) > 0:
            return True
        return False

    def search_packages(self, search_text: str, search_type: str, search_field: str):
        search_text = search_text.strip()
        query = f"""SELECT * FROM tbl_PACKAGES
                    WHERE """

        if search_field == "PackageName":
            query += "PACKAGE_NAME"
        else:
            query += "PACKAGE_ID"

        if search_type == 'exact':
            query += " = ?"
            params = (search_text,)
        elif search_type == 'case_insensitive':
            query += " LIKE ? COLLATE NOCASE"
            params = (f'%{search_text}%',)
        else:
            query += " LIKE ?"
            params = (f'%{search_text}%',)

        self.__cursor.execute(query, params)
        data = self.__cursor.fetchall()
        return [list(d) for d in data]

    def get_All_Versions_from_Package(self, package_id: str) -> list:
        self.__cursor.execute("""SELECT PV.PACKAGE_ID, PV.VERSION, PL.LOCALE, PV.ARCHITECTURE, PV.INSTALLER_TYPE, PV.INSTALLER_URL, PV.INSTALLER_SHA256, PV.INSTALLER_SCOPE, PV.UID FROM tbl_PACKAGES_VERSIONS AS PV
                                    INNER JOIN tbl_PACKAGES_LOCALE AS PL ON PV.LOCALE_ID = PL.LOCALE_ID
                                WHERE PV.PACKAGE_ID = ?""", (package_id,))
        data = self.__cursor.fetchall()
        return [{"ID": d[0], "Version": d[1], "Locale": d[2], "Architecture": d[3], "Type": d[4], "URL": d[5], "SHA256": d[6], "Scope": d[7], "UID": d[8]} for d in data]

    def get_specfic_Versions_from_Package(self, uid: str) -> dict:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES_VERSIONS WHERE UID = ?""", (uid,))
        data = self.__cursor.fetchone()

        if data is not None:
            return {"ID": data[0], "Version": data[1], "Locale": data[2], "Architecture": data[3], "Type": data[4], "URL": data[5], "SHA256": data[6], "Scope": data[7], "UID": data[8]}
        return {}

    def get_Package_by_ID(self, package_id: str) -> list:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))
        data = self.__cursor.fetchone()
        return list(data)

    def get_specific_Package(self, package_id: str, version: str) -> list:
        if version is None:
            self.__cursor.execute("""SELECT P.PACKAGE_ID, P.PACKAGE_NAME, P.PACKAGE_PUBLISHER, P.PACKAGE_DESCRIPTION, PL.LOCALE, PV.VERSION, PV.ARCHITECTURE, PV.INSTALLER_TYPE, PV.INSTALLER_URL, PV.INSTALLER_SHA256, PV.INSTALLER_SCOPE, PV.UID FROM tbl_PACKAGES AS P
                                            INNER JOIN tbl_PACKAGES_VERSIONS AS PV ON P.PACKAGE_ID = PV.PACKAGE_ID
                                            INNER JOIN tbl_PACKAGES_LOCALE AS PL ON PV.LOCALE_ID = PL.LOCALE_ID
                                        WHERE P.PACKAGE_ID = ?
                                        ORDER BY PV.VERSION DESC""", (package_id,))
        else:
            self.__cursor.execute("""SELECT P.PACKAGE_ID, P.PACKAGE_NAME, P.PACKAGE_PUBLISHER, P.PACKAGE_DESCRIPTION, PL.LOCALE, PV.VERSION, PV.ARCHITECTURE, PV.INSTALLER_TYPE, PV.INSTALLER_URL, PV.INSTALLER_SHA256, PV.INSTALLER_SCOPE, PV.UID FROM tbl_PACKAGES AS P
                                            INNER JOIN tbl_PACKAGES_VERSIONS AS PV ON P.PACKAGE_ID = PV.PACKAGE_ID
                                            INNER JOIN tbl_PACKAGES_LOCALE AS PL ON PV.LOCALE_ID = PL.LOCALE_ID
                                        WHERE P.PACKAGE_ID = ?
                                            AND PV.VERSION = ?""", (package_id, version))
        data = self.__cursor.fetchall()
        if len(data) > 0:
            return data
        return []

    def get_Package_Switche(self, package_version_uid: str) -> dict:
        self.__cursor.execute("""SELECT SWITCH_TYPE, SWITCH_TEXT FROM tbl_PACKAGES_SWITCHES 
                                    WHERE PACKAGE_VERSION_UID = ?""", (package_version_uid,))
        data = self.__cursor.fetchall()

        if len(data) > 0:
            return {d[0]: d[1] for d in data}
        return {}

    def get_winget_Settings(self, secret: bool = False) -> dict:
        self.__cursor.execute("""SELECT SETTING_NAME, VALUE FROM tbl_SETTINGS""")
        data = self.__cursor.fetchall()

        if len(data) > 0:
            data = dict(data)

            if secret is False and 'SECRET_KEY' in data.keys():
                data.pop('SECRET_KEY')
            elif secret is True and 'SECRET_KEY' not in data.keys():
                data['SECRET_KEY'] = generate_random_string(32)
                self.add_wingetrepo_Setting("SECRET_KEY", data['SECRET_KEY'], "TEXT", False)
                self.db_commit()

            return data
        return {}

    def get_Settings_for_View(self) -> dict:
        self.__cursor.execute("""SELECT SETTING_NAME, VALUE, TYPE FROM tbl_SETTINGS WHERE SHOW = 1""")
        data = self.__cursor.fetchall()

        if len(data) > 0:
            return {d[0]: {"VALUE": d[1], "TYPE": d[2]} for d in data}
        return {}

    def add_wingetrepo_Setting(self, name: str, value: str, settings_type: str, show: bool) -> bool:
        self.__cursor.execute("""INSERT OR IGNORE INTO tbl_SETTINGS (SETTING_NAME, VALUE, TYPE, SHOW) 
                                    VALUES (?, ?, ?, ?)""",
                              (name, value, settings_type, int(show)))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def update_wingetrepo_Setting(self, name: str, value: str):
        self.__cursor.execute("""UPDATE tbl_SETTINGS SET VALUE = ? WHERE SETTING_NAME = ?""", (value, name))

    def add_New_Group(self, group_name: str, id: str):
        self.__cursor.execute("""INSERT INTO tbl_USER_RIGHTS (ID, NAME) VALUES (?, ?)""", (id, group_name))
        self.db_commit()

    def add_Package(self, package_id: str, package_name: str, package_publisher: str, package_description: str) -> bool:
        self.__cursor.execute("""INSERT OR REPLACE INTO tbl_PACKAGES (PACKAGE_ID, PACKAGE_NAME, PACKAGE_PUBLISHER, PACKAGE_DESCRIPTION) 
                                    VALUES (?, ?, ?, ?)""",
                              (package_id, package_name, package_publisher, package_description))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def add_Package_Version(self, package_id: str, package_version: str, package_local: str, file_architecture: str, file_type: str, file_download: str, file_sha: str, file_scope: str, uid: str) -> bool:
        self.__cursor.execute("""INSERT OR IGNORE INTO tbl_PACKAGES_VERSIONS (PACKAGE_ID, VERSION, LOCALE_ID, ARCHITECTURE, INSTALLER_TYPE, INSTALLER_URL, INSTALLER_SHA256, INSTALLER_SCOPE, UID) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (package_id, package_version, package_local, file_architecture, file_type, file_download, file_sha, file_scope, uid))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def add_Package_Version_Switch(self, package_version_uid: str, switch_type: str, switch_text: str) -> bool:
        self.__cursor.execute("""INSERT OR REPLACE INTO tbl_PACKAGES_SWITCHES (PACKAGE_VERSION_UID, SWITCH_TYPE, SWITCH_TEXT)
                                    VALUES (?, ?, ?)""",
                              (package_version_uid, switch_type, switch_text))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def update_Permission(self, group_id: str, permission_name: str, state: int):
        self.__cursor.execute(f"""UPDATE tbl_USER_RIGHTS SET "{permission_name}" = ? WHERE ID = ?""", (state, group_id))

    def update_User_Password(self, user_id: str, password: str):
        self.__cursor.execute(f"""UPDATE tbl_USER SET PW = ? WHERE ID = ?""", (password, user_id))
        self.db_commit()

    def delete_Package(self, package_id: str):
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))

    def delete_Package_Version(self, version_uid: str):
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES_VERSIONS WHERE UID = ?""", (version_uid,))
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES_SWITCHES WHERE PACKAGE_VERSION_UID = ?""", (version_uid,))

    def get_Text_by_Typ(self, text_id: str) -> str:
        self.__cursor.execute("SELECT TEXT FROM tbl_TEXTS WHERE ID = ?", (text_id,))
        data = self.__cursor.fetchone()
        if len(data) > 0 and data[0] is not None:
            return data[0]
        return ""

    def update_Text_by_Typ(self, text_id: str, text: str) -> str:
        self.__cursor.execute("UPDATE tbl_TEXTS SET TEXT = ? WHERE ID = ?", (text, text_id))
        self.__conn.commit()

    def check_User_Credentials(self, username: str) -> dict:
        self.__cursor.execute("""SELECT ID, PW FROM tbl_USER WHERE USERNAME = ?""", (username,))
        data = self.__cursor.fetchone()

        if data is not None and len(data) > 0:
            return {"id": data[0], "hash": data[1]}
        return {}

    def check_User_Authentication(self, username: str) -> dict:
        self.__cursor.execute("""SELECT TUR.* FROM tbl_USER_RIGHTS AS TUR 
                                            LEFT JOIN tbl_USER AS TU ON TUR.ID = TU."GROUP"
                                        WHERE TU.ID = ?""", (username,))
        data = self.__cursor.fetchall()
        data = select_to_dict(data, self.__cursor.description)
        if len(data) > 0:
            return data[0]
        return {}

    def check_Username_exists(self, username: str, user_id="") -> tuple[bool, int, str, str]:
        if len(user_id) > 0:
            self.__cursor.execute("""SELECT USERNAME, DELETABLE, "GROUP" FROM tbl_USER WHERE ID = ?""", (user_id,))
        else:
            self.__cursor.execute("""SELECT USERNAME, DELETABLE, "GROUP" FROM tbl_USER WHERE USERNAME = ?""", (username,))
        data = self.__cursor.fetchone()

        if data is not None and len(data) > 0:
            return True, data[1], data[0], data[2]
        return False, 0, "", ""

    def check_Group_exists(self, group_id: str) -> bool:
        self.__cursor.execute("""SELECT * FROM tbl_USER_RIGHTS WHERE ID = ?""", (group_id,))
        data = self.__cursor.fetchone()

        if data is not None and len(data) > 0:
            return True
        return False

    def get_All_User(self):
        self.__cursor.execute("""SELECT TU.*, TUR.NAME FROM tbl_USER AS TU
                                    LEFT JOIN tbl_USER_RIGHTS AS TUR ON TU."GROUP" = TUR.ID""")
        data = self.__cursor.fetchall()
        data = select_to_dict(data, self.__cursor.description)
        return data

    def add_User(self, uid: str, username: str, password: str, group: str, deletable: int = 1) -> bool:
        self.__cursor.execute("""INSERT OR IGNORE INTO tbl_USER (ID, USERNAME, PW, DELETABLE, "GROUP") VALUES (?, ?, ?, ?, ?)""", (uid, username, password, deletable, group))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def update_User(self, uid: str, username: str = None, group: list = None) -> bool:
        if username is not None:
            self.__cursor.execute("""UPDATE tbl_USER SET USERNAME = ? WHERE ID = ?""", (username, uid))
        if len(group) == 1:
            self.__cursor.execute("""UPDATE tbl_USER SET "GROUP" = ? WHERE ID = ?""", (group[0], uid))
        return True

    def delete_User(self, user_id: str):
        self.__cursor.execute("""DELETE FROM tbl_USER WHERE ID = ? AND DELETABLE = 1""", (user_id,))

    def delete_Group(self, group_id: str):
        self.__cursor.execute("""DELETE FROM tbl_USER_RIGHTS WHERE ID = ?""", (group_id,))
        self.db_commit()
