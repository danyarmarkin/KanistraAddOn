bl_info = {
    "name": "Kanistra Client",
    "description": "Access to Kanistra Studio models library",
    "author": "Kanistra Studio",
    "version": (0, 3, 6),
    "blender": (4, 0, 0),
    "category": "Import-Export",
    "doc_url": "https://kanistra.com",
}

if "bpy" not in locals():
    from . import addon_updater_ops
    from . import asset_browser_panel
    from . import download_operator
    from . import open_kanistra_assets_operator
    from . import thumbnails
    from . import logger
    from . import download_assets_operator
    from . import statusbar
    from . import check_updates_operator
    from . import links_operators
    from . import download_history_panel
    from . import search_tag_operator
    from . import login
    from . import auth
    from . import account
    from . import admin
    from . import timer
else:
    from importlib import reload
    reload(addon_updater_ops)
    reload(asset_browser_panel)
    reload(download_operator)
    reload(open_kanistra_assets_operator)
    reload(thumbnails)
    reload(logger)
    reload(download_assets_operator)
    reload(statusbar)
    reload(check_updates_operator)
    reload(links_operators)
    reload(download_history_panel)
    reload(search_tag_operator)
    reload(login)
    reload(auth)
    reload(account)
    reload(admin)
    reload(timer)

import bpy
from bpy.app.handlers import persistent


@addon_updater_ops.make_annotations
class AddOnPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    auto_check_update = bpy.props.BoolProperty(
        name="Auto-check for Update",
        description="If enabled, auto-check for updates using an interval",
        default=True,
    )

    updater_interval_months = bpy.props.IntProperty(
        name='Months',
        description="Number of months between checking for updates",
        default=0,
        min=0
    )
    updater_interval_days = bpy.props.IntProperty(
        name='Days',
        description="Number of days between checking for updates",
        default=0,
        min=0,
    )
    updater_interval_hours = bpy.props.IntProperty(
        name='Hours',
        description="Number of hours between checking for updates",
        default=0,
        min=0,
        max=23
    )
    updater_interval_minutes = bpy.props.IntProperty(
        name='Minutes',
        description="Number of minutes between checking for updates",
        default=1,
        min=0,
        max=59
    )

    def draw(self, context):
        addon_updater_ops.update_settings_ui(self, context)


class KanistraProperties(bpy.types.PropertyGroup):
    progress: bpy.props.StringProperty(options={"HIDDEN"})
    download_anim_index: bpy.props.IntProperty(default=0, options={"HIDDEN"})
    download_status: bpy.props.StringProperty(default='NONE', options={"HIDDEN"})
    updates: bpy.props.IntProperty(default=0, options={"HIDDEN"})
    updates_size: bpy.props.IntProperty(default=0, options={"HIDDEN"})
    show_more_history: bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    # log in / log up
    access_token: bpy.props.StringProperty(default='token', options={"HIDDEN"})
    refresh_token: bpy.props.StringProperty(default='token', options={"HIDDEN"})
    login: bpy.props.StringProperty(name='Email', options={"HIDDEN"})
    password: bpy.props.StringProperty(name='Password', options={"HIDDEN"}, subtype="PASSWORD")
    password_again: bpy.props.StringProperty(name='Password again', options={"HIDDEN"}, subtype="PASSWORD")
    license_agreement: bpy.props.BoolProperty(name='I agree with addon policy', default=False, options={"HIDDEN"})
    email_sends_agreement: bpy.props.BoolProperty(name='I agree with email notification', default=False, options={"HIDDEN"})
    login_or_logup: bpy.props.BoolProperty(default=False, options={"HIDDEN"})
    authenticated: bpy.props.BoolProperty(default=False, options={"HIDDEN"})
    register_code: bpy.props.StringProperty(name='Code', options={"HIDDEN"})
    need_activation: bpy.props.BoolProperty(default=False, options={"HIDDEN"})

    # admin
    admin: bpy.props.BoolProperty(default=False, options={"HIDDEN"})
    admin_updates: bpy.props.IntProperty(default=0, options={"HIDDEN"})
    admin_updates_size: bpy.props.IntProperty(default=0, options={"HIDDEN"})
    admin_users: bpy.props.StringProperty(default='[]', options={"HIDDEN"})


classes = [
    AddOnPreferences,
    KanistraProperties,
    download_operator.DownloadAssetsOperator,
    open_kanistra_assets_operator.OpenKanistraAssetsOperator,
    download_assets_operator.DownloadKanistraAssetsOperator,
    download_assets_operator.CancelDownloadingOperator,
    statusbar.UpdateAnimOperator,
    check_updates_operator.CheckUpdatesOperator,
    search_tag_operator.SearchTagOperator,
    login.LoginOperator,
    login.LoginPanel,
    download_history_panel.DownloadHistoryPanel,
    links_operators.KanistraLinksPanel,
    account.DeleteAccountOperator,
    account.LogOutOperator,
    admin.UsersCountPanel,
    account.AccountPanel,
    admin.OpenAdminOperator,
    admin.PublishAdminOperator,
    admin.PushAdminOperator,
    admin.PullAdminOperator,
]


# Register classes
def register():
    logger.prepare()
    logger.log("register")
    thumbnails.thumbnails_register()
    addon_updater_ops.register(bl_info)

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.ASSETBROWSER_MT_editor_menus.append(open_kanistra_assets_operator.draw_operator)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(download_assets_operator.draw_operator)
    bpy.types.ASSETBROWSER_MT_editor_menus.append(admin.draw_operators)

    bpy.types.WindowManager.kanistra_props = bpy.props.PointerProperty(type=KanistraProperties)

    bpy.types.STATUSBAR_HT_header.prepend(statusbar.statusbar_ui)

    bpy.app.handlers.load_post.append(auth.load_auth_handler)
    bpy.app.handlers.load_post.append(check_updates_operator.load_check_handler)

    timer.register_timers()

    # bpy.app.timers.register(update_download_anim_index)


def unregister():
    addon_updater_ops.unregister()
    logger.log("unregister called")

    timer.unregister_timers()

    bpy.app.handlers.load_post.remove(check_updates_operator.load_check_handler)
    bpy.app.handlers.load_post.remove(auth.load_auth_handler)

    bpy.types.STATUSBAR_HT_header.remove(statusbar.statusbar_ui)

    del bpy.types.WindowManager.kanistra_props

    bpy.types.ASSETBROWSER_MT_editor_menus.remove(open_kanistra_assets_operator.draw_operator)
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(admin.draw_operators)
    bpy.types.ASSETBROWSER_MT_editor_menus.remove(download_assets_operator.draw_operator)

    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    thumbnails.thumbnails_unregister()


if __name__ == "__main__":
    register()
