bl_info = {
    "name": "Kanistra Client",
    "description": "",
    "author": "Kanistra Studio",
    "version": (0, 0, 2),
    "blender": (4, 0, 0),
    "category": "Import-Export",
}


if "bpy" not in locals():
    from . import asset_browser_panel
    from . import download_operator
    from . import open_kanistra_assets_operator
    from . import thumbnails
    from . import logger
    from . import addon_updater_ops
else:
    from importlib import reload
    reload(asset_browser_panel)
    reload(download_operator)
    reload(open_kanistra_assets_operator)
    reload(thumbnails)
    reload(logger)
    reload(addon_updater_ops)

import bpy

@addon_updater_ops.make_annotations
class AddOnPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    auto_check_update = bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=True,
    )

    updater_interval_months = bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_interval_days = bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=7,
        min=0,
    )
    updater_interval_hours = bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_interval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=0,
        min=0,
        max=59
    )

    def draw(self, context):
        addon_updater_ops.update_settings_ui(self, context)


classes = [
    AddOnPreferences,
    download_operator.DownloadAssetsOperator,
    asset_browser_panel.AssetBrowserPanel,
    open_kanistra_assets_operator.OpenKanistraAssetsOperator
]


# Register classes
def register():
    logger.prepare()
    logger.log("register")
    addon_updater_ops.register(bl_info)
    thumbnails.thumbnails_register()
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(open_kanistra_assets_operator.draw_operator)


def unregister():
    logger.log("unregister called")
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(open_kanistra_assets_operator.draw_operator)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    thumbnails.thumbnails_unregister()
    addon_updater_ops.unregister()


if __name__ == "__main__":
    register()
