import hashlib
import json

import bpy
import threading
import requests
import os
from . import filehash, version_control, download_assets_operator, auth, admin, server_config
import time


def check_updates(self, context):
    if self.is_first_update:
        time.sleep(2)
        self.is_first_update = False
    else:
        time.sleep(30)

    auth.check_admin(context)

    list_r = requests.get(f"{server_config.SERVER}/blendfiles/")
    if list_r.status_code != 200:
        return
    files = dict()

    for file in list_r.json():
        files[file['hash']] = file['size']

    local_data = version_control.load_versions_data(context)
    for h in local_data['files'].values():
        if h in files.keys():
            del files[h]

    self.updates = len(files)
    self.updates_size = sum(files.values())

    props = context.window_manager.kanistra_props
    if props.admin:
        list_r = auth.get(context, f"{server_config.SERVER}/admin-files/files/")
        if list_r.status_code != 200:
            return
        files = dict()

        for file in list_r.json():
            files[file['hash']] = file['size']

        path = admin.get_lib_path(context)
        for root, dirs, fls in os.walk(path):
            for file in fls:
                filepath = os.path.join(root, file)
                h = filehash.filehash(filepath)
                if h in files.keys():
                    del files[h]
        self.admin_updates = len(files)
        self.admin_updates_size = sum(files.values())

        list_r = auth.get(context, f"{server_config.SERVER}/admin-data/users/")
        if list_r.status_code == 200:
            props.admin_users = str(json.dumps(list_r.json()))
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
    _interval = 10

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
                return {'PASS_THROUGH'}
            if not self.check_thread.is_alive():
                self.check_thread.join()
                download_assets_operator.set_updates(context, self.updates, self.updates_size)
                admin.set_updates(context, self.admin_updates, self.admin_updates_size)
                run_check(self, context)
        return {'PASS_THROUGH'}

    def execute(self, context):
        # if CheckUpdatesOperator.updating:
        #     return {"FINISHED"}
        #
        # CheckUpdatesOperator.updating = True
        run_check(self, context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(self._interval, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


from bpy.app.handlers import persistent


@persistent
def load_check_handler(dummy):
    bpy.ops.kanistra.check_updates_operator()
