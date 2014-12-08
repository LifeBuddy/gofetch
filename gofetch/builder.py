"""
Responsible for reading in the config file and creating objects from it.

Config files work like this:
* If it starts with an '@', it's interpretted as a flag and applies to
  repos following it
* Otherwise, it's a path to a workspace to keep synced.
"""

from .repo import Workspace


def load_from_file(fn):
    """
    Read a config file, producing a dictionary mapping
    Workspace objects.
    """
    rv = {}
    ops = {}
    for line in open(fn):
        wspath = line.strip()
        if wspath.startswith('@'):
            # This is actually a flag
            key, value = wspath[1:].split('=', 1)
            ops[key] = value
            continue
        workspace = Workspace(wspath, **ops)

        for _, remote, _ in workspace.remotes():
            yield remote, workspace
