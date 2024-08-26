import subprocess
from datetime import datetime
from pathlib import Path
import os
import requests
from . import auth, version_control

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


def walk_in_asset_lib(lib_path):
    for root, _, fls in os.walk(lib_path):
        for file in fls:
            filepath = os.path.join(root, file)
            if not (filepath.endswith('.blend') or filepath.endswith(".txt")):
                continue
            yield filepath, os.path.relpath(filepath, lib_path).replace(os.path.sep, "/")


FIRST = lambda x: x[0]
SECOND = lambda x: x[1]


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

    current_time = datetime.now()

    def formated(n, c=2):
        return "0" * max(0, c - len(str(n))) + str(n)

    tag = (f"{tag}_at_"
           f"{formated(current_time.year, 4)}-"
           f"{formated(current_time.month)}-"
           f"{formated(current_time.day)}_"
           f"{formated(current_time.hour)}:"
           f"{formated(current_time.minute)}:"
           f"{formated(current_time.second)}")
    local_data["version_tags"].append(tag)

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
                    return
                cls.downloaded_size += len(data)
                f.write(data)
        local_data['files'][file] = h
        if tag != "":
            mark_file_with_tag(context, file_path, tag, "add")
    version_control.save_versions_data(context, local_data, admin)
    for root, dirs, fls in os.walk(asset_lib_path):
        if len(dirs) + len(fls) == 0:
            os.remove(root)
