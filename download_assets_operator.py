import bpy
from . import thumbnails
from pathlib import Path
import shutil
import requests
import os


def get_asset_lib(context):
    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name.lower() == "kanistra assets":
            return lib
    return None


def abspath(p):
    return Path(bpy.path.abspath(p)).resolve()


class DownloadKanistraAssetsOperator(bpy.types.Operator):
    bl_idname = "kanistra.download_kanistra_assets"
    bl_label = "Download Kanistra Assets"
    bl_description = "Download Kanistra Assets"

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

        shutil.rmtree(asset_lib.path)
        os.makedirs(asset_lib.path)
        list_r = requests.get("http://95.164.68.38:8000/blendfiles/")
        if list_r.status_code != 200:
            self.report(
                {"ERROR"},
                "Server doesnt request",
            )
            return {"CANCELLED"}

        for file in list_r.json():
            pk = file['id']
            filename = file['file'].split('/')[-1]
            file_r = requests.post(f"http://95.164.68.38:8000/download/{pk}/")
            if file_r.status_code != 200:
                self.report(
                    {"ERROR"},
                    f"Cant download file {filename}",
                )
                return {"CANCELLED"}
            with open(os.path.join(asset_lib.path, filename), 'wb') as f:
                f.write(file_r.content)
                f.close()

        return {'FINISHED'}


def draw_operator(self, context):
    lib_ref = context.space_data.params.asset_library_reference
    if lib_ref.lower() != "Kanistra Assets".lower():
        return
    layout = self.layout
    layout.operator("kanistra.download_kanistra_assets", icon_value=thumbnails.get_thumbnails()["download-icon"].icon_id)
