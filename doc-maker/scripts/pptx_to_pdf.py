"""Export a .pptx to .pdf in the background (no window).

    python pptx_to_pdf.py slides/talk.pptx            -> slides/talk.pdf
    python pptx_to_pdf.py slides/talk.pptx out.pdf

Windows: Microsoft PowerPoint (via COM). Linux / macOS, or Windows without
PowerPoint: LibreOffice (`soffice --headless`). Embedded videos appear in the
PDF as their poster image (still frame).
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def has_powerpoint():
    if sys.platform != "win32":
        return False
    import winreg
    try:
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application\CurVer").Close()
        return True
    except OSError:
        return False


def find_soffice():
    for exe in ("soffice", "libreoffice"):
        p = shutil.which(exe)
        if p:
            return p
    cands = [r"C:\Program Files\LibreOffice\program\soffice.exe",
             r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
             "/Applications/LibreOffice.app/Contents/MacOS/soffice"]
    cands += glob.glob("/opt/libreoffice*/program/soffice")
    return next((c for c in cands if os.path.exists(c)), None)


def export_powerpoint(pptx, pdf):
    import pythoncom
    import win32com.client
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx("PowerPoint.Application")
    pres = None
    try:
        # ReadOnly, Untitled=False, WithWindow=False  -> nothing shown
        pres = app.Presentations.Open(pptx, True, False, False)
        pres.SaveAs(pdf, 32)  # 32 = ppSaveAsPDF
    finally:
        if pres is not None:
            pres.Close()
        try:
            if app.Presentations.Count == 0:  # don't kill the user's own session
                app.Quit()
        except Exception:  # noqa: BLE001
            pass
        pythoncom.CoUninitialize()


def export_libreoffice(pptx, pdf, soffice):
    with tempfile.TemporaryDirectory() as out:
        # separate profile dir so it works even while LibreOffice is open
        profile = "file:///" + os.path.join(out, "profile").replace("\\", "/").lstrip("/")
        subprocess.run([soffice, f"-env:UserInstallation={profile}", "--headless",
                        "--convert-to", "pdf", "--outdir", out, pptx],
                       check=True, capture_output=True, timeout=600)
        produced = os.path.join(out, os.path.splitext(os.path.basename(pptx))[0] + ".pdf")
        if not os.path.exists(produced):
            raise RuntimeError("LibreOffice did not produce a PDF")
        shutil.move(produced, pdf)


def export(pptx, pdf=None):
    pptx = os.path.abspath(pptx)
    pdf = os.path.abspath(pdf or os.path.splitext(pptx)[0] + ".pdf")
    if has_powerpoint():
        export_powerpoint(pptx, pdf)
        return pdf
    soffice = find_soffice()
    if soffice:
        export_libreoffice(pptx, pdf, soffice)
        return pdf
    sys.exit("No PowerPoint or LibreOffice found. Install Microsoft PowerPoint "
             "(Windows/macOS) or LibreOffice (Linux: sudo apt install libreoffice-impress).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(export(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
