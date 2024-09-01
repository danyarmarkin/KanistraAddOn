import hashlib
import json

import bpy
import threading
import requests
import os
from . import filehash, version_control, download_assets_operator, auth, admin, server_config


def check_group_update(cls, context, source: str, admin: bool):
    props = context.window_manager.kanistra_props
    authenticated = props.authenticated
    if not authenticated and admin or admin and not props.admin:
        return

    if authenticated:
        source_list_response = auth.get(context, source)
    else:
        source_list_response = requests.get(source)
    if source_list_response.status_code != 200:
        return

    source_files = dict()
    for file in source_list_response.json():
        source_files[file['hash']] = file['size']

    local_data = version_control.load_versions_data(context, admin)
    for h in local_data['files'].values():
        if h in source_files.keys():
            del source_files[h]

    if admin:
        cls.admin_updates = len(source_files)
        cls.admin_updates_size = sum(source_files.values())
    else:
        cls.updates = len(source_files)
        cls.updates_size = sum(source_files.values())


def check_updates(self, context):
    auth.check_admin(context)
    props = context.window_manager.kanistra_props

    check_group_update(self, context, f"{server_config.SERVER}/blendfiles/", False)
    if props.admin:
        check_group_update(self, context, f"{server_config.SERVER}/admin-files/files/", True)

        users_data_response = auth.get(context, f"{server_config.SERVER}/admin-data/users/")
        if users_data_response.status_code == 200:
            props.admin_users = str(json.dumps(users_data_response.json()))
    else:
        props.admin_users = '[]'
        self.admin_updates = 0
        self.admin_updates_size = 0


def run_check(self, context):
    self.check_thread = threading.Thread(target=check_updates, args=(self, context))
    self.check_thread.start()


class CheckUpdatesOperator(bpy.types.Operator):
    bl_idname = "kanistra.check_updates_operator"
    bl_label = "Check Updates Operator"

    updating = False

    _timer = None
    _interval = 3

    updates = 0
    updates_size = 0

    admin_updates = 0
    admin_updates_size = 0

    is_first_update = True

    check_thread: threading.Thread = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if download_assets_operator.downloading_status(context) != 'NONE':
                self.updates = 0
                self.updates_size = 0
                self.admin_updates = 0
                self.admin_updates_size = 0
                return {'FINISHED'}
            if not self.check_thread.is_alive():
                self.check_thread.join()
                download_assets_operator.set_updates(context, self.updates, self.updates_size)
                admin.set_updates(context, self.admin_updates, self.admin_updates_size)
                return {'FINISHED'}
        return {"PASS_THROUGH"}

    def execute(self, context):
        run_check(self, context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(self._interval, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
