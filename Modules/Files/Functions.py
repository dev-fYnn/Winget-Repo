import os

from settings import PATH_FILES


def delete_File(file_name: str, file_path: str = PATH_FILES):
    if os.path.exists(path := (os.path.join(file_path, file_name))):
        os.remove(path)
