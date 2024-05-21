try:
    from cysystemd import daemon
except ImportError:
    daemon = None

# Used on linux to report bot status to systemd


def ready():
    if not daemon:
        return
    daemon.notify(daemon.Notification.READY)


def stopping():
    if not daemon:
        return
    daemon.notify(daemon.Notification.STOPPING)
