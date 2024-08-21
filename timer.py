import bpy

from . import addon_updater_ops


def on_startup_timer():
    addon_updater_ops.check_for_update_background()

    return None


def show_update_popup_timer():
    addon_updater_ops.updater_run_install_popup_handler(None)
    return None


timers = [
    (on_startup_timer, {"first_interval": 0}),
    (show_update_popup_timer, {"first_interval": 3})
]


def register_timers():
    if bpy.app.background:
        return

    for t, kw in timers:
        bpy.app.timers.register(t, **kw)


def unregister_timers():
    if bpy.app.background:
        return

    for t, kw in timers:
        if bpy.app.timers.is_registered(t):
            bpy.app.timers.unregister(t)
