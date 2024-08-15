import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:]

filepath, tag = argv

for obj in list(bpy.data.objects) + list(bpy.data.collections) + list(bpy.data.materials):
    if not obj.asset_data:
        continue
    obj.asset_data.tags.new(tag, skip_if_exists=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile(filepath=str(filepath), compress=True, relative_remap=False)
