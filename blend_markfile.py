import bpy
import sys

argv = sys.argv
argv = argv[argv.index("--") + 1:]

if len(argv) == 2:
    filepath, tag = argv
    action = "add"
if len(argv) == 3:
    filepath, tag, action = argv
else:
    exit(0)

for obj in list(bpy.data.objects) + list(bpy.data.collections) + list(bpy.data.materials):
    if not obj.asset_data:
        continue
    if action == "add":
        obj.asset_data.tags.new(tag, skip_if_exists=True)
    elif action == "del":
        obj.asset_data.tags.remove(tag)
    elif action == "draft":
        flag = True
        for tag in obj.asset_data.tags:
            if str(tag).lower().startswith("published_at"):
                flag = False
                break
        if flag:
            obj.asset_data.tags.new(tag, skip_if_exists=True)


bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile(filepath=str(filepath), compress=True, relative_remap=False)
