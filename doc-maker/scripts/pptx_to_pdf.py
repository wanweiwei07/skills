"""Export a .pptx to .pdf with Microsoft PowerPoint, in the background.

    python pptx_to_pdf.py slides/talk.pptx            -> slides/talk.pdf
    python pptx_to_pdf.py slides/talk.pptx out.pdf

No PowerPoint window is opened. Embedded videos appear in the PDF as their
poster image (still frame).
"""
import os
import sys


def export(pptx, pdf=None):
    import pythoncom
    import win32com.client
    pptx = os.path.abspath(pptx)
    pdf = os.path.abspath(pdf or os.path.splitext(pptx)[0] + ".pdf")
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
    return pdf


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    print(export(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
