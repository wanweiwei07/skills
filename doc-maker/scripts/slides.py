r"""Build 16:9 slides with python-pptx in the house style (see figstyle.py):
all text 18 pt, formulas typeset by LaTeX (never PowerPoint's equation editor),
pictures sized for a HALF or FULL slide and placed as large as possible.

    import sys; sys.path.insert(0, r"<path to doc-maker>/scripts")
    from slides import Deck
    deck = Deck(math_dir="../imgs/math")
    deck.title("Grasp Planning with one", "Lab meeting · 2026-11-22")
    deck.image("../imgs/scene_full.png", title="Scene")                 # FULL figure
    deck.image_text("../imgs/grasp_half.png", title="Antipodal grasp",  # HALF figure + text
                    items=["contacts on opposite faces",
                           r"friction cone: $\|f_t\| \le \mu f_n$"])
    deck.images(["../imgs/a.png", "../imgs/b.png"], title="Before / after",
                labels=["before", "after"])                             # two HALF figures
    deck.bullets("Resolved rates", [r"$\dot q = J^{+}(q)\, v$", "plain text"])
    deck.equation(r"\min_{q} \; \tfrac12 \|q - q_0\|^2", title="Objective")
    deck.video("../videos/orbit.mp4", title="Orbit view")               # poster = orbit.png
    deck.save("../slides/talk.pptx")                                    # then pptx_to_pdf.py

Any text containing ``$...$`` is typeset by LaTeX as a whole line.
"""
import math
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

import figstyle as fs
import latex_math

W, H = Inches(fs.SLIDE_W), Inches(fs.SLIDE_H)
MARGIN = Inches(fs.MARGIN)
TITLE_H = Inches(fs.TITLE_H)
GAP = Inches(fs.GAP)
FONT_PT = fs.FONT_PT
LINE_H = Pt(FONT_PT * 1.25)
TEXT_COLOR = RGBColor(0x20, 0x20, 0x20)
EMU_PER_PT = 12700


