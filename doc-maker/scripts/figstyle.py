"""House style shared by every figure, slide and video.

* Text INSIDE figures 18 pt.  Slide text: cover title 44 pt, slide titles
  32 pt, body 24 pt, secondary (sub-bullets, labels, captions) 20 pt.
* All lines 1.5 pt.  * Formulas typeset by LaTeX.
* Figures are made at the exact size they occupy on a 16:9 slide, either a
  HALF slide (one of two columns under the title) or a FULL slide (the whole
  area under the title). Try HALF first; use FULL when it does not fit.
* Videos default to 1280x720 (720p, 16:9).

Matplotlib plots:

    import sys; sys.path.insert(0, r"<path to doc-maker>/scripts")
    import figstyle
    fig, ax = figstyle.figure("half")          # or "full"
    ax.plot(t, q, label=r"$q_1(t)$")
    ax.set_xlabel(r"$t$ [s]")
    figstyle.save(fig, "../imgs/joint_traj.png")
"""
import shutil

# ---- slide geometry (inches); must match slides.py ------------------------
SLIDE_W, SLIDE_H = 13.333, 7.5
MARGIN = 0.25
TITLE_H = 1.1             # title bar, tall enough for the logo on the right
GAP = 0.15
CONTENT_W = SLIDE_W - 2 * MARGIN                    # 12.833
CONTENT_H = SLIDE_H - TITLE_H - MARGIN              # 6.15
HALF_W = (CONTENT_W - GAP) / 2                      # 6.342

SIZES_IN = {
    "full": (CONTENT_W, CONTENT_H),
    "half": (HALF_W, CONTENT_H),
}
DPI = 200                       # pixels per inch for raster figures / renders
VIDEO_SIZE = (1280, 720)        # every video: 720p 16:9

FONT_PT = 18            # text inside figures (plots, diagrams)
SLIDE_COVER_PT = 44     # big title on the first slide
SLIDE_TITLE_PT = 32
SLIDE_BODY_PT = 24
SLIDE_SMALL_PT = 20
LINE_PT = 1.5


def size_in(layout):
    return SIZES_IN[layout]


def size_px(layout, dpi=DPI):
    if layout == "video":
        return VIDEO_SIZE
    w, h = SIZES_IN[layout]
    return int(round(w * dpi)), int(round(h * dpi))


def apply_matplotlib():
    import matplotlib as mpl
    rc = {
        "font.size": FONT_PT, "axes.titlesize": FONT_PT, "axes.labelsize": FONT_PT,
        "xtick.labelsize": FONT_PT, "ytick.labelsize": FONT_PT,
        "legend.fontsize": FONT_PT, "figure.titlesize": FONT_PT,
        "legend.title_fontsize": FONT_PT, "figure.labelsize": FONT_PT,
        "lines.linewidth": LINE_PT, "axes.linewidth": LINE_PT,
        "patch.linewidth": LINE_PT, "hatch.linewidth": LINE_PT,
        "grid.linewidth": LINE_PT * 0.5,
        "xtick.major.width": LINE_PT, "ytick.major.width": LINE_PT,
        "xtick.minor.width": LINE_PT * 0.67, "ytick.minor.width": LINE_PT * 0.67,
        "lines.markeredgewidth": LINE_PT,
        "savefig.dpi": DPI, "figure.dpi": 100,
        "font.family": "sans-serif",
        "font.sans-serif": ["TeX Gyre Heros", "Arial", "Helvetica", "DejaVu Sans"],
    }
    if shutil.which("latex"):
        # formulas (and labels) typeset by real LaTeX, sans text like the slides
        # (matplotlib itself loads helvet for the sans-serif text)
        rc.update({
            "text.usetex": True,
            # tick numbers ($\mathdefault{..}$) in the sans text font, like all other text
            "text.latex.preamble": r"\usepackage{amsmath,amssymb,bm}"
                                   r"\renewcommand{\mathdefault}[1]{\text{#1}}",
            "font.sans-serif": ["Helvetica"],
        })
    else:
        rc.update({"mathtext.fontset": "cm"})
    mpl.rcParams.update(rc)


def figure(layout="half", **kw):
    """plt.subplots() at the exact slide size of ``layout`` with house style."""
    import matplotlib.pyplot as plt
    apply_matplotlib()
    kw.setdefault("layout", "constrained")
    return plt.subplots(figsize=size_in(layout), **kw)


def unify_text(fig, size=FONT_PT):
    """Every piece of text in the figure at one size (titles, labels, ticks,
    legends, annotations, colorbars, offset text). Returns what was changed."""
    from matplotlib.text import Text
    changed = []
    fig.draw_without_rendering()                    # create tick labels etc.
    for ax in fig.axes:                             # ticks are rebuilt on draw: set at the source
        for axis in (ax.xaxis, ax.yaxis):
            labels = axis.get_ticklabels(which="both")
            sizes = {round(l.get_fontsize(), 2) for l in labels if l.get_text()}
            if sizes - {float(size)}:
                changed.append((f"{axis.axis_name} ticks", max(sizes - {float(size)})))
                ax.tick_params(axis=axis.axis_name, which="both", labelsize=size)
    for t in fig.findobj(Text):
        if t.get_visible() and t.get_text().strip() and abs(t.get_fontsize() - size) > 0.01:
            changed.append((t.get_text()[:30], t.get_fontsize()))
            t.set_fontsize(size)
    return changed


def save(fig, path):
    """Save at the exact slide size. All text is forced to 18 pt first, so one
    figure never mixes big and small text; a note lists what was resized."""
    import os
    changed = unify_text(fig)
    if changed:
        print(f"figstyle: set {len(changed)} text item(s) to {FONT_PT} pt in {os.path.basename(path)}: "
              + ", ".join(f"{t!r} ({s:g} pt)" for t, s in changed[:6]))
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    fig.savefig(path, dpi=DPI)        # no bbox "tight": keep the exact slide size
    return os.path.abspath(path)
