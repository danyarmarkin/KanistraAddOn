import hashlib

import bpy
from . import thumbnails, statusbar
from pathlib import Path
import shutil
import requests
import os
import pathlib
import threading
import time
from . import filehash

SERVER = "http://95.164.68.38"


def get_asset_lib(context):
    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name.lower() == "kanistra assets":
            return lib
    return None


def abspath(p):
    return Path(bpy.path.abspath(p)).resolve()


def set_updates(context, u, us=0):
    context.window_manager.kanistra_props.updates = u
    context.window_manager.kanistra_props.updates_size = us
    for a in context.screen.areas:
        if a.type == "FILE_BROWSER":
            a.tag_redraw()


def downloading_status(context, status=None):
    props = context.window_manager.kanistra_props
    if not status:
        return props.download_status
    props.download_status = status


def download_assets(self, context, asset_lib):
    # shutil.rmtree(asset_lib.path)
    # os.makedirs(asset_lib.path)
    list_r = requests.get(f"{SERVER}/blendfiles/")
    if list_r.status_code != 200:
        self.report(
            {"ERROR"},
            "Server didn't send response"
        )
        return
    files = dict()

    for file in list_r.json():
        pk = file['id']
        h = file['hash']
        name = file['name']
        size = file['size']
        files[name] = (h, pk, size)

    for file in os.listdir(asset_lib.path):
        file_path = os.path.join(asset_lib.path, file)
        h = filehash.filehash(file_path)
        if file not in files.keys():
            os.remove(file_path)
            continue
        if files[file][0] == h:
            del files[file]

    self.total_size = sum([i[2] for i in files.values()])
    self.downloaded_size = 0
    block_size = 1024 * 16  # 16 kB

    if len(files) == 0:
        self.report(
            {"INFO"},
            f"Library is up to date"
        )

    for file, (_, pk, _) in files.items():
        file_r = requests.get(f"{SERVER}/download/{pk}/", stream=True)
        file_path = os.path.join(asset_lib.path, file)
        self.filename = file

        if file_r.status_code != 200:
            self.report(
                {"ERROR"},
                "Server doesn't send files"
            )
            return

        f = open(file_path, 'wb')
        for data in file_r.iter_content(block_size):
            if downloading_status(context) != 'DOWNLOADING':
                f.close()
                os.remove(f.name)
                return
            self.downloaded_size += len(data)
            f.write(data)
            # time.sleep(0.001)


class DownloadKanistraAssetsOperator(bpy.types.Operator):
    bl_idname = "kanistra.download_kanistra_assets"
    bl_label = "Update Kanistra Assets"
    bl_description = "Download Kanistra Assets"
    bl_options = {"REGISTER", "UNDO"}

    downloading_thread: threading.Thread = None
    total_size = 1
    downloaded_size = 0
    filename = None

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def modal(self, context, event):
        if event.type == "TIMER":
            if self.total_size > 0:
                statusbar.update_progress(context, self.downloaded_size / self.total_size * 100, f"{self.filename}")

            if not self.downloading_thread.is_alive():
                self.downloading_thread.join()
                try:
                    bpy.ops.asset.library_refresh()
                except RuntimeError:
                    pass
                statusbar.end_progress(context)
                set_updates(context, 0)
                downloading_status(context, status='NONE')
                return {"FINISHED"}
        return {"PASS_THROUGH"}

    def execute(self, context):
        asset_lib = get_asset_lib(context)
        if asset_lib is None:
            self.report(
                {"ERROR"},
                'First open Preferences > File Paths and create an asset library named "Kanistra Assets"',
            )
            return {"CANCELLED"}
        if not abspath(asset_lib.path).exists():
            self.report(
                {"ERROR"},
                "Asset library path not found! Please check the folder still exists",
            )
            return {"CANCELLED"}

        if downloading_status(context) != 'NONE':
            return {"FINISHED"}

        self.downloading_thread = threading.Thread(target=download_assets, args=(self, context, asset_lib))
        self.downloading_thread.start()
        set_updates(context, -1)

        self.report({"INFO"}, f"Downloading from kanistra in background...")

        context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        downloading_status(context, status='DOWNLOADING')

        return {"RUNNING_MODAL"}


class CancelDownloadingOperator(bpy.types.Operator):
    bl_idname = "kanistra.cancel_download_kanistra_assets"
    bl_label = "Cancel downloading Kanistra"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        downloading_status(context, status='CANCEL')
        return {"FINISHED"}


def draw_operator(self, context):
    lib_ref = context.space_data.params.asset_library_reference
    if lib_ref.lower() != "Kanistra Assets".lower():
        return
    layout = self.layout
    props = context.window_manager.kanistra_props
    if props.updates > 0:
        layout.operator("kanistra.download_kanistra_assets",
                        text=f"Download {props.updates} update{'' if props.updates == 1 else 's'}"
                             f" ({props.updates_size // (1024 * 1024)} Mb)",
                        icon_value=thumbnails.get_thumbnails()["download-icon"].icon_id)
    elif props.updates < 0:
        layout.label(text='Updating...')
    else:
        layout.label(text='Library is up to date')

