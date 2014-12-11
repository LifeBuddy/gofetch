import os
import threading
from .builder import load_from_file

FIFO = '/var/run/gofetch.fifo'
CONF = '/etc/gofetch.conf'


def watch_rpc(regi):
    """
    Runs the RPC mechanism.

    Watches on the FIFO for lines of remotes
    """
    oldmask = os.umask(0)
    try:
        os.mkfifo(FIFO)
    finally:
        os.umask(oldmask)
    try:
        with open(FIFO, 'r') as fifo:
            for line in fifo:
                path = line.rstrip()
                try:
                    wspace = regi[path]
                except KeyError:
                    pass
                else:
                    wspace.pull()
    finally:
        os.unlink(FIFO)


def masterrunner():
    """Run the application."""
    regi = dict(load_from_file(CONF))
    for ws in regi.values():
        ws.pull()
        ws.autopush()
        threading.Thread(target=ws.watch, name=ws.workspace, daemon=True).start()
    watch_rpc(regi)
