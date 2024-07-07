import bpy
import os
from . import logger

preview_collections = {}


def thumbnails_register():
    icons_dir = os.path.join(os.path.dirname(__file__), "thumbnails")
    custom_icons = bpy.utils.previews.new()
    logger.log(f"dir = {icons_dir}")
    for f in os.listdir(icons_dir):
        logger.log(f"file = {f}")
        if f.endswith(".png"):
            custom_icons.load(
                f.split(".")[0],
                os.path.join(icons_dir, f),
                "IMAGE",
            )
            print(os.path.splitext(os.path.basename(f''))[0])
    preview_collections["thumbnails"] = custom_icons


def thumbnails_unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


def get_thumbnails():
    return preview_collections["thumbnails"]
