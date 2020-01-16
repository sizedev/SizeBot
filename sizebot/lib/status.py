try:
    from systemd import daemon
except ImportError:
    daemon = None


def ready():
    if not daemon:
        return
    daemon.notify(daemon.Notification.READY)


def stopping():
    if not daemon:
        return
    daemon.notify(daemon.Notification.STOPPING)
