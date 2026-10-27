"""Re-exec a harness entry point with a neutral argv.

Submitted code runs as the same user as the harness and can read every
process's /proc/<pid>/cmdline. If the harness was started as
`python3 /home/me/repo/ladder/run.py`, that line names the repository and the
answer key beside it. neutral_argv() passes the script's path and arguments to
the new image over a pipe that is read and closed before any submission exists,
so the process's cmdline afterwards is only the Python binary, -c, and a loader.
"""

from __future__ import annotations

import json
import os
import sys

_LOADER = (
    "import json, os, runpy, sys\n"
    "fd = int(sys.argv[1])\n"
    "cfg = json.loads(os.read(fd, 1 << 20))\n"
    "os.close(fd)\n"
    "sys.argv = [cfg['name']] + cfg['argv']\n"
    "sys.path.insert(0, cfg['dir'])\n"
    "runpy.run_path(cfg['path'], run_name='__main__')\n"
)


def neutral_argv(script_file: str) -> None:
    """Replace this process with one whose cmdline does not name the script."""
    if os.environ.get("LADDER_BOOTED") == "1":
        return
    path = os.path.abspath(script_file)
    cfg = {"path": path, "dir": os.path.dirname(path), "name": os.path.basename(path), "argv": sys.argv[1:]}
    rfd, wfd = os.pipe()
    os.write(wfd, json.dumps(cfg).encode())
    os.close(wfd)
    os.set_inheritable(rfd, True)
    env = {k: v for k, v in os.environ.items() if k not in ("PWD", "OLDPWD", "PYTHONPATH")}
    env["LADDER_BOOTED"] = "1"
    sys.stdout.flush()
    sys.stderr.flush()
    os.execve(sys.executable, [sys.executable, "-c", _LOADER, str(rfd)], env)
