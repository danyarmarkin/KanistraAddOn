import bpy

from . import thumbnails, addon_updater_ops


class KanistraLinksPanel(bpy.types.Panel):
    bl_label = "Kanistra Studio"
    bl_idname = "kanistra.links_panel"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(self, context):
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        return context.area.ui_type == "ASSETS" and lib_ref.lower() == "kanistra assets"

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        addon_updater_ops.update_notice_box_ui(self, column)

        column.operator(
            "wm.url_open", text="Join our Discord", icon_value=thumbnails.get_thumbnails()["discord-logo"].icon_id
        ).url = "https://discord.gg/XDFgEyQbTt"


