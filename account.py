import bpy
from . import thumbnails, auth


class LogOutOperator(bpy.types.Operator):
    bl_label = "Log out"
    bl_idname = "kanistra.logout_operator"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        auth.log_out(context)
        self.report({"INFO"}, "Logged out")
        return {"FINISHED"}


class DeleteAccountOperator(bpy.types.Operator):
    bl_label = "Delete account"
    bl_idname = "kanistra.delete_account_operator"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        status, text = auth.delete_account(context)
        self.report({status}, text)
        return {"FINISHED"}


class AccountPanel(bpy.types.Panel):
    bl_label = "Account"
    bl_idname = "kanistra.account_panel"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOLS"

    @classmethod
    def poll(self, context):
        props = context.window_manager.kanistra_props
        lib_ref = getattr(context.space_data.params, "asset_library_ref", None)
        lib_ref = getattr(context.space_data.params, "asset_library_reference", lib_ref)
        return context.area.ui_type == "ASSETS" and lib_ref.lower() in ["kanistra assets", "kanistra admin"] and props.authenticated

    def draw(self, context):
        props = context.window_manager.kanistra_props
        layout = self.layout
        col = layout.column()

        col.label(text=f"Login: {props.login}", icon_value=thumbnails.get_thumbnails()["user"].icon_id)
        col.operator("kanistra.logout_operator", text="Log out", icon_value=thumbnails.get_thumbnails()["logout"].icon_id)

        col.label(text="Warning zone!")
        col.alert = True
        col.operator("kanistra.delete_account_operator", text="Delete account", icon_value=thumbnails.get_thumbnails()["delete-account"].icon_id)

