import os
import sys


def delete_File(file_name: str):
    if os.path.exists(path := (os.path.join(fr"{sys.path[0]}\Files", file_name))):
        os.remove(path)
