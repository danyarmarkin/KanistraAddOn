import hashlib

import bpy
import threading
from . import download_assets_operator
import requests
import os
from . import filehash
import time


def check_updates(self, context):
    list_r = requests.get(f"{download_assets_operator.SERVER}/blendfiles/")
    if list_r.status_code != 200:
        return
    files = dict()

    for file in list_r.json():
        files[file['hash']] = file['size']

    asset_lib = download_assets_operator.get_asset_lib(context)
    for file in os.listdir(asset_lib.path):
        file_path = os.path.join(asset_lib.path, file)
        h = filehash.filehash(file_path)
        if h in files.keys():
            del files[h]

    self.updates = len(files)
    self.updates_size = sum(files.values())
    time.sleep(10)


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

    check_thread: threading.Thread = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if download_assets_operator.downloading_status(context) != 'NONE':
                self.updates = 0
                self.updates_size = 0
                return {'PASS_THROUGH'}
            if not self.check_thread.is_alive():
                self.check_thread.join()
                download_assets_operator.set_updates(context, self.updates, self.updates_size)
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
