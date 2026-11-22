"""Check everything doc-maker needs and print an install hint for each gap.

Run with the Python interpreter that should have `one` installed:
    python check_env.py            # all checks
    python check_env.py --slides   # only what slides need
    python check_env.py --paper    # only what the LaTeX paper needs
Exit code 0 = all required items present, 1 = something missing.
"""
import argparse
import importlib
import os
import shutil
import subprocess
import sys

VSCODE_PATHS = [
    r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd",
    r"%ProgramFiles%\Microsoft VS Code\bin\code.cmd",
]


def _code_cmd():
    c = shutil.which("code")
    if c:
        return c
    for p in VSCODE_PATHS:
        p = os.path.expandvars(p)
        if os.path.exists(p):
            return p
    return None


def check_python():
    ok = sys.version_info >= (3, 12)
    return ok, f"{sys.version.split()[0]} ({sys.executable})", \
        "one needs Python >= 3.12; install from python.org or `winget install Python.Python.3.12`"


def check_module(mod, hint):
    def _f():
        try:
            m = importlib.import_module(mod)
            return True, getattr(m, "__file__", "") or "ok", hint
        except Exception as e:  # noqa: BLE001
            return False, f"{type(e).__name__}: {e}", hint
    return _f


def check_ffmpeg():
    try:
        import imageio_ffmpeg
        return True, imageio_ffmpeg.get_ffmpeg_exe(), ""
    except Exception as e:  # noqa: BLE001
        return False, str(e), f"{sys.executable} -m pip install imageio imageio-ffmpeg"


def check_vscode():
    c = _code_cmd()
    return bool(c), c or "not found", "winget install -e --id Microsoft.VisualStudioCode"


def _vscode_ext(ext_id, hint_name):
    def _f():
        c = _code_cmd()
        if not c:
            return False, "VS Code not found", "install VS Code first"
        try:
            out = subprocess.run([c, "--list-extensions"], capture_output=True,
                                 text=True, timeout=60, shell=c.endswith(".cmd")).stdout
        except Exception as e:  # noqa: BLE001
            return False, str(e), f'code --install-extension {ext_id}'
        ok = ext_id.lower() in out.lower().split()
        return ok, ext_id if ok else f"{hint_name} not installed", f"code --install-extension {ext_id}"
    return _f


def check_powerpoint():
    if sys.platform != "win32":
        return False, "not Windows", "PowerPoint export uses Windows COM"
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application\CurVer") as k:
            ver = winreg.QueryValue(k, None)
        return True, ver, ""
    except OSError:
        return False, "not installed", "Install Microsoft PowerPoint (Microsoft 365 / Office); "\
            "the user must do this themselves"


def check_latex():
    for exe in ("latexmk", "xelatex", "pdflatex"):
        if not shutil.which(exe):
            return False, f"{exe} not on PATH", \
                "winget install -e --id MiKTeX.MiKTeX  (or TeX Live from tug.org), then reopen the terminal"
    return True, shutil.which("latexmk"), ""


PIP = f"{sys.executable} -m pip install"
ONE_HINT = ("git clone https://github.com/wanweiwei07/one.git && cd one && "
            f"{PIP} -e .")

CORE = [
    ("Python >= 3.12", check_python, True),
    ("one (Python library)", check_module("one", ONE_HINT), True),
    ("VS Code", check_vscode, True),
    ("Pillow", check_module("PIL", f"{PIP} pillow"), True),
    ("imageio + ffmpeg (videos)", check_ffmpeg, True),
    ("VS Code PDF viewer ext", _vscode_ext("tomoki1207.pdf", "vscode-pdf"), False),
]
SLIDES = [
    ("python-pptx", check_module("pptx", f"{PIP} python-pptx"), True),
    ("pywin32 (PowerPoint COM)", check_module("win32com.client", f"{PIP} pywin32"), True),
    ("Microsoft PowerPoint", check_powerpoint, True),
]
PAPER = [
    ("LaTeX (latexmk/xelatex)", check_latex, True),
    ("VS Code LaTeX Workshop ext", _vscode_ext("james-yu.latex-workshop", "LaTeX Workshop"), True),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slides", action="store_true")
    ap.add_argument("--paper", action="store_true")
    a = ap.parse_args()
    checks = list(CORE)
    if a.slides or not (a.slides or a.paper):
        checks += SLIDES
    if a.paper or not (a.slides or a.paper):
        checks += PAPER
    missing = False
    for name, fn, required in checks:
        ok, info, hint = fn()
        tag = "OK     " if ok else ("MISSING" if required else "OPTION ")
        print(f"[{tag}] {name}: {info}")
        if not ok:
            print(f"          install: {hint}")
            missing |= required
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
