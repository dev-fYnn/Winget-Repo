import random
import string


def generate_random_string(length: int) -> string:
    letters = string.ascii_letters
    random_string = ''.join(random.choice(letters) for _ in range(length))
    return random_string


def select_to_dict(data: list, header_data: tuple) -> list:
    if len(data) > 0:
        header = []
        for item in header_data:
            header.extend(value for value in item if value is not None)
        data = [dict(zip(header, d)) for d in data]
        return data
    return []
