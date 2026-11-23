r"""Build 16:9 slides with python-pptx in the house style (see figstyle.py):
cover title 44 pt, slide titles 32 pt, body text 24 pt, secondary text
(sub-bullets, labels, captions) 20 pt; formulas typeset by LaTeX at the size of
the text around them (never PowerPoint's equation editor); pictures sized for a
HALF or FULL slide and placed as large as possible. (18 pt is only for text
*inside* figures.)

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
    deck.bullets("Resolved rates", [r"$\dot q = J^{+}(q)\, v$",        # 24 pt
                                    ["sub-point, 20 pt", "another"]])   # list = sub-bullets
    deck.equation(r"\min_{q} \; \tfrac12 \|q - q_0\|^2", title="Objective")
    deck.video("../videos/orbit.mp4", title="Orbit view")               # poster = orbit.png
    deck.save("../slides/talk.pptx")                                    # then pptx_to_pdf.py

Any text containing ``$...$`` is typeset by LaTeX as a whole line.

Logo: every slide except the cover carries the lab logo (``assets/logo.png``,
transparent background) in the top-right corner of the title bar.
``Deck(logo="path.png")`` swaps it, ``Deck(logo=None)`` turns it off.
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
COVER_PT = fs.SLIDE_COVER_PT
TITLE_PT, BODY_PT, SMALL_PT = fs.SLIDE_TITLE_PT, fs.SLIDE_BODY_PT, fs.SLIDE_SMALL_PT


def line_h(size_pt):
    return Pt(size_pt * 1.25)
TEXT_COLOR = RGBColor(0x20, 0x20, 0x20)
EMU_PER_PT = 12700
DEFAULT_LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo.png")
LOGO_H = Inches(0.85)                   # logo height in the title bar
LOGO_TOP = Inches(0.15)                 # gap above the logo


class Deck:
    def __init__(self, math_dir="../imgs/math", font="Arial", logo=DEFAULT_LOGO):
        self.logo = os.path.abspath(logo) if logo and os.path.exists(logo) else None
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.font = font
        self.math_dir = math_dir

    # ================================================================ slides
    def title(self, title, subtitle=None):
        """Cover: big title and subtitle as one block, centered on the slide
        (a little above the middle, which looks centered). No logo here."""
        s = self._blank()
        tw = W - Inches(1.6)
        n = max(1, math.ceil(_text_width_pt(title, COVER_PT) / (tw / EMU_PER_PT * 0.95)))
        title_h = line_h(COVER_PT) * n
        gap2 = Inches(0.3)
        sub_h = line_h(BODY_PT) if subtitle else 0
        total = title_h + (gap2 + sub_h if subtitle else 0)
        y = (H - total) / 2 - Inches(0.2)
        self._text(s, title, Inches(0.8), y, tw, title_h, size=COVER_PT, bold=True, center=True)
        y += title_h + gap2
        if subtitle:
            self._text(s, subtitle, Inches(0.8), y, tw, sub_h,
                       size=BODY_PT, center=True, color=RGBColor(0x55, 0x55, 0x55))
        return s

    def bullets(self, title, items):
        s = self._blank()
        top = self._title(s, title)
        self._flow(s, items, MARGIN + Inches(0.3), top + GAP,
                   W - 2 * MARGIN - Inches(0.6), H - top - MARGIN)
        return s

    def equation(self, latex, title=None, caption=None):
        """One display formula, centered on the slide (24 pt, LaTeX)."""
        s = self._blank()
        top = self._title(s, title) if title else self._top_no_title(s)
        png, w_pt, h_pt = latex_math.render(latex, self.math_dir, display=True,
                                            size_pt=BODY_PT, max_width_in=fs.CONTENT_W)
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
        lab_h = line_h(SMALL_PT) if labels else 0
        cw = (W - 2 * MARGIN - (cols - 1) * GAP) / cols
        ch = (bottom - top - (rows - 1) * GAP) / rows - lab_h
        for i, p in enumerate(paths):
            r, c = divmod(i, cols)
            x, y = MARGIN + c * (cw + GAP), top + r * (ch + lab_h + GAP)
            self._fit_picture(s, p, x, y, cw, ch)
            if labels:
                self._text(s, labels[i], x, y + ch, cw, lab_h, size=SMALL_PT, center=True)
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

    def _logo(self, s):
        """Logo in the top-right corner of the title bar; returns its width."""
        if not self.logo:
            return 0
        iw, ih = Image.open(self.logo).size
        lw = int(LOGO_H * iw / ih)
        s.shapes.add_picture(self.logo, int(W - MARGIN - lw), int(LOGO_TOP), lw, LOGO_H)
        return lw

    def _title(self, s, title):
        lw = self._logo(s)
        right = lw + Inches(0.25) if lw else 0
        self._text(s, title, Inches(0.4), LOGO_TOP, W - Inches(0.8) - right, LOGO_H,
                   size=TITLE_PT, bold=True)
        return TITLE_H

    def _top_no_title(self, s):
        """Slide without a title: still show the logo; content starts below it."""
        return TITLE_H if self._logo(s) else MARGIN

    def _area(self, s, title, has_caption):
        top = self._title(s, title) if title else self._top_no_title(s)
        bottom = H - MARGIN - (line_h(SMALL_PT) + Inches(0.05) if has_caption else 0)
        return top, bottom

    def _caption(self, s, caption):
        self._line(s, caption, MARGIN, H - MARGIN - line_h(SMALL_PT), W - 2 * MARGIN,
                   size=SMALL_PT, center=True)

    def _fit_picture(self, s, path, x, y, w, h):
        iw, ih = Image.open(path).size
        s.shapes.add_picture(os.path.abspath(path), *_fit(iw, ih, x, y, w, h))

    def _flow(self, s, items, x, y, w, h, center_v=False):
        """Stack bullet rows top-down. A str item is a 24 pt bullet; a list item
        holds 20 pt sub-bullets. Rows with $...$ are LaTeX images."""
        rows = []
        for it in items:
            subs = it if isinstance(it, (list, tuple)) else None
            for t in (subs or [it]):
                size, mark, indent = (SMALL_PT, "– ", Inches(0.4)) if subs else (BODY_PT, "• ", 0)
                rw = w - indent
                if "$" in t:
                    png, w_pt, h_pt = latex_math.render(mark + t, self.math_dir, size_pt=size,
                                                        max_width_in=rw / 914400)
                    rows.append(("img", png, indent, Emu(int(w_pt * EMU_PER_PT)),
                                 Emu(int(h_pt * EMU_PER_PT)), size))
                else:
                    n = max(1, math.ceil(_text_width_pt(mark + t, size) / (rw / EMU_PER_PT)))
                    rows.append(("txt", mark + t, indent, rw, line_h(size) * n + Pt(4), size))
        space = Pt(10)
        total = sum(r[4] for r in rows) + space * (len(rows) - 1)
        cy = y + ((h - total) / 2 if center_v and total < h else 0)
        for kind, content, indent, rw, rh, size in rows:
            if kind == "img":
                s.shapes.add_picture(content, int(x + indent), int(cy), rw, rh)
            else:
                self._text(s, content, x + indent, cy, rw, rh, size=size, anchor=MSO_ANCHOR.TOP)
            cy += rh + space

    def _line(self, s, text, x, y, w, size=BODY_PT, center=False, bold=False):
        if "$" in text:
            if bold:
                text = r"\textbf{" + text + "}"
            png, w_pt, h_pt = latex_math.render(text, self.math_dir, size_pt=size,
                                                max_width_in=w / 914400)
            iw, ih = Emu(int(w_pt * EMU_PER_PT)), Emu(int(h_pt * EMU_PER_PT))
            ix = x + (w - iw) / 2 if center else x
            s.shapes.add_picture(png, int(ix), int(y), iw, ih)
        else:
            self._text(s, text, x, y, w, line_h(size), size=size, center=center, bold=bold)

    def _text(self, s, text, x, y, w, h, size=BODY_PT, bold=False, center=False,
              color=TEXT_COLOR, anchor=MSO_ANCHOR.MIDDLE):
        if "$" in text:
            ly = y + max(0, (h - line_h(size)) / 2) if anchor == MSO_ANCHOR.MIDDLE else y
            return self._line(s, text, x, ly, w, size=size, center=center, bold=bold)
        tf = s.shapes.add_textbox(int(x), int(y), int(w), int(h)).text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = text
        if center:
            p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name = Pt(size), bold, self.font
            r.font.color.rgb = color


_FONT = None


def _text_width_pt(s, size):
    """Rendered width in pt: measured with Arial (or a metric-compatible font);
    CJK characters count as 1 em."""
    global _FONT
    if _FONT is None:
        from PIL import ImageFont
        _FONT = False
        for name in ("arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf",
                     "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                     "/Library/Fonts/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
            try:
                _FONT = ImageFont.truetype(name, 100)
                break
            except OSError:
                pass
    cjk = sum(1 for ch in s if ord(ch) > 0x2E80)
    latin = "".join(ch for ch in s if ord(ch) <= 0x2E80)
    if _FONT:
        w_latin = _FONT.getlength(latin) / 100 * size
    else:
        w_latin = len(latin) * size * 0.5
    return w_latin + cjk * size


def _fit(iw, ih, x, y, w, h):
    """Largest (x, y, w, h) with the image's aspect ratio inside the box, centered."""
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    return Emu(int(x + (w - pw) / 2)), Emu(int(y + (h - ph) / 2)), Emu(pw), Emu(ph)
