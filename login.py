import bpy
from . import thumbnails


class LoginOperator(bpy.types.Operator):
    bl_label = "Log in"
    bl_idname = "kanistra.login_operator"

    def execute(self, context):
        self.report({"INFO"}, "Log in!")
        return {"FINISHED"}


class LoginPanel(bpy.types.Panel):
    bl_label = "Kanistra Studio"
    bl_idname = "kanistra.login_panel"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(self, context):
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        return context.area.ui_type == "ASSETS" and lib_ref.lower() == "kanistra assets"

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.prop(
            context.window_manager.kanistra_props,
            "login",
            icon_value=thumbnails.get_thumbnails()["user"].icon_id
        )

        col.prop(
            context.window_manager.kanistra_props,
            "password",
            icon_value=thumbnails.get_thumbnails()["key"].icon_id
        )

        if context.window_manager.kanistra_props.login_or_logup:
            col.prop(
                context.window_manager.kanistra_props,
                "password_again",
                icon_value=thumbnails.get_thumbnails()["key"].icon_id
            )
            col.prop(
                context.window_manager.kanistra_props,
                "license_agreement"
            )
            col.prop(
                context.window_manager.kanistra_props,
                "email_sends_agreement"
            )

        col.operator("kanistra.login_operator",
                     text="Log up!" if context.window_manager.kanistra_props.login_or_logup else "Log in!")

        col.prop(
            context.window_manager.kanistra_props,
            "login_or_logup",
            text="Already have an account? Log in" if context.window_manager.kanistra_props.login_or_logup else "Don't have an account? Log up",
            emboss=False
        )
