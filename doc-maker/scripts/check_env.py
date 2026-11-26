"""Check everything doc-maker needs and print an install hint for each gap.

Run with the Python interpreter that should have `one` installed (find it with
find_python.py; it may be an unactivated uv / venv / conda environment):
    python check_env.py            # all checks
    python check_env.py --slides   # only what slides need
    python check_env.py --paper    # only what the LaTeX paper needs
Exit code 0 = all required items present, 1 = something missing.
"""
import argparse
import importlib
import importlib.util
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


def _env_kind():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import find_python
    return find_python.env_kind(sys.executable)


def _pip_cmd():
    """Install command for *this* interpreter. uv venvs have no pip by default."""
    exe = f'"{sys.executable}"' if " " in sys.executable else sys.executable
    has_pip = importlib.util.find_spec("pip") is not None
    if _env_kind() == "uv venv" or not has_pip:
        if shutil.which("uv"):
            return f"uv pip install --python {exe}"
        return f"{exe} -m ensurepip && {exe} -m pip install"
    return f"{exe} -m pip install"


def check_python():
    ok = sys.version_info >= (3, 12)
    return ok, f"{sys.version.split()[0]} ({sys.executable}, {_env_kind()})", \
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
        return False, str(e), f"{PIP} imageio imageio-ffmpeg"


def check_vscode():
    c = _code_cmd()
    hint = {"win32": "winget install -e --id Microsoft.VisualStudioCode",
            "darwin": "brew install --cask visual-studio-code"}.get(
        sys.platform, "sudo snap install code --classic   (or the .deb/.rpm from code.visualstudio.com)")
    return bool(c), c or "not found", hint


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


def _office_hint():
    if sys.platform == "win32":
        return ("Install Microsoft PowerPoint (Microsoft 365 / Office) yourself, "
                "or LibreOffice: winget install -e --id TheDocumentFoundation.LibreOffice")
    if sys.platform == "darwin":
        return "brew install --cask libreoffice"
    return "sudo apt install libreoffice-impress   (Fedora: sudo dnf install libreoffice-impress)"


def check_office():
    """PowerPoint (Windows) or LibreOffice, for .pptx -> .pdf export."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pptx_to_pdf as p2p
    if p2p.has_powerpoint():
        try:
            import win32com.client  # noqa: F401
            return True, "Microsoft PowerPoint", ""
        except ImportError:
            return False, "PowerPoint found but pywin32 missing", f"{PIP} pywin32"
    s = p2p.find_soffice()
    if s:
        return True, f"LibreOffice ({s})", ""
    return False, "neither PowerPoint nor LibreOffice found", _office_hint()


def check_latex():
    for exe in ("latexmk", "xelatex", "pdflatex"):
        if not shutil.which(exe):
            hint = {"win32": "winget install -e --id MiKTeX.MiKTeX  (or TeX Live from tug.org), "
                             "then reopen the terminal",
                    "darwin": "brew install --cask mactex-no-gui"}.get(
                sys.platform, "sudo apt install texlive-xetex texlive-lang-cjk latexmk")
            return False, f"{exe} not on PATH", hint
    return True, shutil.which("latexmk"), ""


PIP = _pip_cmd()
if shutil.which("uv"):
    ONE_HINT = ("git clone https://github.com/wanweiwei07/one.git && cd one && "
                "uv venv --python 3.12 && uv pip install --python .venv -e .   "
                "(then use one/.venv as the Python)")
else:
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
    ("PowerPoint / LibreOffice (PDF export)", check_office, True),
    ("PyMuPDF (formula images, PDF preview)", check_module("fitz", f"{PIP} pymupdf"), True),
    ("matplotlib (plots)", check_module("matplotlib", f"{PIP} matplotlib"), False),
    ("LaTeX (formulas on slides)", lambda: check_latex(), False),
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
