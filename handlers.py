import bpy
from . import util

from bpy.app.handlers import persistent

@persistent
def save_post_handler(filename):
    filename = str(filename)
    lib_path = util.get_asset_lib(bpy.context, "kanistra admin").path
    if filename.startswith(lib_path):
        util.mark_file_with_tag(bpy.context, filename, "draft", "draft")
        bpy.ops.wm.open_mainfile(filepath=filename)


@persistent
def save_pre_handler(filename):
    filename = str(filename)
    lib_path = util.get_asset_lib(bpy.context, "kanistra admin").path
    if not filename.startswith(lib_path):
        return

    data = bpy.data
    for obj in list(data.objects) + list(data.collections) + list(data.materials):
        if not obj.asset_data:
            continue
        flag = True
        for tag in obj.asset_data.tags:
            if str(tag.name).lower().startswith("published_at"):
                flag = False
                break
        if flag:
            obj.asset_data.tags.new("draft", skip_if_exists=True)


def register_handlers():
    # bpy.app.handlers.save_post.append(save_post_handler)
    bpy.app.handlers.save_pre.append(save_pre_handler)


def unregister_handlers():
    # bpy.app.handlers.save_post.remove(save_post_handler)
    bpy.app.handlers.save_pre.remove(save_pre_handler)
