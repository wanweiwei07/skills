"""Render text / math with real LaTeX (xelatex) to a transparent PNG for slides.

PowerPoint's own equation editor is never used. The PNG is made so that when
it is placed at its natural size (``w_pt`` x ``h_pt`` points) on a slide, the
glyphs are exactly ``size_pt`` points tall, i.e. the same size as 18 pt slide
text.

    from latex_math import render
    png, w_pt, h_pt = render(r"$\\dot{q} = J^{+}(q)\\,v$", "../imgs/math", display=True)

``latex`` is LaTeX source: plain text with inline ``$...$`` math, or a bare
formula with ``display=True`` (typeset as ``\\[ ... \\]``). Text uses TeX Gyre
Heros (an Arial / Helvetica look-alike, ships with TeX Live and MiKTeX) so it
matches the slide font; Chinese / Japanese text is supported. Results are cached
by content hash in ``out_dir``.
"""
import hashlib
import os
import shutil
import subprocess
import tempfile

PREAMBLE = r"""\documentclass[border=0.5pt,varwidth=%(width)s]{standalone}
\usepackage[no-math]{fontspec}
\setmainfont{texgyreheros}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,
  ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\usepackage{amsmath,amssymb,bm}
%(cjk)s
\usepackage{xcolor}
\begin{document}
\fontsize{%(size)s}{%(lead)s}\selectfont\color[HTML]{%(color)s}%%
%(body)s
\end{document}
"""


def _has_cjk(s):
    return any("぀" <= ch <= "ヿ" or "一" <= ch <= "鿿" or
               "가" <= ch <= "힯" for ch in s)


def render(latex, out_dir, size_pt=18, display=False, color="202020",
           max_width_in=12.0, dpi=600):
    """Return (png_path, width_pt, height_pt)."""
    import fitz  # PyMuPDF
    body = (r"$\displaystyle " + latex + "$") if display else latex
    cjk = r"\usepackage{xeCJK}" if _has_cjk(latex) else ""
    src = PREAMBLE % {"width": f"{max_width_in}in", "cjk": cjk, "size": f"{size_pt}pt",
                      "lead": f"{size_pt * 1.25:.1f}pt", "color": color, "body": body}
    key = hashlib.sha1((src + str(dpi)).encode("utf-8")).hexdigest()[:16]
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.abspath(os.path.join(out_dir, f"math_{key}.png"))
    pdf_cached = png[:-4] + ".pdf"
    if not os.path.exists(png) or not os.path.exists(pdf_cached):
        with tempfile.TemporaryDirectory() as tmp:
            tex = os.path.join(tmp, "m.tex")
            with open(tex, "w", encoding="utf-8") as f:
                f.write(src)
            r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "m.tex"],
                               cwd=tmp, capture_output=True, text=True, errors="replace",
                               timeout=180)
            pdf = os.path.join(tmp, "m.pdf")
            if r.returncode != 0 or not os.path.exists(pdf):
                log = r.stdout[-2500:]
                raise RuntimeError(f"LaTeX failed for:\n{latex}\n--- log tail ---\n{log}")
            shutil.copy(pdf, pdf_cached)
        doc = fitz.open(pdf_cached)
        doc[0].get_pixmap(dpi=dpi, alpha=True).save(png)
        doc.close()
    doc = fitz.open(pdf_cached)
    w_pt, h_pt = doc[0].rect.width, doc[0].rect.height
    doc.close()
    return png, w_pt, h_pt
