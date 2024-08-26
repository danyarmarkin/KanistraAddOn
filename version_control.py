import os
from . import filehash, util
import json


def revalidate_versions_data(context, lib_path, admin):
    data = {'files': {}, 'version_tags': []}
    for fp, name in util.walk_in_asset_lib(lib_path):
        h = filehash.filehash(fp)
        data['files'][name] = h
    save_versions_data(context, data, admin)


def load_versions_data(context, admin=False):
    lib_path = util.get_asset_lib(context, "kanistra admin").path \
        if admin else util.get_asset_lib(context).path
    props = os.path.join(lib_path, ".props")
    path = os.path.join(props, "versions.json")

    if not os.path.exists(path):
        revalidate_versions_data(context, lib_path, admin)

    with open(path) as f:
        data = json.load(f)

    if 'files' not in data.keys() or 'version_tags' not in data.keys():
        revalidate_versions_data(context, lib_path, admin)
        with open(path) as f:
            data = json.load(f)

    # Check deletions
    files = list(map(util.SECOND, util.walk_in_asset_lib(lib_path)))
    save_flag = False
    keys = list(data['files'].keys())
    for f in keys:
        if f not in files:
            del data['files'][f]
            save_flag = True
    if save_flag:
        save_versions_data(context, data, admin)

    return data


def save_versions_data(context, data, admin=False):
    lib_path = util.get_asset_lib(context, "kanistra admin").path \
        if admin else util.get_asset_lib(context).path
    props = os.path.join(lib_path, ".props")
    path = os.path.join(props, "versions.json")

    if not os.path.exists(props):
        os.mkdir(props)
    with open(path, "w") as f:
        f.write(json.dumps(data))
