import json
import os
import importlib
import sys

from functools import wraps
from flask import current_app, request, session, flash, redirect, url_for
from starlette.middleware.cors import CORSMiddleware

from Modules.Database.Database import SQLiteDatabase
from settings import PATH_PLUGINS


def load_plugins(current_app, fast_api):
    if not os.path.exists(PATH_PLUGINS):
        return

    current_app.config['ACTIV_PLUGINS'] = []
    current_app.config['PLUGIN_PERMISSIONS'] = {}
    current_app.config['ALL_PLUGIN_PERMISSIONS'] = []

    base_dir = os.path.dirname(os.path.abspath(PATH_PLUGINS))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    plugins_dirname = os.path.basename(os.path.abspath(PATH_PLUGINS))

    for folder in os.listdir(PATH_PLUGINS):
        folder_path = os.path.join(PATH_PLUGINS, folder)

        if os.path.isdir(folder_path) and not folder.startswith('__'):
            try:
                module = importlib.import_module(f"{plugins_dirname}.{folder}")
                if hasattr(module, 'PLUGIN_METADATA'):
                    metadata = module.PLUGIN_METADATA
                    url_prefix = f"/ui/{folder.lower()}"
                    metadata['url'] = url_prefix + "/"

                    current_app.register_blueprint(metadata['blueprint'], url_prefix=url_prefix)
                    current_app.config['ACTIV_PLUGINS'].append(metadata)

                    for mount_path, asgi_app in metadata.get('fastapi_mounts', []):
                        cors_config = metadata.get('fastapi_config', {
                            "allow_origins": ["*"],
                            "allow_methods": ["GET"],
                            "allow_headers": ["Content-Type", "Accept", "Authorization", "Cache-Control"]})
                        wrapped = CORSMiddleware(app=asgi_app, **cors_config)
                        fast_api.mount(mount_path, wrapped)

                    if 'permissions' in metadata:
                        current_app.config['ALL_PLUGIN_PERMISSIONS'].extend(metadata['permissions'])

                    perm_path = os.path.join(folder_path, "permissions.json")
                    if os.path.exists(perm_path) and os.path.getsize(perm_path) > 0:
                        with open(perm_path, "r", encoding="utf-8") as f:
                            try:
                                plugin_perms = json.load(f)
                                for role, endpoints in plugin_perms.items():
                                    if role not in current_app.config['PLUGIN_PERMISSIONS']:
                                        current_app.config['PLUGIN_PERMISSIONS'][role] = []
                                    current_app.config['PLUGIN_PERMISSIONS'][role].extend(endpoints)
                            except json.JSONDecodeError:
                                pass
            except Exception as e:
                print(f"Error loading Plugin: '{folder}': {e}")


def plugin_authenticate(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        endpoint = request.endpoint
        all_plugin_endpoints = current_app.config.get('ALL_PLUGIN_PERMISSIONS', [])
        if endpoint in all_plugin_endpoints:
            with SQLiteDatabase() as db:
                u_data = db.get_User_by_ID(session.get('logged_in', ''))

            plugin_permissions = current_app.config.get('PLUGIN_PERMISSIONS', {})
            allowed_endpoints = plugin_permissions.get(u_data['GROUP'], [])
            if endpoint in allowed_endpoints:
                return f(*args, **kwargs)
        flash("Missing permissions!", "error")
        return redirect(url_for("ui_bp.index"))
    return decorator
