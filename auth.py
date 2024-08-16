import os
from pathlib import Path

import requests
from . import server_config
import json


def save_auth_props(context):
    props = context.window_manager.kanistra_props
    data = {
        "login": props.login,
        "refresh_token": props.refresh_token,
    }
    auth_folder_path = Path(__file__).parents[0] / "auth"
    if not os.path.exists(auth_folder_path):
        os.mkdir(auth_folder_path)
    with open(auth_folder_path / "auth.json", "w") as f:
        f.write(json.dumps(data))


def load_auth_props(context):
    auth_path = Path(__file__).parents[0] / "auth" / "auth.json"
    if not os.path.exists(auth_path):
        return False
    props = context.window_manager.kanistra_props
    with open(auth_path, "r") as f:
        data = json.loads(f.read())
        props.login = data["login"]
        props.refresh_token = data["refresh_token"]
    return True


def log_up(context):
    props = context.window_manager.kanistra_props
    if str(props.login).count("@") != 1:
        return "ERROR", "Invalid email"
    if len(props.password) < 6:
        return "ERROR", "Password length must be at least 8 characters"
    if props.password != props.password_again:
        return "ERROR", "Passwords don't match!"
    if not props.license_agreement:
        return "ERROR", "Registration is not possible without agreeing to the addon policy"
    data = {
        "email": props.login,
        "password": props.password,
        "notify": bool(props.email_sends_agreement)
    }

    r = requests.post(f"{server_config.SERVER}/register/", json=data)
    if r.status_code != 201:
        return "ERROR", r.text
    props.password = ""
    props.password_again = ""
    props.need_activation = True
    return "INFO", "A confirmation code has been sent to your email"


def activate_account(context):
    props = context.window_manager.kanistra_props
    data = {
        "email": props.login,
        "code": props.register_code
    }

    r = requests.post(f"{server_config.SERVER}/activate/", json=data)
    if r.status_code != 200:
        return "ERROR", r.text

    props.need_activation = False
    props.login_or_logup = False
    return "INFO", "Your email has been successfully verified"


def log_out(context):
    props = context.window_manager.kanistra_props
    props.access_token = "token"
    props.refresh_token = "token"
    props.admin = False
    save_auth_props(context)
    props.authenticated = False


def delete_account(context):
    r = delete(context, f"{server_config.SERVER}/delete-account/")
    if r.status_code != 200:
        return "ERROR", "Error while deleting account"
    log_out(context)
    return "INFO", "Account deleted successfully"


def check_admin(context):
    r = get(context, f"{server_config.SERVER}/is-admin/")
    if r.status_code != 200:
        return
    props = context.window_manager.kanistra_props
    props.admin = r.json()['is_admin']


def authenticate(context):
    props = context.window_manager.kanistra_props
    r = requests.post(f"{server_config.SERVER}/api/token/", json={"username": props.login, "password": props.password})
    if r.status_code == 200:
        props.authenticated = True
        props.access_token = r.json()["access"]
        props.refresh_token = r.json()["refresh"]
        props.password = ""
        save_auth_props(context)
        check_admin(context)
        return "INFO", "Logged in successfully"
    if r.status_code == 401:
        props.authenticated = False
        props.admin = False
        return "ERROR", "Incorrect username or password"
    return "ERROR", f"{r.status_code}: {r.text}"


def refresh(context):
    props = context.window_manager.kanistra_props
    r = requests.post(f"{server_config.SERVER}/api/token/refresh/", json={"refresh": props.refresh_token})
    if r.status_code == 401:
        props.authenticated = False
        props.admin = False
        return False
    if r.status_code != 200:
        return False
    props.refresh_token = r.json()["refresh"]
    props.access_token = r.json()["access"]
    props.authenticated = True
    save_auth_props(context)
    check_admin(context)
    return True


def get_authorization_header(context):
    props = context.window_manager.kanistra_props
    return f"JWT {props.access_token}"


def request(method, context, retry, *args, **kwargs):
    if "headers" not in kwargs:
        kwargs['headers'] = {}
    kwargs['headers']['Authorization'] = get_authorization_header(context)
    r = method(*args, **kwargs)
    if r.status_code == 401:
        if not retry and refresh(context):
            return request(method, context, True, *args, **kwargs)
    return r


def get(context, *args, **kwargs):
    return request(requests.get, context, False, *args, **kwargs)


def put(context, *args, **kwargs):
    return request(requests.put, context, False, *args, **kwargs)


def post(context, *args, **kwargs):
    return request(requests.post, context, False, *args, **kwargs)


def delete(context, *args, **kwargs):
    return request(requests.delete, context, False, *args, **kwargs)


def patch(context, *args, **kwargs):
    return request(requests.patch, context, False, *args, **kwargs)


import bpy
from bpy.app.handlers import persistent


@persistent
def load_auth_handler(dummy):
    context = bpy.context
    if load_auth_props(context):
        refresh(context)
