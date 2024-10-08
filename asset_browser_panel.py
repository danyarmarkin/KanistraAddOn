import bpy
from . import thumbnails
from . import logger


class AssetBrowserPanel(bpy.types.Panel):
    bl_label = "Download Original"
    bl_idname = "kanistra.asset_browser_panel"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'

    @classmethod
    def poll(self, context):
        lib_ref = context.space_data.params.asset_library_reference
        props = context.window_manager.kanistra_props
        return lib_ref.lower() in ["kanistra admin"] and props.admin

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        try:
            row.operator("kanistra.download_asset",
                         icon_value=thumbnails.get_thumbnails()["download-icon"].icon_id)
        except Exception:
            row.operator("kanistra.download_asset")

        row.label(text="23.777 Mb")
