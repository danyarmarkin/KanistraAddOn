import bpy
import pathlib
from . import thumbnails, version_control


class DownloadHistoryPanel(bpy.types.Panel):
    bl_label = "Kanistra Studio"
    bl_idname = "kanistra.download_history_panel"
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
        box = layout.box()
        col = box.column(align=True)
        row = col.row()
        row.label(
            text="History:",
            icon_value=thumbnails.get_thumbnails()["recently"].icon_id
        )
        data = version_control.load_versions_data(context)["version_tags"]
        tags = list(reversed(data))[:10] if (len(data) > 10 and not
                                             context.window_manager.kanistra_props.show_more_history)\
            else list(reversed(data))

        is_first = True
        for tag in tags:
            row = col.row(align=True)
            row.alignment = "RIGHT"
            comps = tag.split("_")
            if len(comps) < 4:
                name = tag
            else:
                name = f"{comps[2]} {comps[3]}"
            if is_first:
                row.label(
                    text="",
                    icon_value=thumbnails.get_thumbnails()["new"].icon_id
                )
            row.operator(
                "kanistra.search_tag_operator",
                text=f"{name} →",
                emboss=False).tag = tag
            is_first = False
        if len(data) > 10:
            col.prop(
                context.window_manager.kanistra_props,
                "show_more_history",
                text="",
                icon="TRIA_UP" if context.window_manager.kanistra_props.show_more_history else "TRIA_DOWN",
            )
        layout.separator()
