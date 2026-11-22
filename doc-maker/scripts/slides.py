"""Helpers for building 16:9 slides with python-pptx where pictures and
videos fill the slide (scaled as large as possible, aspect kept, centered).

    import sys; sys.path.insert(0, r"<path to doc-maker>/scripts")
    from slides import Deck
    deck = Deck()
    deck.title("Grasp Planning with one", "Lab meeting · 2026-11-22")
    deck.image("../imgs/bunny.png", title="Antipodal grasps on the bunny")
    deck.images(["../imgs/a.png", "../imgs/b.png"], title="Before / after")
    deck.video("../videos/orbit.mp4", title="Orbit view")   # uses orbit.png as poster
    deck.bullets("Summary", ["point one", "point two"])
    deck.save("../slides/talk.pptx")                        # then run pptx_to_pdf.py

Paths are resolved relative to the calling script's working directory.
"""
import os

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

W, H = Inches(13.333), Inches(7.5)
MARGIN = Inches(0.25)          # outer margin around pictures
TITLE_H = Inches(0.85)
CAPTION_H = Inches(0.45)
GAP = Inches(0.15)
TITLE_COLOR = RGBColor(0x20, 0x20, 0x20)


class Deck:
    def __init__(self, font="Arial"):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.font = font

    # -------------------------------------------------------------- slides
    def title(self, title, subtitle=None):
        s = self._blank()
        self._text(s, title, Inches(0.8), Inches(2.6), W - Inches(1.6), Inches(1.4),
                   size=40, bold=True, center=True)
        if subtitle:
            self._text(s, subtitle, Inches(0.8), Inches(4.1), W - Inches(1.6), Inches(0.8),
                       size=22, center=True, color=RGBColor(0x55, 0x55, 0x55))
        return s

    def bullets(self, title, items, size=26):
        s = self._blank()
        top = self._title(s, title)
        box = s.shapes.add_textbox(Inches(0.8), top + GAP, W - Inches(1.6), H - top - Inches(0.6))
        tf = box.text_frame
        tf.word_wrap = True
        for i, it in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = "• " + it
            p.space_after = Pt(10)
            for r in p.runs:
                r.font.size, r.font.name = Pt(size), self.font
        return s

    def image(self, path, title=None, caption=None):
        """One picture, as large as the slide allows."""
        return self.images([path], title=title, caption=caption)

    def images(self, paths, title=None, caption=None, labels=None):
        """1-4 pictures side by side (2x2 for 4), each scaled to fill its cell."""
        s = self._blank()
        top = self._title(s, title) if title else MARGIN
        bottom = H - (CAPTION_H if caption else 0) - MARGIN
        n = len(paths)
        cols, rows = (n, 1) if n <= 3 else (2, 2)
        cw = (W - 2 * MARGIN - (cols - 1) * GAP) / cols
        lab_h = CAPTION_H if labels else 0
        ch = (bottom - top - (rows - 1) * GAP) / rows - lab_h
        for i, p in enumerate(paths):
            r, c = divmod(i, cols)
            x = MARGIN + c * (cw + GAP)
            y = top + r * (ch + lab_h + GAP)
            self._fit_picture(s, p, x, y, cw, ch)
            if labels:
                self._text(s, labels[i], x, y + ch, cw, lab_h, size=16, center=True)
        if caption:
            self._text(s, caption, MARGIN, bottom, W - 2 * MARGIN, CAPTION_H, size=16, center=True)
        return s

    def video(self, path, title=None, caption=None, poster=None):
        """A video scaled to fill the slide. ``poster`` defaults to the .png
        written next to the video by one_capture.record(); PowerPoint shows it
        before playback and in the exported PDF."""
        s = self._blank()
        top = self._title(s, title) if title else MARGIN
        bottom = H - (CAPTION_H if caption else 0) - MARGIN
        poster = poster or os.path.splitext(path)[0] + ".png"
        iw, ih = Image.open(poster).size
        x, y, w, h = _fit(iw, ih, MARGIN, top, W - 2 * MARGIN, bottom - top)
        s.shapes.add_movie(os.path.abspath(path), x, y, w, h,
                           poster_frame_image=os.path.abspath(poster), mime_type="video/mp4")
        if caption:
            self._text(s, caption, MARGIN, bottom, W - 2 * MARGIN, CAPTION_H, size=16, center=True)
        return s

    def save(self, path):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.prs.save(path)
        return os.path.abspath(path)

    # ------------------------------------------------------------- internals
    def _blank(self):
        return self.prs.slides.add_slide(self.prs.slide_layouts[6])

    def _title(self, s, title):
        self._text(s, title, Inches(0.5), Inches(0.15), W - Inches(1.0), TITLE_H - Inches(0.15),
                   size=30, bold=True)
        return TITLE_H

    def _fit_picture(self, s, path, x, y, w, h):
        iw, ih = Image.open(path).size
        s.shapes.add_picture(os.path.abspath(path), *_fit(iw, ih, x, y, w, h))

    def _text(self, s, text, x, y, w, h, size=20, bold=False, center=False, color=TITLE_COLOR):
        from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
        tf = s.shapes.add_textbox(x, y, w, h).text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.text = text
        if center:
            p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.size, r.font.bold, r.font.name = Pt(size), bold, self.font
            r.font.color.rgb = color


def _fit(iw, ih, x, y, w, h):
    """Largest (x, y, w, h) with the image's aspect ratio inside the box, centered."""
    scale = min(w / iw, h / ih)
    pw, ph = int(iw * scale), int(ih * scale)
    return Emu(int(x + (w - pw) / 2)), Emu(int(y + (h - ph) / 2)), Emu(pw), Emu(ph)
