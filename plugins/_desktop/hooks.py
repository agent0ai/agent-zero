def disable(**kwargs):
    from plugins._desktop.helpers.runtime import stop
    stop()

uninstall = disable
