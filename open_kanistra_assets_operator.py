import bpy
from . import thumbnails


class OpenKanistraAssetsOperator(bpy.types.Operator):
    bl_idname = "kanistra.open_kanistra_assets"
    bl_label = "Open Kanistra Assets"
    bl_description = "Switch asset library to Kanistra"

    def execute(self, context):
        context.space_data.params.asset_library_reference = "Kanistra Assets"
        return {'FINISHED'}


def draw_operator(self, context):
    lib_ref = context.space_data.params.asset_library_reference
    if lib_ref.lower() == "Kanistra Assets".lower():
        return
    if lib_ref.lower() != "All".lower():
        return
    layout = self.layout
    layout.operator("kanistra.open_kanistra_assets", icon_value=thumbnails.get_thumbnails()["kanistra"].icon_id)
