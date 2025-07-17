import time

from Modules.Winget.Functions import write_log


def log_flusher(app, interval: int=60):
    with app.app_context():
        while True:
            time.sleep(interval)
            buffer = app.config.get('active_downloads', [])
            if buffer:
                entries_to_write = buffer.copy()
                app.config['active_downloads'].clear()
                for ip, file in entries_to_write:
                    write_log(ip, file, entries_to_write[(ip, file)])