class Deck:
    def __init__(self, math_dir="../imgs/math", font="Arial"):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.font = font
        self.math_dir = math_dir

    # ================================================================ slides
    def title(self, title, subtitle=None):
        s = self._blank()
        self._text(s, title, Inches(0.8), Inches(3.0), W - Inches(1.6), Inches(0.6),
                   bold=True, center=True)
        if subtitle:
            self._text(s, subtitle, Inches(0.8), Inches(3.6), W - Inches(1.6), Inches(0.6),
                       center=True, color=RGBColor(0x55, 0x55, 0x55))
        return s

    def bullets(self, title, items):
        s = self._blank()
        top = self._title(s, title)
        self._flow(s, items, MARGIN + Inches(0.3), top + GAP,
                   W - 2 * MARGIN - Inches(0.6), H - top - MARGIN)
        return s

    def equation(self, latex, title=None, caption=None):
        """One display formula, centered on the slide (18 pt, LaTeX)."""
        s = self._blank()
        top = self._title(s, title) if title else MARGIN
        png, w_pt, h_pt = latex_math.render(latex, self.math_dir, display=True,
                                            max_width_in=fs.CONTENT_W)
        w, h = Emu(int(w_pt * EMU_PER_PT)), Emu(int(h_pt * EMU_PER_PT))
        y = top + (H - top - MARGIN - h) / 2
        s.shapes.add_picture(png, int((W - w) / 2), int(y), w, h)
        if caption:
            self._caption(s, caption)
        return s

    def image(self, path, title=None, caption=None):
        """A FULL-slide figure, as large as the area under the title allows."""
        return self.images([path], title=title, caption=caption)

    def images(self, paths, title=None, caption=None, labels=None):
        """1 picture = FULL, 2 = two HALF columns, 3-4 = grid; each fills its cell."""
        s = self._blank()
        top, bottom = self._area(s, title, caption)
        n = len(paths)
        cols, rows = (n, 1) if n <= 3 else (2, 2)
        lab_h = LINE_H if labels else 0
        cw = (W - 2 * MARGIN - (cols - 1) * GAP) / cols
        ch = (bottom - top - (rows - 1) * GAP) / rows - lab_h
        for i, p in enumerate(paths):
            r, c = divmod(i, cols)
            x, y = MARGIN + c * (cw + GAP), top + r * (ch + lab_h + GAP)
            self._fit_picture(s, p, x, y, cw, ch)
            if labels:
                self._text(s, labels[i], x, y + ch, cw, LINE_H, center=True)
        if caption:
            self._caption(s, caption)
        return s

    def image_text(self, path, items, title=None, side="left"):
        """A HALF-slide figure next to a column of text / formulas."""
        s = self._blank()
        top, bottom = self._area(s, title, None)
        half = (W - 2 * MARGIN - GAP) / 2
        img_x = MARGIN if side == "left" else MARGIN + half + GAP
        txt_x = MARGIN + half + GAP if side == "left" else MARGIN
        self._fit_picture(s, path, img_x, top, half, bottom - top)
        self._flow(s, items, txt_x + Inches(0.1), top, half - Inches(0.1), bottom - top,
                   center_v=True)
        return s

    def video(self, path, title=None, caption=None, poster=None):
        """A video (720p) scaled to fill the slide. ``poster`` defaults to the
        .png written next to it by one_capture.record(); PowerPoint shows it
        before playback and in the exported PDF."""
        s = self._blank()
        top, bottom = self._area(s, title, caption)
        poster = poster or os.path.splitext(path)[0] + ".png"
        iw, ih = Image.open(poster).size
        x, y, w, h = _fit(iw, ih, MARGIN, top, W - 2 * MARGIN, bottom - top)
        s.shapes.add_movie(os.path.abspath(path), x, y, w, h,
                           poster_frame_image=os.path.abspath(poster), mime_type="video/mp4")
        if caption:
            self._caption(s, caption)
        return s

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.prs.save(path)
        return os.path.abspath(path)

    # ============================================================ internals
    def _blank(self):
        return self.prs.slides.add_slide(self.prs.slide_layouts[6])

    def _title(self, s, title):
        self._text(s, title, Inches(0.4), Inches(0.1), W - Inches(0.8), TITLE_H - Inches(0.1),
                   bold=True)
        return TITLE_H

    def _area(self, s, title, has_caption):
        top = self._title(s, title) if title else MARGIN
        bottom = H - MARGIN - (LINE_H + Inches(0.05) if has_caption else 0)
        return top, bottom

    def _caption(self, s, caption):
        self._line(s, caption, MARGIN, H - MARGIN - LINE_H, W - 2 * MARGIN, center=True)

    def _fit_picture(self, s, path, x, y, w, h):
        iw, ih = Image.open(path).size
        s.shapes.add_picture(os.path.abspath(path), *_fit(iw, ih, x, y, w, h))

    def _flow(self, s, items, x, y, w, h, center_v=False):
        """Stack bullet rows top-down; rows with $...$ are LaTeX images."""
        rows = []
        for it in items:
            if "$" in it:
                png, w_pt, h_pt = latex_math.render("• " + it, self.math_dir,
                                                    max_width_in=w / 914400)
                rows.append(("img", png, Emu(int(w_pt * EMU_PER_PT)), Emu(int(h_pt * EMU_PER_PT))))
            else:
                n_lines = max(1, math.ceil(_text_width_pt("• " + it) / (w / EMU_PER_PT * 0.95)))
                rows.append(("txt", "• " + it, w, LINE_H * n_lines + Pt(6)))
        space = Pt(10)
        total = sum(r[3] for r in rows) + space * (len(rows) - 1)
        cy = y + ((h - total) / 2 if center_v and total < h else 0)
        for kind, content, rw, rh in rows:
            if kind == "img":
                s.shapes.add_picture(content, int(x), int(cy), rw, rh)
            else:
                self._text(s, content, x, cy, rw, rh, anchor=MSO_ANCHOR.TOP)
            cy += rh + space

    def _line(self, s, text, x, y, w, center=False):
        if "$" in text:
            png, w_pt, h_pt = latex_math.render(text, self.math_dir, max_width_in=w / 914400)
            iw, ih = Emu(int(w_pt * EMU_PER_PT)), Emu(int(h_pt * EMU_PER_PT))
            ix = x + (w - iw) / 2 if center else x
            s.shapes.add_picture(png, int(ix), int(y), iw, ih)
        else:
            self._text(s, text, x, y, w, LINE_H, center=center)

    def _text(self, s, text, x, y, w, h, bold=False, center=False, color=TEXT_COLOR,
              anchor=MSO_ANCHOR.MIDDLE):
        if "$" in text:
            return self._line(s, text, x, y, w, center=center)
        tf = s.shapes.add_textbox(int(x), int(y), int(w), int(h)).text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        if center:
            p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name = Pt(FONT_PT), bold, self.font
            r.font.color.rgb = color


def _text_width_pt(s):
    """Rough rendered width at FONT_PT: CJK ~1 em, latin ~0.55 em."""
    return sum(FONT_PT if ord(ch) > 0x2E80 else FONT_PT * 0.55 for ch in s)


def _fit(iw, ih, x, y, w, h):
    """Largest (x, y, w, h) with the image's aspect ratio inside the box, centered."""
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    return Emu(int(x + (w - pw) / 2)), Emu(int(y + (h - ph) / 2)), Emu(pw), Emu(ph)
