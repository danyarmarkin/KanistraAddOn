import subprocess
from datetime import datetime
from pathlib import Path
import os
import requests

from . import auth, version_control, server_config, filehash, admin
import shutil

import bpy


def get_asset_lib(context, name="kanistra assets"):
    for lib in context.preferences.filepaths.asset_libraries:
        if lib.name.lower() == name:
            return lib
    return None


def mark_file_with_tag(context, file, tag, *args):
    script_path = Path(__file__).parents[0] / "blend_markfile.py"
    subprocess.call([
        bpy.app.binary_path, "--background",
        file, "--factory-startup",
        "--python", script_path,
        "--", file, tag, *args
    ])


def walk_in_asset_lib(lib_path) -> (str, str):
    for root, _, fls in os.walk(lib_path):
        for file in fls:
            filepath = os.path.join(root, file)
            if not (filepath.endswith('.blend') or filepath.endswith(".txt")):
                continue
            yield filepath, os.path.relpath(filepath, lib_path).replace(os.path.sep, "/")


FIRST = lambda x: x[0]
SECOND = lambda x: x[1]


def create_tag(tag):
    current_time = datetime.now()

    def formated(n, c=2):
        return "0" * max(0, c - len(str(n))) + str(n)

    return (f"{tag}_at_"
            f"{formated(current_time.year, 4)}-"
            f"{formated(current_time.month)}-"
            f"{formated(current_time.day)}_"
            f"{formated(current_time.hour)}:"
            f"{formated(current_time.minute)}:"
            f"{formated(current_time.second)}")


def download_from_source(cls, context, source: str, download_source: str, asset_lib_path: str, tag: str, admin: bool):
    props = context.window_manager.kanistra_props
    authenticated = props.authenticated

    if authenticated:
        source_files_list_response = auth.get(context, source)
    else:
        source_files_list_response = requests.get(source)
    if source_files_list_response.status_code != 200:
        cls.report(
            {"ERROR"},
            "Server didn't send response"
        )
        return

    source_data = dict()
    for file in source_files_list_response.json():
        pk = file['id']
        h = file['hash']
        name = file['name']
        size = file['size']
        is_free = file.get('is_free', True)
        source_data[name] = (h, pk, size, is_free)

    local_data = version_control.load_versions_data(context, admin)
    for file, h in local_data['files'].items():
        file_path = os.path.join(asset_lib_path, file)
        if file not in source_data.keys():
            os.remove(file_path)
            continue
        if source_data[file][0] == h:
            del source_data[file]

    cls.total_size = sum([i[2] for i in source_data.values()])
    cls.downloaded_size = 0
    block_size = 1024 * 16  # 16 kB

    if len(source_data) == 0:
        cls.report({"INFO"}, f"Library is up to date")

    tag = create_tag(tag)
    if not admin:
        local_data["version_tags"].append(tag)

    try:
        if authenticated:
            auth.post(context, f"{server_config.SERVER}/statistics/download/")
        else:
            requests.post(f"{server_config.SERVER}/statistics/download/")
    except:
        pass

    for file, (h, pk, _, is_free) in source_data.items():
        if not is_free and not authenticated:
            continue
        if authenticated:
            download_file_response = auth.get(context, f"{download_source}{pk}/", stream=True)
        else:
            download_file_response = requests.get(f"{download_source}{pk}/", stream=True)
        file_path = Path(asset_lib_path)
        for i in file.split("/"):
            file_path /= i

        if not os.path.exists(file_path.parents[0]):
            os.makedirs(file_path.parents[0])
        cls.filename = file_path.name

        if download_file_response.status_code != 200:
            cls.report({"ERROR"}, download_file_response.text)
            return

        with open(file_path, 'wb') as f:
            for data in download_file_response.iter_content(block_size):
                if props.download_status != 'DOWNLOADING':
                    f.close()
                    os.remove(f.name)
                    version_control.save_versions_data(context, local_data, admin)
                    if admin:
                        update_publish_tags(context, asset_lib_path)
                    return
                cls.downloaded_size += len(data)
                f.write(data)
        local_data['files'][file] = h
        if tag != "" and not admin:
            mark_file_with_tag(context, file_path, tag, "add")
    version_control.save_versions_data(context, local_data, admin)
    if admin:
        update_publish_tags(context, asset_lib_path)
    for root, dirs, fls in os.walk(asset_lib_path):
        if len(dirs) + len(fls) == 0:
            os.remove(root)


def update_publish_tags(context, asset_lib: str):
    files_tags = get_files_and_tags(asset_lib)
    publish_tags = set()
    for _, tags in files_tags.items():
        for t in tags:
            if t.lower().startswith("published_at"):
                publish_tags.add(t)
    publish_tags = list(publish_tags)
    publish_tags.sort()
    data = version_control.load_versions_data(context, admin=True)
    data["version_tags"] = publish_tags
    version_control.save_versions_data(context, data, admin=True)


