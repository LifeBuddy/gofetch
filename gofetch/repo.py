"""
Primitives for syncing the repos, including async behavior.

It is assumed that repos are workspaces map 1:1.
"""

import os
import subprocess
import pwd
import grp
import re
from subprocess import PIPE

def popen(args, *, user=None, group=None, **kw):
    """
    Wrapper around subprocess.Popen to implement setuid/setgid.

    Please note that if you are not root and try to do this, an error will
    probably be raised.
    """
    uid = gid = None
    if user is not None:
        uid = pwd.getpwnam(user).pw_uid
    if group is not None:
        gid = grp.getgrnam(group).gr_gid

    def preexec():
        """Set the UID/GID of the process before the exec()."""
        if uid is not None:
            os.setuid(uid)
        if gid is not None:
            os.setgid(gid)

    return subprocess.Popen(args, preexec_fn=preexec, **kw)


class Workspace:

    """
    Manages the the actual push and pull process.

    Operations are executed asyncronously, and only one executes at a time.
    """
    # TODO: Actually implement mutex

    def __init__(self, path, flags=None):
        """Workspace(str)"""
        self.workspace = os.path.abspath(path)
        self.flags = flags or {}

    def _git(self, *args, **kw):
        """Execute git."""
        flgs = self.flags.copy()
        flgs.update(kw)
        return popen(('git',)+args, cwd=self.workspace, **flgs)

    @staticmethod
    def _check(proc):
        """Temporary method that waits and checks a Popen object."""
        retcode = proc.wait()
        if retcode != 0:
            raise subprocess.CalledProcessError

    def autopush(self):
        """
        Autocommit and push up.

        If the remote rejects it, a pull will attempted.
        """
        self._check(self._git('add', '.'))
        self._check(self._git('commit', '.', '-m', "Autocommit"))
        self._check(self._git('push'))
        # TODO: If remote rejects, pull and push again.

    def pull(self):
        """
        Pull from the remote repo.

        If something cannot be automatically merged, we use the version in git.
        """
        self._check(self._git('pull', '--commit', '-X', 'theirs'))
        self._check(self._git('push'))

    def remotes(self):
        rem = self._git('remote', '-v', stdout=PIPE)
        REMOTES = re.compile(r"(.*)\t(.*) \((.*)\)")
        for line in rem.stdout:
            match = REMOTES.match(line.rstrip())
            yield match.groups()

    def watch(self):
        