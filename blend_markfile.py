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
        for t in obj.asset_data.tags:
            if str(t.name).lower().startswith("published_at"):
                flag = False
                break
        if flag:
            obj.asset_data.tags.new(tag, skip_if_exists=True)
    elif action == "push":
        tags = []
        flag = True
        for t in obj.asset_data.tags:
            if str(t.name).lower().startswith("pulled_at") or str(t.name).lower().startswith("downloaded_at"):
                tags.append(t)
            if str(t.name).lower().startswith("published_at"):
                flag = False
        for t in tags:
            obj.asset_data.tags.remove(t)
        if flag:
            obj.asset_data.tags.new(tag, skip_if_exists=True)
    elif action == "publish":
        tags = []
        for t in obj.asset_data.tags:
            tn = str(t.name).lower()
            if tn.startswith("pulled_at") or tn.startswith("downloaded_at") or tn == "draft":
                tags.append(t)
        for t in tags:
            obj.asset_data.tags.remove(t)
        obj.asset_data.tags.new(tag, skip_if_exists=True)
    elif action == "draft_to_publish":
        tags = []
        for t in obj.asset_data.tags:
            tn = str(t.name).lower()
            if tn == "draft":
                tags.append(t)
        for t in tags:
            obj.asset_data.tags.remove(t)
        obj.asset_data.tags.new(tag, skip_if_exists=True)
    elif action == "manage":
        tags = []
        for t in obj.asset_data.tags:
            if t.name == tag:
                tags.append(t)
        if len(tags) == 0:
            obj.asset_data.tags.new(tag, skip_if_exists=True)
        else:
            for t in tags:
                obj.asset_data.tags.remove(t)


bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_mainfile(filepath=str(filepath), compress=True, relative_remap=False)
