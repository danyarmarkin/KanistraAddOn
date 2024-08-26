import datetime
import subprocess

import bpy
from . import thumbnails, statusbar, filehash, version_control, server_config, util
from pathlib import Path
import requests
import os
import threading
import time


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

        self.downloading_thread = threading.Thread(target=util.download_from_source,
                                                   args=(self, context, f"{server_config.SERVER}/blendfiles/",
                                                         f"{server_config.SERVER}/download/", asset_lib.path,
                                                         "Downloaded", False))
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
                        icon_value=thumbnails.get_thumbnails()["arrow-down"].icon_id)
    elif props.updates < 0:
        layout.label(text='Updating...')
    else:
        layout.label(text='Library is up to date')
