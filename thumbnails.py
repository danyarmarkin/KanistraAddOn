import bpy
import bpy.utils.previews
import os
from . import logger

preview_collections = {}


def load_recursive(collection, directory, additional=""):
    for f in os.listdir(directory):
        print(f)
        path = os.path.join(directory, f)
        if f.endswith(".png"):
            collection.load(
                additional + f.split(".")[0],
                path,
                "IMAGE",
            )
        if os.path.isdir(path):
            load_recursive(collection, path, f"{additional}{f}_")


def thumbnails_register():
    icons_dir = os.path.join(os.path.dirname(__file__), "thumbnails")
    custom_icons = bpy.utils.previews.new()
    load_recursive(custom_icons, icons_dir)
    preview_collections["thumbnails"] = custom_icons


def thumbnails_unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


def get_thumbnails():
    return preview_collections["thumbnails"]
