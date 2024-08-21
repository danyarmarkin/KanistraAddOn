import bpy
from . import thumbnails, auth


class LoginOperator(bpy.types.Operator):
    bl_label = "Log in"
    bl_idname = "kanistra.login_operator"

    def execute(self, context):
        props = context.window_manager.kanistra_props
        if not props.login_or_logup:
            status, text = auth.authenticate(context)
        elif props.need_activation:
            status, text = auth.activate_account(context)
        else:
            status, text = auth.log_up(context)
        self.report({status}, text)
        return {"FINISHED"}


class LoginPanel(bpy.types.Panel):
    bl_label = "Kanistra Studio"
    bl_idname = "kanistra.login_panel"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(self, context):
        props = context.window_manager.kanistra_props
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        return context.area.ui_type == "ASSETS" and lib_ref.lower() in ["kanistra assets", "kanistra admin"] and not props.authenticated

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        props = context.window_manager.kanistra_props
        col.prop(
            props,
            "login",
            icon_value=thumbnails.get_thumbnails()["user"].icon_id
        )

        col.prop(
            props,
            "password",
            icon_value=thumbnails.get_thumbnails()["key"].icon_id
        )

        if props.login_or_logup:
            col.prop(
                props,
                "password_again",
                icon_value=thumbnails.get_thumbnails()["key"].icon_id
            )
            col.prop(props, "license_agreement")
            col.prop(props, "email_sends_agreement")

        if props.need_activation:
            col.prop(props, "register_code")

        col.operator("kanistra.login_operator",
                     text=("Verify" if props.need_activation else "Register!") if props.login_or_logup else "Log in!")

        if not props.need_activation:
            col.prop(
                props,
                "login_or_logup",
                text="Already have an account? click here to log in" if props.login_or_logup else
                "Don't have an account? "
                "Click here to register!",
                emboss=False
            )
