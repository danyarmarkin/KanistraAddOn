import bpy
import os
from . import filehash
import json


def get_asset_lib(context):
    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name.lower() == "kanistra assets":
            return lib
    return None


def revalidate_versions_data(context, lib_path):
    data = {'files': {}, 'version_tags': []}
    for file in os.listdir(lib_path):
        if file.startswith('.'):
            continue
        h = filehash.filehash(os.path.join(lib_path, file))
        data['files'][file] = h
    save_versions_data(context, data)


def load_versions_data(context):
    lib_path = get_asset_lib(context).path
    props = os.path.join(lib_path, ".props")
    path = os.path.join(props, "versions.json")

    if not os.path.exists(path):
        revalidate_versions_data(context, lib_path)

    with open(path) as f:
        data = json.load(f)

    if 'files' not in data.keys() or 'version_tags' not in data.keys():
        revalidate_versions_data(context, lib_path)
        with open(path) as f:
            data = json.load(f)

    # Check deletions
    files = os.listdir(lib_path)
    save_flag = False
    keys = list(data['files'].keys())
    for f in keys:
        if f not in files:
            del data['files'][f]
            save_flag = True
    if save_flag:
        save_versions_data(context, data)

    return data


def save_versions_data(context, data):
    lib_path = get_asset_lib(context).path
    props = os.path.join(lib_path, ".props")
    path = os.path.join(props, "versions.json")

    if not os.path.exists(props):
        os.mkdir(props)
    with open(path, "w") as f:
        f.write(json.dumps(data))
