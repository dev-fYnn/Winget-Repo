import os
import sys


def delete_File(file_name: str, file_path: str = fr"{sys.path[0]}\Files"):
    if os.path.exists(path := (os.path.join(file_path, file_name))):
        os.remove(path)
