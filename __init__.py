bl_info = {
    "name": "Kanistra Client",
    "description": "",
    "author": "Kanistra Studio",
    "version": (0, 0, 1),
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

classes = [
    download_operator.DownloadAssetsOperator,
    asset_browser_panel.AssetBrowserPanel,
    open_kanistra_assets_operator.OpenKanistraAssetsOperator
]


# Register classes
def register():
    logger.prepare()
    logger.log("register")
    thumbnails.thumbnails_register()
    # bpy.context.report({"INFO"}, thumbnails.get_thumbnails())
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(open_kanistra_assets_operator.draw_operator)


def unregister():
    logger.log("unregister called")
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(open_kanistra_assets_operator.draw_operator)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    thumbnails.thumbnails_unregister()


if __name__ == "__main__":
    register()
