import bpy
import pathlib
from . import thumbnails


class DownloadAssetsOperator(bpy.types.Operator):
    bl_idname = "kanistra.download_asset"
    bl_label = "Download original"
    bl_description = "Download original of this model"

    def execute(self, context):
        name = pathlib.PurePath(context.space_data.params.filename).name
        self.report({"INFO"}, f"tried to download model {name}")
        try:
            self.report({"INFO"}, thumbnails.get_thumbnails())
        except Exception as e:
            self.report({"INFO"}, f"error : {e}")
        return {'FINISHED'}
