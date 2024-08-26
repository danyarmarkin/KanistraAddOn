import os
import threading
from pathlib import Path

import bpy
import json

from . import auth, server_config, download_assets_operator, statusbar, filehash, util, thumbnails


def get_lib_path(context):
    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name.lower() == "kanistra admin":
            return lib.path
    return None


def push_assets(self, context):
    files = dict()
    path = get_lib_path(context)
    for root, _, fls in os.walk(path):
        for file in fls:
            filepath = os.path.join(root, file)
            name = os.path.relpath(filepath, path).replace(os.path.sep, "/")
            h = filehash.filehash(filepath)
            files[h] = (filepath, name)

    list_r = auth.get(context, f"{server_config.SERVER}/admin-files/files/")
    if list_r.status_code != 200:
        return
    for file in list_r.json():
        if file['hash'] in files.keys() and file['name'] == files[file['hash']][1]:
            del files[file['hash']]
        else:
            auth.delete(context, f"{server_config.SERVER}/admin-files/files/{file['id']}")
    for _, (filepath, name) in files.items():
        with open(filepath, "rb") as f:
            files = {'file': f}
            data = {'name': name}
            auth.post(context, f"{server_config.SERVER}/admin-files/files/", files=files, data=data)


def publish_assets(self, context):
    list_r = auth.get(context, f"{server_config.SERVER}/blendfiles/")
    server_pks = []
    for i in list_r.json():
        server_pks.append(i['id'])

    path = get_lib_path(context)
    for root, _, fls in os.walk(path):
        for file in fls:
            filepath = os.path.join(root, file)
            name = os.path.relpath(filepath, path).replace(os.path.sep, "_")
            with open(filepath, "rb") as f:
                file_content = f.read()
                self.report({"INFO"}, f"[{file}] File size: {len(file_content)} bytes")
                f.seek(0)
                files = {'file': f}
                data = {'name': name, "is_free": False}
                r = auth.post(context, f"{server_config.SERVER}/blendfiles/", files=files, data=data)
                self.report({"INFO"}, f"[{file}] {r.status_code}: {r.text}")

    for pk in server_pks:
        auth.delete(context, f"{server_config.SERVER}/blendfiles/{pk}")


class OpenAdminOperator(bpy.types.Operator):
    bl_idname = "kanistra.open_admin_operator"
    bl_label = "Open Kanistra Admin"
    bl_description = "Switch asset library to Kanistra Admin"

    def execute(self, context):
        context.space_data.params.asset_library_reference = "Kanistra Admin"
        return {'FINISHED'}


class PushAdminOperator(bpy.types.Operator):
    bl_idname = "kanistra.push_admin_operator"
    bl_label = "Push"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        push_assets(self, context)
        return {"FINISHED"}


class PublishAdminOperator(bpy.types.Operator):
    bl_idname = "kanistra.publish_admin_operator"
    bl_label = "Publish"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        publish_assets(self, context)
        return {"FINISHED"}


class PullAdminOperator(bpy.types.Operator):
    bl_idname = "kanistra.pull_admin_operator"
    bl_label = "Pull"
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
                download_assets_operator.downloading_status(context, status='NONE')
                return {"FINISHED"}
        return {"PASS_THROUGH"}

    def execute(self, context):
        if download_assets_operator.downloading_status(context) != 'NONE':
            return {"FINISHED"}

        asset_lib = get_lib_path(context)
        self.downloading_thread = threading.Thread(target=util.download_from_source,
                                                   args=(self, context, f"{server_config.SERVER}/admin-files/files/",
                                                         f"{server_config.SERVER}/admin-files/download/", asset_lib,
                                                         "Pulled", True))
        self.downloading_thread.start()
        set_updates(context, 0)

        self.report({"INFO"}, f"Downloading from kanistra in background...")

        context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        download_assets_operator.downloading_status(context, status='DOWNLOADING')

        return {"RUNNING_MODAL"}


def draw_operators(self, context):
    lib_ref = context.space_data.params.asset_library_reference
    props = context.window_manager.kanistra_props
    if lib_ref.lower() == "Kanistra Assets".lower() and props.admin:
        layout = self.layout
        layout.operator("kanistra.open_admin_operator")
    if lib_ref.lower() == "Kanistra Admin".lower() and props.admin:
        layout = self.layout
        row = layout.row()
        if props.admin_updates != 0:
            row.operator("kanistra.pull_admin_operator", text=f"Pull {props.admin_updates} "
                                                              f"updates ({props.admin_updates_size // 1024 // 1024}"
                                                              f" Mb)",
                         icon_value=thumbnails.get_thumbnails()["arrow-down"].icon_id)
        row.operator("kanistra.push_admin_operator", icon_value=thumbnails.get_thumbnails()["arrow-up"].icon_id)
        row.operator("kanistra.publish_admin_operator", icon_value=thumbnails.get_thumbnails()["arrow-up-right"].icon_id)


def set_updates(context, u, us=0):
    context.window_manager.kanistra_props.admin_updates = u
    context.window_manager.kanistra_props.admin_updates_size = us
    for a in context.screen.areas:
        if a.type == "FILE_BROWSER":
            a.tag_redraw()


class UsersCountPanel(bpy.types.Panel):
    bl_idname = "kanistra.users_count_panel"
    bl_label = "Addon users"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        props = context.window_manager.kanistra_props
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        return context.area.ui_type == "ASSETS" and lib_ref.lower() in ["kanistra admin"] and props.admin

    def draw(self, context):
        layout = self.layout
        props = context.window_manager.kanistra_props
        col = layout.column()

        users = json.loads(props.admin_users)

        admin_users = sorted(list(filter(lambda x: x["is_staff"], users)), key=lambda u: u['email'])
        default_users = sorted(list(filter(lambda x: not x["is_staff"], users)), key=lambda u: u['email'])

        col.alert = True
        col.label(text=f"Admins ({len(admin_users)})")
        col.alert = False
        col.separator()

        for user in admin_users:
            col.label(text=user['email'])

        col.separator()
        col.alert = True
        col.label(text=f"Users ({len(default_users)})")
        col.alert = False
        col.separator()

        for user in default_users:
            col.label(text=f"{user['email']} {'(not active)' if not user['is_active'] else ''}")
