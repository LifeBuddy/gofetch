import os

FIFO = '/var/run/gofetch.fifo'


def watch_rpc(regi):
    """
    Runs the RPC mechanism.

    Watches on the FIFO for lines of remotes
    """
    os.mkfifo(FIFO)
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
