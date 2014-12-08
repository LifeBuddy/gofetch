"""
Primitives for syncing the repos, including async behavior.

It is assumed that repos are workspaces map 1:1.
"""

import os
import subprocess
import pwd
import grp
import re
import threading
import time
import traceback
import pyinotify
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

    def __init__(self, path, flags=None):
        """Workspace(str)"""
        self.workspace = os.path.abspath(path)
        self.flags = flags or {}
        self.lock = threading.RLock()

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
            raise subprocess.CalledProcessError(retcode, proc.args)

    def autopush(self):
        """
        Autocommit and push up.

        If the remote rejects it, a pull will attempted.
        """
        with self.lock:
            status, _ = self._git('status', '--porcelain', stdout=PIPE).communicate()
            if len(status):
                self._check(self._git('add', '.'))
                self._check(self._git('commit', '.', '-m', "Autocommit"))
                self._check(self._git('push'))
                # TODO: If remote rejects, pull and push again.
            else:
                print("Skipping...")

    def pull(self):
        """
        Pull from the remote repo.

        If something cannot be automatically merged, we use the version in git.
        """
        with self.lock:
            print("pull")
            self._check(self._git('pull', '--commit', '-X', 'theirs'))
            self._check(self._git('push'))

    def remotes(self):
        """
        List the remotes of a function.

        name, URL, direction.
        """
        rem = self._git('remote', '-v', stdout=PIPE)
        REMOTES = re.compile(r"(.*)\t(.*) \((.*)\)")
        for line in rem.stdout:
            match = REMOTES.match(line.decode('utf-8').rstrip())
            yield match.groups()

    def watch(self, wait=10):
        """
        Watch with inotify and autopush on change.

        TODO: Document threading
        """
        # 1. Set recurrent, resettable timer to call autopush
        @RecallerTimer
        def dothething():
            "Do the thing!"
            self.autopush()
        dothething.start()
        # 2. Watch self.workspace
        wm = pyinotify.WatchManager()
        wm.add_watch(
            self.workspace,
            pyinotify.IN_CREATE | pyinotify.IN_DELETE |
            pyinotify.IN_MODIFY | pyinotify.IN_ATTRIB |
            pyinotify.IN_MOVE_SELF |
            pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO,
            rec=True,
            auto_add=True,
            exclude_filter=lambda path: path.endswith('/.git') or '/.git/' in path,
            )
        # 3. on change, reset timer
        def handleevent(event):
            dothething.schedule(time.time() + wait)
        notifier = pyinotify.Notifier(wm, handleevent)
        notifier.loop()


class RecallerTimer:
    """
    Schedule a thing to be called. Rescheduling prevents the
    previous schedule from executing, unless it already did.
    """
    def __init__(self, func):
        self.func = func
        self.event = threading.Event()
        self.lock = threading.Lock()
        self.when = None
        self.thread = None

    def schedule(self, when):
        """
        Set a schedule.

        If the function is currently scheduled, use this schedule instead.

        If not, it is now!
        """
        with self.lock:
            self.when = when
            self.event.set()

    def job(self):
        """The check/delay loop."""
        while True:
            now = time.time()
            if self.when is None:
                self.event.wait()
            elif now < self.when:
                time.sleep(self.when - now)
            else:
                with self.lock:
                    self.when = None
                    self.event.clear()
                try:
                    self.func()
                except Exception:
                    # Eat it and continue
                    traceback.print_exc()

    def start(self):
        """Start the processing thread."""
        self.thread = threading.Thread(
            target=self.job,
            name=self.func.__name__,
            daemon=True)
        self.thread.start()
