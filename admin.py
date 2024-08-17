import os
import threading
from pathlib import Path

import bpy

from . import auth, server_config, download_assets_operator, statusbar, filehash


def get_lib_path(context):
    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name.lower() == "kanistra admin":
            return lib.path
    return None


def download_assets(self, context):
    list_r = auth.get(context, f"{server_config.SERVER}/admin-files/files/")
    if list_r.status_code != 200:
        return
    files = dict()

    for file in list_r.json():
        pk = file['id']
        h = file['hash']
        name = file['name']
        size = file['size']
        files[h] = (name, pk, size)

    path = get_lib_path(context)
    for root, _, fls in os.walk(path):
        for file in fls:
            filepath = os.path.join(root, file)
            h = filehash.filehash(filepath)
            if h in files.keys():
                name = files[h][0]
                if name == os.path.relpath(filepath, path).replace(os.path.sep, "/"):
                    del files[h]
                    continue
            os.remove(filepath)

    self.total_size = sum([i[2] for i in files.values()])

    self.downloaded_size = 0
    block_size = 1024 * 16  # 16 kB

    for h, (name, pk, _) in files.items():
        file_r = auth.get(context, f"{server_config.SERVER}/admin-files/download/{pk}/", stream=True)
        file_path = Path(path)
        for i in name.split("/"):
            file_path /= i

        if not os.path.exists(file_path.parents[0]):
            os.makedirs(file_path.parents[0])
        self.filename = file_path.name

        if file_r.status_code != 200:
            return

        with open(file_path, 'wb') as f:
            for data in file_r.iter_content(block_size):
                if download_assets_operator.downloading_status(context) != 'DOWNLOADING':
                    f.close()
                    os.remove(f.name)
                    return
                self.downloaded_size += len(data)
                f.write(data)

    for root, dirs, fls in os.walk(path):
        if len(dirs) + len(fls) == 0:
            os.remove(root)


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

        self.downloading_thread = threading.Thread(target=download_assets, args=(self, context))
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
                                                              f" Mb)")
        row.operator("kanistra.push_admin_operator")
        row.operator("kanistra.publish_admin_operator")


def set_updates(context, u, us=0):
    context.window_manager.kanistra_props.admin_updates = u
    context.window_manager.kanistra_props.admin_updates_size = us
    for a in context.screen.areas:
        if a.type == "FILE_BROWSER":
            a.tag_redraw()
