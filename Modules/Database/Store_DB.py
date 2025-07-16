import sqlite3

from settings import PATH_WINGET_REPOSITORY_DB


class StoreDB:
    def __init__(self, db_file=PATH_WINGET_REPOSITORY_DB):
        self.__conn = sqlite3.connect(db_file, timeout=10)
        self.__cursor = self.__conn.cursor()

    def __del__(self):
        if self.__conn:
            self.__conn.close()

    def db_commit(self):
        if self.__conn and (self.__cursor.rowcount > 0):
            self.__conn.commit()

    def get_Package_Path(self, p_id: str, version: str) -> list:
        self.__cursor.execute("""SELECT m.pathpart FROM manifest AS m
                                        LEFT JOIN ids ON m.id = ids.rowid
                                        LEFT JOIN versions ON m.version = versions.rowid
                                     WHERE ids.id = ? AND versions.version = ?""", (p_id, version))
        start = self.__cursor.fetchone()
        if start:
            path_parts = []
            start = start[0]
            while start is not None:
                self.__cursor.execute("SELECT parent, pathpart FROM pathparts WHERE rowid = ?", (start,))
                row = self.__cursor.fetchone()
                if not row:
                    break
                parent, path_part = row
                path_parts.insert(0, path_part)
                start = parent
            return path_parts
        return []

    def get_Package_Versions(self, p_id: str) -> list:
        self.__cursor.execute("""SELECT versions.version FROM manifest AS m
                                        LEFT JOIN ids ON m.id = ids.rowid
                                        LEFT JOIN versions ON m.version = versions.rowid
                                     WHERE ids.id = ?
                                     ORDER BY versions.version DESC""", (p_id,))
        data = self.__cursor.fetchall()
        return [d[0] for d in data]

    def get_All_Packages_from_DB(self, search: str = "") -> list:
        query = """SELECT ids.id, names.name, IFNULL(norm_publishers.norm_publisher, '') AS norm_publisher, versions.version
                   FROM manifest AS m
                        LEFT JOIN ids ON m.id = ids.rowid
                        LEFT JOIN versions ON m.version = versions.rowid
                        LEFT JOIN names ON m.name = names.rowid
                        LEFT JOIN norm_publishers_map ON m.rowid = norm_publishers_map.manifest
                        LEFT JOIN norm_publishers ON norm_publishers_map.norm_publisher = norm_publishers.rowid"""

        if search:
            query += " WHERE names.name LIKE ? OR norm_publishers.norm_publisher LIKE ?"
            self.__cursor.execute(query, (f"%{search}%", f"%{search}%"))
        else:
            self.__cursor.execute(query)
        packages = self.__cursor.fetchall()
        return packages
