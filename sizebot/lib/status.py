try:
    import pystemd.daemon as daemon
except ImportError:
    daemon = None


def ready():
    if not daemon:
        return
    daemon.notify(False, ready=1)


def stopping():
    if not daemon:
        return
    daemon.notify(False, stopping=1)
