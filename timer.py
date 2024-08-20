import bpy

from . import addon_updater_ops


def on_startup_timer():
    addon_updater_ops.check_for_update_background()

    return None


def register_timers():
    if bpy.app.background:
        return

    bpy.app.timers.register(on_startup_timer)


def unregister_timers():
    if bpy.app.background:
        return

    if bpy.app.timers.is_registered(on_startup_timer):
        bpy.app.timers.unregister(on_startup_timer)