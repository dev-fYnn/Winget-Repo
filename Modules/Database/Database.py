import sqlite3

from Modules.Functions import generate_random_string, all_to_dict, row_to_dict
from settings import PATH_DATABASE


class SQLiteDatabase:
    def __init__(self, db_file=PATH_DATABASE):
        self.__conn = sqlite3.connect(db_file, timeout=10)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        if self.__conn:
            self.__conn.close()

    def db_commit(self, without: bool = False):
        if self.__conn and (self.__cursor.rowcount > 0 or without):
            self.__conn.commit()

    #----------------Settings--------------------
    ##############Fields##################
    def get_Fields_by_Section(self, section: str, lang: str) -> dict:
        self.__cursor.execute("SELECT FIELD_ID, TEXT FROM tbl_FIELDS WHERE SECTION = ? AND LANGUAGE = ?", (section, lang))
        data = self.__cursor.fetchall()
        return {d[0]: d[1] for d in data}

    ##############Settings##################
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
        self.__cursor.execute("""SELECT SETTING_NAME, VALUE, TYPE, MAX_LENGTH, INTERNET FROM tbl_SETTINGS WHERE SHOW = 1""")
        data = self.__cursor.fetchall()
        return {d[0]: {"VALUE": d[1], "TYPE": d[2], "MAX_LENGTH": d[3], "INTERNET": d[4]} for d in data}

    def add_wingetrepo_Setting(self, name: str, value: str, settings_type: str, show: bool) -> bool:
        self.__cursor.execute("""INSERT OR IGNORE INTO tbl_SETTINGS (SETTING_NAME, VALUE, TYPE, SHOW) 
                                    VALUES (?, ?, ?, ?)""",
                              (name, value, settings_type, int(show)))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def update_wingetrepo_Setting(self, name: str, value: str):
        self.__cursor.execute("""UPDATE tbl_SETTINGS SET VALUE = ? WHERE SETTING_NAME = ?""", (value, name))

    ##############Texts##################
    def get_Text_by_Typ(self, text_id: str) -> dict:
        self.__cursor.execute("SELECT IFNULL(TEXT, '') AS TEXT FROM tbl_TEXTS WHERE ID = ?", (text_id,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def update_Text_by_Typ(self, text_id: str, text: str) -> str:
        self.__cursor.execute("UPDATE tbl_TEXTS SET TEXT = ? WHERE ID = ?", (text, text_id))
        self.__conn.commit()


    #-----------------Clients-------------------
    ##############Clients##################
    def authenticate_client(self, token: str) -> dict:
        self.__cursor.execute("""SELECT * FROM tbl_CLIENTS WHERE TOKEN = ?""", (token,))
        client = self.__cursor.fetchone()
        return row_to_dict(client, self.__cursor.description)

    def get_All_Clients(self) -> list:
        self.__cursor.execute("""SELECT C.*, 
                                    (SELECT GROUP_CONCAT(NAME, ', ')
                                        FROM (
                                            SELECT DISTINCT BG.NAME
                                            FROM tbl_BLACKLIST_GROUPS_CLIENTS AS BGC2
                                            LEFT JOIN tbl_BLACKLIST_GROUPS AS BG ON BGC2.GROUP_ID = BG.UID
                                            WHERE BGC2.CLIENT_AUTH_TOKEN = C.TOKEN
                                        )) AS B_GROUPS
                                FROM tbl_CLIENTS AS C
                                ORDER BY C.NAME;""")
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def get_Client_by_IP(self, ip: str) -> dict:
        self.__cursor.execute("SELECT * FROM tbl_CLIENTS WHERE IP = ?", (ip,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def get_Client_by_ID(self, uid: str) -> dict:
        self.__cursor.execute("SELECT * FROM tbl_CLIENTS WHERE UID = ?", (uid,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def add_New_Client(self, uid: str, client_name: str, ip: str, token: str) -> bool:
        self.__cursor.execute("""SELECT * FROM tbl_CLIENTS WHERE NAME = ?""", (client_name,))
        data = self.__cursor.fetchone()

        if data is None:
            self.__cursor.execute("""INSERT INTO tbl_CLIENTS (UID, NAME, IP, TOKEN) VALUES (?, ?, ?, ?)""", (uid, client_name, ip, token))
            self.db_commit()

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def update_Client_Enable_Status(self, client_id: str, status: int):
        self.__cursor.execute("""UPDATE tbl_CLIENTS SET ENABLED = ? WHERE UID = ?""", (status, client_id,))
        self.db_commit()

    def update_Client_Informations(self, ip: str, last_seen: str, uid: str, client: int = 0):
        self.__cursor.execute("""UPDATE tbl_CLIENTS SET IP = ?, LASTSEEN = ?, CLIENT = ? WHERE UID = ?""", (ip, last_seen, client, uid))
        self.db_commit()

    def delete_Client(self, client_id: str, auth_token: str):
        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_GROUPS_CLIENTS WHERE CLIENT_AUTH_TOKEN = ?""", (auth_token,))
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS_PACKAGES_BLACKLIST WHERE CLIENT_AUTH_TOKEN = ?""", (auth_token,))
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS_LOGS WHERE CLIENT_ID = ?""", (client_id,))
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS WHERE UID = ?""", (client_id,))
        self.db_commit()

    ##############Blacklist##################
    def get_Blacklist_for_client(self, auth_token: str, groups: bool=True) -> list:
        self.__cursor.execute("""SELECT PACKAGE_ID FROM tbl_CLIENTS_PACKAGES_BLACKLIST WHERE CLIENT_AUTH_TOKEN = ?""", (auth_token,))
        data = self.__cursor.fetchall()
        dummy = [d[0] for d in data]

        if groups:
            self.__cursor.execute("""SELECT DISTINCT BP.PACKAGE_ID FROM tbl_BLACKLIST_GROUPS_CLIENTS AS BGC
                                            INNER JOIN tbl_BLACKLIST_PACKAGES AS BP ON BGC.GROUP_ID = BP.GROUP_ID
                                        WHERE BGC.CLIENT_AUTH_TOKEN = ?""", (auth_token,))
            data = self.__cursor.fetchall()
            dummy.extend([d[0] for d in data])
        return list(set(dummy))

    def update_Blacklist_Package(self, auth_token: str, packages: list):
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS_PACKAGES_BLACKLIST WHERE CLIENT_AUTH_TOKEN = ?""", (auth_token,))

        for p in packages:
            self.__cursor.execute("""INSERT INTO tbl_CLIENTS_PACKAGES_BLACKLIST (CLIENT_AUTH_TOKEN, PACKAGE_ID) VALUES (?, ?)""", (auth_token, p))
        self.db_commit()

    ##############Blacklist-Groups################
    def get_All_Blacklist_Groups(self) -> list:
        self.__cursor.execute("""SELECT TBG.UID, TBG.NAME, COUNT(TBP.PACKAGE_ID) AS PACKAGE_COUNT FROM tbl_BLACKLIST_GROUPS AS TBG
                                    LEFT JOIN tbl_BLACKLIST_PACKAGES AS TBP ON TBG.UID = TBP.GROUP_ID
                                GROUP BY TBG.UID, TBG.NAME""")
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def get_Blacklist_Group(self, group_id: str) -> dict:
        self.__cursor.execute("""SELECT * FROM tbl_BLACKLIST_GROUPS WHERE UID = ?""", (group_id,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def get_Blacklist_Groups_for_Client(self, client_auth_token: str) -> list:
        self.__cursor.execute("""SELECT GROUP_ID FROM tbl_BLACKLIST_GROUPS_CLIENTS WHERE CLIENT_AUTH_TOKEN = ?""", (client_auth_token,))
        data = self.__cursor.fetchall()
        return [d[0] for d in data]

    def get_Packages_from_Blacklist_Group(self, group_id: str) -> list:
        self.__cursor.execute("""SELECT PACKAGE_ID FROM tbl_BLACKLIST_PACKAGES WHERE GROUP_ID = ?""", (group_id,))
        data = self.__cursor.fetchall()
        return [d[0] for d in data]

    def update_Blacklist_Groups_Clients(self, auth_token: str, groups: list):
        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_GROUPS_CLIENTS WHERE CLIENT_AUTH_TOKEN = ?""", (auth_token,))

        for g in groups:
            self.__cursor.execute("""INSERT INTO tbl_BLACKLIST_GROUPS_CLIENTS (GROUP_ID, CLIENT_AUTH_TOKEN) VALUES (?, ?)""", (g, auth_token))
        self.db_commit(True)

    def insert_update_Blacklist_Group(self, uid: str, name: str, packages: list):
        self.__cursor.execute("""INSERT OR REPLACE INTO tbl_BLACKLIST_GROUPS (UID, NAME) VALUES (?, ?)""", (uid, name))

        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_PACKAGES WHERE GROUP_ID = ?""", (uid,))
        for p in packages:
            self.__cursor.execute("""INSERT INTO tbl_BLACKLIST_PACKAGES (GROUP_ID, PACKAGE_ID) VALUES (?, ?)""", (uid, p))
        self.db_commit(True)

    def remove_Blacklist_Group(self, group_id: str):
        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_PACKAGES WHERE GROUP_ID = ?""", (group_id,))
        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_GROUPS_CLIENTS WHERE GROUP_ID = ?""", (group_id,))
        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_GROUPS WHERE UID = ?""", (group_id,))
        self.db_commit()

    ##############Logs##################
    def get_Logs_for_Client(self, client_id: str) -> list:
        self.__cursor.execute("SELECT * FROM tbl_CLIENTS_LOGS WHERE CLIENT_ID = ? ORDER BY TIMESTAMP DESC", (client_id,))
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def insert_Log(self, client_id: str, log_type: str, log_message: str, timestamp: str):
        self.__cursor.execute("""INSERT INTO tbl_CLIENTS_LOGS (CLIENT_ID, LOG_TYPE, LOG_MESSAGE, TIMESTAMP) VALUES (?, ?, ?, ?)""", (client_id, log_type, log_message, timestamp))
        self.db_commit()

    def remove_logs(self, client_id: str):
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS_LOGS WHERE CLIENT_ID = ?""", (client_id,))
        self.db_commit()

    #-------------------Packages--------------------
    def check_Package_exists(self, package_id: str) -> bool:
        self.__cursor.execute("""SELECT PACKAGE_ID FROM tbl_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))
        data = self.__cursor.fetchone()
        if data is not None and len(data) > 0:
            return True
        return False

    def search_packages(self, search_text: str, search_type: str, search_field: str):
        search_text = search_text.strip()
        query = f"""SELECT * FROM tbl_PACKAGES
                    WHERE PACKAGE_ACTIVE = 1
                        AND """

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
        return all_to_dict(data, self.__cursor.description)

    def get_All_Packages(self, disabled: bool = True) -> list:
        if disabled:
            self.__cursor.execute("""SELECT * FROM tbl_PACKAGES ORDER BY PACKAGE_ID""")
        else:
            self.__cursor.execute("""SELECT * FROM tbl_PACKAGES WHERE PACKAGE_ACTIVE = 1 ORDER BY PACKAGE_ID""")
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def get_Package_by_ID(self, package_id: str) -> dict:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def get_specific_Package(self, package_id: str, version: str) -> list:
        if version is None:
            self.__cursor.execute("""SELECT P.PACKAGE_ID, P.PACKAGE_NAME, P.PACKAGE_PUBLISHER, P.PACKAGE_DESCRIPTION, PL.LOCALE, PV.VERSION, PV.ARCHITECTURE, PV.INSTALLER_TYPE, PV.INSTALLER_URL, PV.INSTALLER_SHA256, PV.INSTALLER_SCOPE, PV.UID, PV.INSTALLER_NESTED_TYPE FROM tbl_PACKAGES AS P
                                            INNER JOIN tbl_PACKAGES_VERSIONS AS PV ON P.PACKAGE_ID = PV.PACKAGE_ID
                                            INNER JOIN tbl_PACKAGES_LOCALE AS PL ON PV.LOCALE_ID = PL.LOCALE_ID
                                        WHERE P.PACKAGE_ID = ?
                                            AND P.PACKAGE_ACTIVE = 1
                                        ORDER BY PV.VERSION DESC""", (package_id,))
        else:
            self.__cursor.execute("""SELECT P.PACKAGE_ID, P.PACKAGE_NAME, P.PACKAGE_PUBLISHER, P.PACKAGE_DESCRIPTION, PL.LOCALE, PV.VERSION, PV.ARCHITECTURE, PV.INSTALLER_TYPE, PV.INSTALLER_URL, PV.INSTALLER_SHA256, PV.INSTALLER_SCOPE, PV.UID, PV.INSTALLER_NESTED_TYPE FROM tbl_PACKAGES AS P
                                            INNER JOIN tbl_PACKAGES_VERSIONS AS PV ON P.PACKAGE_ID = PV.PACKAGE_ID
                                            INNER JOIN tbl_PACKAGES_LOCALE AS PL ON PV.LOCALE_ID = PL.LOCALE_ID
                                        WHERE P.PACKAGE_ID = ?
                                            AND P.PACKAGE_ACTIVE = 1
                                            AND PV.VERSION = ?""", (package_id, version))
        data = self.__cursor.fetchall()
        if len(data) > 0:
            return data
        return []

    def add_Package(self, package_id: str, package_name: str, package_publisher: str, package_description: str, package_logo: str, package_active: int = 1) -> bool:
        self.__cursor.execute("""INSERT OR REPLACE INTO tbl_PACKAGES (PACKAGE_ID, PACKAGE_NAME, PACKAGE_PUBLISHER, PACKAGE_DESCRIPTION, PACKAGE_LOGO, PACKAGE_ACTIVE) 
                                    VALUES (?, ?, ?, ?, ?, ?)""",
                              (package_id, package_name, package_publisher, package_description, package_logo, package_active))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def delete_Package(self, package_id: str):
        self.__cursor.execute("""DELETE FROM tbl_BLACKLIST_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))
        self.__cursor.execute("""DELETE FROM tbl_CLIENTS_PACKAGES_BLACKLIST WHERE PACKAGE_ID = ?""", (package_id,))
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES WHERE PACKAGE_ID = ?""", (package_id,))


    #----------------Package-Version----------------
    def check_Package_Version_not_exists(self, package_id: str, package_version: str, package_local: int, file_architecture: str, file_type: str, file_scope: str) -> bool:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES_VERSIONS WHERE PACKAGE_ID = ? AND VERSION = ? AND LOCALE_ID = ? AND ARCHITECTURE = ? AND INSTALLER_TYPE = ? AND INSTALLER_SCOPE = ?""", (package_id, package_version, package_local, file_architecture, file_type, file_scope))
        data = self.__cursor.fetchone()

        if data is None:
            return True
        return False

    def get_All_Versions_from_Package(self, package_id: str) -> list:
        self.__cursor.execute("""SELECT PV.PACKAGE_ID, PV.VERSION, PL.LOCALE AS LOCALE, PV.ARCHITECTURE, PV.INSTALLER_TYPE, PV.INSTALLER_URL, PV.INSTALLER_SHA256, PV.INSTALLER_SCOPE, PV.UID, PV.INSTALLER_NESTED_TYPE FROM tbl_PACKAGES_VERSIONS AS PV
                                    INNER JOIN tbl_PACKAGES_LOCALE AS PL ON PV.LOCALE_ID = PL.LOCALE_ID
                                WHERE PV.PACKAGE_ID = ?
                                ORDER BY PV.VERSION DESC""", (package_id,))
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def get_specfic_Versions_from_Package(self, uid: str) -> dict:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES_VERSIONS WHERE UID = ?""", (uid,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def add_Package_Version(self, package_id: str, package_version: str, package_local: int, file_architecture: str, file_type: str, file_download: str, file_sha: str, file_scope: str, uid: str, nested_type: str = None) -> bool:
        if nested_type is not None:
            self.__cursor.execute("""INSERT OR IGNORE INTO tbl_PACKAGES_VERSIONS (PACKAGE_ID, VERSION, LOCALE_ID, ARCHITECTURE, INSTALLER_TYPE, INSTALLER_NESTED_TYPE, INSTALLER_URL, INSTALLER_SHA256, INSTALLER_SCOPE, UID) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                  (package_id, package_version, package_local, file_architecture, file_type, nested_type, file_download, file_sha, file_scope, uid))
        else:
            self.__cursor.execute("""INSERT OR IGNORE INTO tbl_PACKAGES_VERSIONS (PACKAGE_ID, VERSION, LOCALE_ID, ARCHITECTURE, INSTALLER_TYPE, INSTALLER_URL, INSTALLER_SHA256, INSTALLER_SCOPE, UID) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                  (package_id, package_version, package_local, file_architecture, file_type, file_download, file_sha, file_scope, uid))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def delete_Package_Version(self, version_uid: str):
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES_VERSIONS WHERE UID = ?""", (version_uid,))
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES_SWITCHES WHERE PACKAGE_VERSION_UID = ?""", (version_uid,))
        self.__cursor.execute("""DELETE FROM tbl_PACKAGES_NESTED WHERE PACKAGE_VERSION_UID = ?""", (version_uid,))

    ####################Nested Installer######################
    def get_Nested_Installer(self, package_version_uid: str) -> list[dict]:
        self.__cursor.execute("""SELECT NAME, PATH FROM tbl_PACKAGES_NESTED
                                    WHERE PACKAGE_VERSION_UID = ?""", (package_version_uid,))
        data = self.__cursor.fetchall()
        return [{d[0]: d[1]} for d in data]

    def add_Nested_Installer(self, version_uid: str, name: str, path: str) -> bool:
        self.__cursor.execute("""INSERT OR REPLACE INTO tbl_PACKAGES_NESTED (PACKAGE_VERSION_UID, NAME, PATH)
                                    VALUES (?, ?, ?)""",
                              (version_uid, name, path))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    ####################Switch######################
    def get_Package_Switche(self, package_version_uid: str) -> dict:
        self.__cursor.execute("""SELECT SWITCH_TYPE, SWITCH_TEXT FROM tbl_PACKAGES_SWITCHES 
                                    WHERE PACKAGE_VERSION_UID = ?""", (package_version_uid,))
        data = self.__cursor.fetchall()
        return {d[0]: d[1] for d in data}

    def add_Package_Version_Switch(self, package_version_uid: str, switch_type: str, switch_text: str) -> bool:
        self.__cursor.execute("""INSERT OR REPLACE INTO tbl_PACKAGES_SWITCHES (PACKAGE_VERSION_UID, SWITCH_TYPE, SWITCH_TEXT)
                                    VALUES (?, ?, ?)""",
                              (package_version_uid, switch_type, switch_text))

        if self.__cursor.lastrowid > 0:
            return True
        return False

    ####################Locales######################
    def get_All_Locales(self) -> list:
        self.__cursor.execute("""SELECT * FROM tbl_PACKAGES_LOCALE""")
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def get_Locale_ID_by_Value(self, locale: str) -> int:
        self.__cursor.execute("""SELECT IFNULL(LOCALE_ID, 1) FROM tbl_PACKAGES_LOCALE WHERE LOCALE = ?""", (locale,))
        data = self.__cursor.fetchone()
        if data is None:
            return 1
        return data[0]


    #------------------Permissions-------------------
    def check_Group_exists(self, group_id: str) -> bool:
        self.__cursor.execute("""SELECT * FROM tbl_USER_RIGHTS WHERE ID = ?""", (group_id,))
        data = self.__cursor.fetchone()
        data = row_to_dict(data, self.__cursor.description)

        if data:
            return True
        return False

    def get_All_Permission_Groups(self) -> list:
        self.__cursor.execute("SELECT * FROM tbl_USER_RIGHTS")
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

    def add_New_Group(self, group_name: str, id: str) -> bool:
        self.__cursor.execute("""INSERT INTO tbl_USER_RIGHTS (ID, NAME) VALUES (?, ?)""", (id, group_name))
        self.db_commit()

        if self.__cursor.lastrowid > 0:
            return True
        return False

    def update_Permission(self, group_id: str, permission_name: str, state: int):
        self.__cursor.execute(f"""UPDATE tbl_USER_RIGHTS SET "{permission_name}" = ? WHERE ID = ?""", (state, group_id))

    def delete_Group(self, group_id: str):
        self.__cursor.execute("""DELETE FROM tbl_USER_RIGHTS WHERE ID = ?""", (group_id,))
        self.db_commit()


    #-------------------User----------------------
    def check_Username_exists(self, username: str, user_id="") -> tuple[bool, dict]:
        if len(user_id) > 0:
            self.__cursor.execute("""SELECT DELETABLE, USERNAME, "GROUP" FROM tbl_USER WHERE ID = ?""", (user_id,))
        else:
            self.__cursor.execute("""SELECT USERNAME, DELETABLE, "GROUP" FROM tbl_USER WHERE USERNAME = ?""", (username,))
        data = self.__cursor.fetchone()
        data = row_to_dict(data, self.__cursor.description)

        if data:
            return True, data
        return False, data

    def get_All_User(self):
        self.__cursor.execute("""SELECT TU.*, TUR.NAME FROM tbl_USER AS TU
                                    LEFT JOIN tbl_USER_RIGHTS AS TUR ON TU."GROUP" = TUR.ID""")
        data = self.__cursor.fetchall()
        return all_to_dict(data, self.__cursor.description)

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
        self.db_commit()


    #-------------------User-Authentication----------------------
    def check_User_Credentials(self, username: str) -> dict:
        self.__cursor.execute("""SELECT ID, PW FROM tbl_USER WHERE USERNAME = ?""", (username,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def check_User_Authentication(self, username: str) -> dict:
        self.__cursor.execute("""SELECT TUR.* FROM tbl_USER_RIGHTS AS TUR 
                                            LEFT JOIN tbl_USER AS TU ON TUR.ID = TU."GROUP"
                                        WHERE TU.ID = ?""", (username,))
        data = self.__cursor.fetchone()
        return row_to_dict(data, self.__cursor.description)

    def update_User_Password(self, user_id: str, password: str):
        self.__cursor.execute(f"""UPDATE tbl_USER SET PW = ? WHERE ID = ?""", (password, user_id))
        self.db_commit()