def index_library_draft_files(cls, files):
    cls.total_files = len(files)
    cls.files_done = 0
    for file in files:
        cls.current_file = file.split(os.path.sep)[-1]
        mark_file_with_tag(None, file, "draft", "draft")
        cls.files_done += 1


def index_library_draft(cls, context, asset_lib):
    files = get_files_list_by_tag(asset_lib,
                                  lambda tags: "draft" not in tags and
                                               not any([t.lower().startswith("published_at") for t in tags]))
    index_library_draft_files(cls, files)


def index_library_draft2publish_files(cls, files, tag):
    cls.total_files = len(files)
    cls.files_done = 0
    for file in files:
        cls.current_file = file.split(os.path.sep)[-1]
        mark_file_with_tag(None, file, tag, "publish")
        cls.files_done += 1


def index_library_draft2publish(cls, context, asset_lib, tag):
    files = get_files_list_by_tag(asset_lib, lambda tags: "draft" in tags)
    index_library_draft2publish_files(cls, files, tag)


def get_all_blend_entities(data):
    return list(data.objects) + list(data.collections) + list(data.materials)


def get_files_list_by_tag(asset_lib, tags_function):
    files = []
    for filepath, _ in walk_in_asset_lib(asset_lib):
        if not filepath.endswith(".blend"):
            continue
        with bpy.data.libraries.load(filepath, link=False) as (df, dt):
            dt.objects = df.objects
            dt.collections = df.collections
            dt.materials = df.materials
        for obj in get_all_blend_entities(dt):
            if obj.asset_data:
                if tags_function(list([x.name for x in obj.asset_data.tags])):
                    files.append(filepath)
                    break
    return files


def get_files_and_tags(asset_lib: str):
    files = dict()
    for filepath, name in walk_in_asset_lib(asset_lib):
        if not filepath.endswith(".blend"):
            continue
        files[filepath] = set()
        with bpy.data.libraries.load(filepath, link=False) as (df, dt):
            dt.objects = df.objects
            dt.collections = df.collections
            dt.materials = df.materials
        for obj in get_all_blend_entities(dt):
            if obj.asset_data:
                for tag in [x.name for x in obj.asset_data.tags]:
                    files[filepath].add(tag)
    return files


def push_library(cls, context, push: bool, asset_lib: str):
    publish_tag = create_tag("Published")
    cls.push_status = "Indexing"
    files_tags = get_files_and_tags(asset_lib)
    draft_files = list([fp for fp, tags in files_tags.items() if "draft" in tags])
    if push:
        to_draft_files = list([fp for fp, tags in files_tags.items() if
                               "draft" not in tags and
                               not any([t.lower().startswith("published_at") for t in tags])
                               ])
        index_library_draft_files(cls, to_draft_files)
        draft_files += to_draft_files
    else:
        index_library_draft2publish_files(cls, draft_files, publish_tag)

    cls.report({"INFO"}, str(draft_files))

    all_files = []
    for filepath, name in walk_in_asset_lib(asset_lib):
        all_files.append((filepath, name))

    cls.total_files = len(all_files)
    cls.files_done = 0
    cls.push_status = "Hashing"

    local_files = dict()
    local_data = version_control.load_versions_data(context, admin=True)
    for filepath, name in all_files:
        cls.current_file = filepath.split(os.path.sep)[-1]
        if (
                filepath in draft_files or
                name not in local_data['files'].keys() or
                filepath.endswith(".txt")
        ):
            h = filehash.filehash(filepath)
            local_data['files'][name] = h
        else:
            h = local_data['files'][name]
        local_files[h] = (filepath, name, "free" in files_tags.get(filepath, []))
        cls.files_done += 1

    version_control.save_versions_data(context, local_data, admin=True)

    cls.report({"INFO"}, "Hashing done")

    if not push:
        cls.push_status = "Publishing"
        push_publish(cls, context, f"{server_config.SERVER}/blendfiles/", local_files.copy())
    cls.push_status = "Pushing"
    push_publish(cls, context, f"{server_config.SERVER}/admin-files/files/", local_files.copy())

    if not push:
        auth.post(context, f"{server_config.SERVER}/statistics/data/", json={"tag": publish_tag})
        version_data = version_control.load_versions_data(context, True)
        version_data["version_tags"].append(publish_tag)
        version_control.save_versions_data(context, version_data, True)


def push_publish(cls, context, server, local_files):
    source_files_response = auth.get(context, server)
    if source_files_response.status_code != 200:
        cls.report({"ERROR"}, f"{source_files_response.status_code}: {source_files_response.text}")
        return

    for file in source_files_response.json():
        if file['hash'] in local_files.keys() and file['name'] == local_files[file['hash']][1]:
            del local_files[file['hash']]
        else:
            auth.delete(context, f"{server}{file['id']}/")

    cls.total_files = len(local_files)
    cls.files_done = 0

    for _, (fp, name, free) in local_files.items():
        cls.current_file = fp.split(os.path.sep)[-1]
        with open(fp, "rb") as f:
            all_files = {'file': f}
            data = {'name': name, "is_free": free}
            auth.post(context, server, files=all_files, data=data)
        cls.files_done += 1
