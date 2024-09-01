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
        props = context.window_manager.kanistra_props
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        return context.area.ui_type == "ASSETS" and (lib_ref.lower() == "kanistra assets" or
                                                     lib_ref.lower() == "kanistra admin" and props.admin)

    def draw(self, context):
        props = context.window_manager.kanistra_props
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        admin = lib_ref.lower() == "kanistra admin" and props.admin

        layout = self.layout
        box = layout.box()
        col = box.column(align=True)

        if admin:
            col.operator("kanistra.admin_index_operator")
            col.separator()

        row = col.row()
        row.label(
            text="History:",
            icon_value=thumbnails.get_thumbnails()["recently"].icon_id
        )

        if context.space_data.params.filter_search:
            row.operator("kanistra.search_tag_operator", text="Clear Search", icon="PANEL_CLOSE").tag = ""

        data = version_control.load_versions_data(context, admin=admin)["version_tags"]
        tags = list(reversed(data))[:10] if (len(data) > 10 and not
                                             context.window_manager.kanistra_props.show_more_history)\
            else list(reversed(data))

        if admin:
            row = col.row(align=True)
            row.alignment = "RIGHT"
            c = row.column()
            c.alert = True
            c.operator(
                "kanistra.search_tag_operator",
                text="Draft →").tag = "draft"
            c.alert = False
            c.operator(
                "kanistra.search_tag_operator",
                text="Free →").tag = "free"
            col.separator()
        is_first = True
        for tag in tags:
            row = col.row(align=True)
            comps = tag.split("_")
            row.alignment = "LEFT"
            if len(comps) < 4:
                name = tag
            else:
                name = f"{comps[2]} {comps[3]}"
            if is_first and not admin:
                row.label(
                    text="",
                    icon_value=thumbnails.get_thumbnails()["new"].icon_id
                )
            if comps[0].lower() == "pulled" and admin:
                row.label(
                    text="",
                    icon_value=thumbnails.get_thumbnails()["arrow-down"].icon_id
                )
            if comps[0].lower() == "published" and admin:
                row.label(
                    text="",
                    icon_value=thumbnails.get_thumbnails()["arrow-up-right"].icon_id
                )
            row.alignment = "RIGHT"
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
