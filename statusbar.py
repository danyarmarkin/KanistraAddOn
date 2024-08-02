import bpy
from . import thumbnails


def statusbar_ui(self, context):
    props = context.window_manager.kanistra_props
    if props.progress:
        row = self.layout.row(align=True)
        row.label(text='Downloading assets: ', icon_value=thumbnails.get_thumbnails()['kanistra'].icon_id)
        row.label(text=props.progress)
        row.operator("kanistra.cancel_download_kanistra_assets", text="", icon="CANCEL")


def update_progress(context, progress, filename=None):
    props = context.window_manager.kanistra_props
    props.progress = "{:.1f}%".format(progress)
    context.workspace.status_text_set_internal(filename)
    for a in context.screen.areas:
        if a.type == "PROPERTIES":
            a.tag_redraw()


def end_progress(context):
    props = context.window_manager.kanistra_props
    props.progress = ""
    context.workspace.status_text_set_internal(None)
    for a in context.screen.areas:
        if a.type == "PROPERTIES":
            a.tag_redraw()


class UpdateAnimOperator(bpy.types.Operator):
    bl_idname = 'kanistra.anim_update_operator'
    bl_label = "Simple Operator"

    def execute(self, context):
        props = context.window_manager.kanistra_props
        props.download_anim_index = (props.download_anim_index + 1) % 23
        p = float(props.progress[:-1])
        p += 0.1156
        props.progress = "{:.2f}%".format(p)
        context.workspace.status_text_set_internal(None)
        return {"FINISHED"}


def update_download_anim_index():
    scene = bpy.context.window_manager
    if scene is not None and hasattr(scene, 'kanistra_props'):
        bpy.ops.kanistra.anim_update_operator()
        return 0.1
    return 1
