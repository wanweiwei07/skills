"""Find a Python (>= 3.12) that can `import one`, including one inside a virtual
environment (uv / venv / conda) that is not activated.

Can be run with any Python 3, even one that does not have `one`:
    python find_python.py                  # search the usual places
    python find_python.py --one C:\\one     # also look in this one checkout
    python find_python.py --python PATH    # check (and remember) this interpreter

Prints one line per candidate, then on success
    PYTHON=<interpreter to use for every doc-maker step>
    INSTALL=<command prefix to install packages into it>
and remembers the interpreter in .python-path next to this skill, so the next
session finds it first. Exit code 0 = found, 1 = not found.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SAVED = os.path.join(os.path.dirname(HERE), ".python-path")
WIN = sys.platform == "win32"
PROBE = ("import sys; import one; "
         "print(sys.version.split()[0]); print(one.__file__)")


def venv_python(env_dir):
    """Interpreter inside a venv / conda env folder, or None."""
    names = (["Scripts/python.exe", "python.exe"] if WIN
             else ["bin/python3", "bin/python"])
    for n in names:
        p = os.path.join(env_dir, n)
        if os.path.isfile(p):
            return os.path.abspath(p)
    return None


def env_kind(py):
    """'uv venv', 'venv', 'conda' or 'system' for an interpreter path."""
    d = os.path.dirname(py)
    root = os.path.dirname(d) if os.path.basename(d).lower() in ("scripts", "bin") else d
    cfg = os.path.join(root, "pyvenv.cfg")
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8", errors="replace") as f:
            text = f.read()
        return "uv venv" if any(l.startswith("uv ") or l.startswith("uv=")
                                for l in text.splitlines()) else "venv"
    if os.path.isdir(os.path.join(root, "conda-meta")):
        return "conda"
    return "system"


def has_pip(py):
    r = subprocess.run([py, "-c", "import pip"], capture_output=True)
    return r.returncode == 0


def install_prefix(py):
    q = f'"{py}"' if " " in py else py
    if env_kind(py) == "uv venv" or not has_pip(py):
        if shutil.which("uv"):
            return f"uv pip install --python {q}"
        return f"{q} -m ensurepip && {q} -m pip install"
    return f"{q} -m pip install"


def ancestors(path):
    path = os.path.abspath(path)
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            return
        path = parent


def candidates(args):
    """(label, interpreter path or command list) in priority order."""
    if args.python:
        yield "--python", args.python
        return
    if args.one:
        for v in (".venv", "venv"):
            yield f"--one {v}", venv_python(os.path.join(args.one, v))
    if os.path.isfile(SAVED):
        with open(SAVED, encoding="utf-8") as f:
            p = f.read().strip()
        if p:
            yield "remembered (.python-path)", p
    for var in ("VIRTUAL_ENV", "CONDA_PREFIX"):
        if os.environ.get(var):
            yield f"${var}", venv_python(os.environ[var])
    for d in ancestors(os.getcwd()):
        for v in (".venv", "venv"):
            yield f"{v} in {d}", venv_python(os.path.join(d, v))
    # a one checkout next to the work folder, in the home folder or at the drive root
    roots = list(ancestors(os.getcwd())) + [os.path.expanduser("~")]
    for d in dict.fromkeys(roots):
        for v in (".venv", "venv"):
            yield f"one/{v} in {d}", venv_python(os.path.join(d, "one", v))
    for exe in ("python", "python3"):
        if shutil.which(exe):
            yield f"{exe} on PATH", shutil.which(exe)
    if WIN and shutil.which("py"):
        yield "py -3.12", ["py", "-3.12"]
        yield "py", ["py"]


def probe(cmd):
    """Return (ok, message, resolved interpreter path)."""
    argv = list(cmd) if isinstance(cmd, list) else [cmd]
    # run from an empty folder so a directory called `one` in the current
    # folder is not mistaken for the installed library
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run(argv + ["-c", PROBE + "; print(sys.executable)"],
                               capture_output=True, text=True, cwd=tmp, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as e:
            return False, str(e), None
    if r.returncode != 0:
        err = (r.stderr.strip().splitlines() or ["failed"])[-1]
        return False, err, None
    ver, one_file, exe = r.stdout.strip().splitlines()[-3:]
    if one_file in ("None", ""):
        return False, "`one` is a bare folder, not the installed library", None
    if tuple(int(x) for x in ver.split(".")[:2]) < (3, 12):
        return False, f"Python {ver} < 3.12", None
    return True, f"Python {ver}, one at {one_file}", exe


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--one", help="folder of a one checkout (its .venv / venv is tried)")
    ap.add_argument("--python", help="check this interpreter only")
    a = ap.parse_args()
    seen = set()
    for label, cmd in candidates(a):
        if not cmd:
            continue
        key = os.path.normcase(os.path.abspath(cmd)) if isinstance(cmd, str) else tuple(cmd)
        if key in seen:
            continue
        seen.add(key)
        ok, msg, exe = probe(cmd)
        print(f"[{'OK' if ok else '--'}] {label}: {msg}")
        if ok:
            print(f"PYTHON={exe}")
            print(f"KIND={env_kind(exe)}")
            print(f"INSTALL={install_prefix(exe)}")
            try:
                with open(SAVED, "w", encoding="utf-8") as f:
                    f.write(exe + "\n")
            except OSError:
                pass
            sys.exit(0)
    print("No Python that can `import one` was found. Ask the user where one is "
          "installed and re-run with --one <folder> or --python <interpreter>.")
    sys.exit(1)


if __name__ == "__main__":
    main()
