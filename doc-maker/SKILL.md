---
name: doc-maker
description: Make documents (slides / PowerPoint decks, papers, reports) whose figures and videos are rendered with the `one` robotics library, inside a dated project folder viewed in VS Code. Use when the user asks to make, write or prepare slides, a presentation, a PPT, a paper, a report or a document, especially about robots, grasping, motion planning or anything shown with `one`. Also use when they ask for a figure, screenshot, animation or video of a `one` scene for a document.
---

# doc-maker

Produces a document folder in the user's **current working directory**:

```
YYYYMMDD_<name>/          e.g. 20261122_grasp_planning   (no name given → YYYYMMDD_document)
├── scripts/   one programs that generate every picture and video (re-runnable)
├── imgs/      screenshots rendered by those scripts
├── videos/    animations recorded by those scripts (+ a .png poster per video)
├── slides/    <name>.pptx built from imgs/ + videos/, and its exported <name>.pdf
├── tex/       LaTeX source of the paper (main.tex) and the compiled main.pdf
└── .vscode/   settings so LaTeX Workshop rebuilds the PDF on every save
```

Everything for one document lives in this one folder. Helper scripts are in the
`scripts/` folder **next to this SKILL.md** (call it `SKILL_SCRIPTS` below;
usually `%USERPROFILE%\.claude\skills\doc-maker\scripts`). Resolve it to an
absolute path once and reuse it.

Talk to the user in the language they use.

## 1. Check the environment first

Find a Python that can `import one` (try `python`, then `py -3.12`, then `py`).
Run:

```
<python> SKILL_SCRIPTS/check_env.py            # or --slides / --paper for just one part
```

For every `MISSING` line:

- **VS Code, Python packages, LaTeX, VS Code extensions**: tell the user what is
  missing, show the printed install command, and **ask whether you should
  install it**. Install only after they say yes; then re-run the check.
- **one**: same — explain it is the lab's robotics library
  (https://github.com/wanweiwei07/one), ask where to clone it, and with their
  OK run the printed `git clone … && pip install -e .`.
- **PowerPoint / LibreOffice** (needed to export slides to PDF): on Windows
  PowerPoint is preferred, but you cannot install it — ask the user to install
  Microsoft PowerPoint themselves, or offer to install LibreOffice instead. On
  Linux / macOS use LibreOffice (offer the printed install command; `sudo`
  needs the user). WPS cannot be driven from scripts, so it does not count.
- **Linux without a desktop** (SSH, servers): `one`'s off-screen rendering still
  needs an OpenGL display. Run figure scripts with `xvfb-run -a <python> …`
  (offer `sudo apt install xvfb` if missing).

`OPTION` lines are nice to have (e.g. the VS Code PDF viewer extension, needed
to view slide PDFs inside VS Code); offer them the same way.

Use the Python that passed the check for every later step.

## 2. Create the document folder

```
<python> SKILL_SCRIPTS/new_doc.py "<name>"          # add --tex when a paper is needed
```

- Name: from the user's request (short, e.g. "grasp planning"); spaces become
  `_`. If they gave none, omit it → `YYYYMMDD_document`.
- If the folder already exists the script reuses it — keep working in it, do not
  make a second one.
- Then open it in VS Code so they can watch files appear: `code <folder>`.

## 3. House style (always)

| Rule | Value |
|---|---|
| Slide text | Cover title **44 pt**; slide titles **32 pt**; body text **24 pt**; secondary text (sub-bullets, labels under pictures, captions) **20 pt**. Formulas on slides are typeset at the size of the text they belong to |
| Text inside figures | **18 pt**: plot ticks / axis labels / legends, labels drawn into diagrams or renders |
| Line width | **1.5 pt** for every line: plot curves, axes, ticks, arrows / connectors drawn on slides |
| Formulas | Typeset by **LaTeX** — in slides too. Never use PowerPoint's equation editor or Unicode pseudo-math |
| Figure size | Made at the exact size of a **HALF** slide (6.34 × 6.4 in) or a **FULL** slide (12.83 × 6.4 in) of a 16:9 deck. Try HALF first; use FULL only when the content does not fit legibly in half |
| Videos | **1280 × 720 (720p, 16:9)** by default |

The sizes and fonts live in `SKILL_SCRIPTS/figstyle.py`; `slides.py`,
`one_capture.py` and `latex_math.py` already follow them — use the helpers
rather than hand-placing things, so the rules hold automatically. Because a
figure is made at the size it is shown, 18 pt in the figure is 18 pt on the
slide (a little smaller than the 20–24 pt slide text, as it should be); do not rescale figures afterwards. Paper figures reuse the same files.

If a video cannot reasonably be 720p 16:9 (e.g. a tall robot that would be
tiny in a wide frame, or the user wants a different size), explain the problem
and ask the user what they prefer before recording at another `size=`.

## 4. Figures and videos

For every picture or video write a script in `<doc>/scripts/` (e.g.
`scripts/fig_grasp_bunny.py`) and run it **from `<doc>/scripts/`** so the
relative output paths `../imgs/…` and `../videos/…` work.

### Scenes rendered with `one`

Never call `base.run()` and always create the World with `visible=False` —
nothing should pop up on the screen.

```python
import sys; sys.path.insert(0, r"SKILL_SCRIPTS")      # absolute path
from one import ovw, ossop, osso, ouc
from one_capture import OffscreenCapture

base = ovw.World(win_size=(1280, 720), visible=False)
obj = osso.SceneObject.from_file("bunny.stl")
obj.attach_to(base.scene)
ossop.frame().attach_to(base.scene)

cap = OffscreenCapture(base, layout="half")   # "half" or "full" slide size
cap.frame(obj, view="auto")                   # camera fits the target, see below
cap.snapshot("../imgs/bunny_half.png")

def step(i):                                  # move robot / objects / camera per frame
    base.camera.orbit(angle_rad=0.02)
cap.record("../videos/bunny_orbit.mp4", n_frames=180, fps=30, step=step)
# 1280x720, re-framed for 16:9; also writes ../videos/bunny_orbit.png (poster)
```

Learn the scene API from the `one` repo itself (its `CLAUDE.md`,
`docs/API_INDEX.md`, and `examples/`) instead of guessing names. Example
scripts call `base.run()` — keep their scene setup, drop the `run()`.

### Framing rules — make the subject big

The subject the user wants to show must **fill the picture**. A far-away camera
with a tiny robot in the middle of a white image is a failure.

- Always call `cap.frame(targets, view=...)` before `snapshot`/`record`.
  `targets` = the objects / robots that matter (not the whole scene, not the
  floor or a large table unless it is the point). `fill=0.92` is the default.
- Choose `view` for what must be seen: `"auto"` picks the diagonal view with the
  largest silhouette; `"front"`, `"back"`, `"left"`, `"right"`, `"top"`,
  `"iso"`, or a 3-vector from the target toward the camera. E.g. a grasp →
  look so both fingers and the contact are visible; a planar layout → `"top"`.
- If two things must be compared, frame both together (`targets=[a, b]`).
- A tall subject suits `layout="half"` (nearly square); a wide scene suits
  `"full"`. `cap.resize(*figstyle.size_px("full"))` switches size and re-frames.
- For videos, frame on the whole motion: call `frame()` on the targets at the
  pose where they are spread out most (or frame a list of the start and end
  poses' objects), so nothing leaves the picture during the clip.
- **Look at every image you produce** (open the PNG) before using it. If the
  subject is small, cut off, hidden behind something, or the view does not show
  what the user asked about, change the view / targets and re-render.

### Plots and diagrams (matplotlib)

```python
import sys; sys.path.insert(0, r"SKILL_SCRIPTS")
import figstyle
fig, ax = figstyle.figure("half")             # 18 pt, 1.5 pt lines, LaTeX labels
ax.plot(t, q, label=r"$q_1(t)$")
ax.set_xlabel(r"$t$ [s]")
figstyle.save(fig, "../imgs/joint_traj_half.png")   # keeps the exact slide size
```

Do not override the font sizes or line widths. For many subplots use
`figstyle.figure("full", ncols=2)` etc.

## 5. Slides

Build the deck with a script `<doc>/scripts/make_slides.py` using the helper,
then export the PDF:

```python
import sys; sys.path.insert(0, r"SKILL_SCRIPTS")
from slides import Deck
deck = Deck(math_dir="../imgs/math")       # LaTeX formula images are cached here
deck.title("Grasp Planning with one", "Lab meeting · 2026-11-22")
deck.image("../imgs/scene_full.png", title="Scene")                  # one FULL figure
deck.image_text("../imgs/grasp_half.png", title="Antipodal grasp",   # HALF figure + text
                items=["contacts on opposite faces",
                       r"friction cone: $\|f_t\| \le \mu f_n$"])
deck.images(["../imgs/a_half.png", "../imgs/b_half.png"], title="Before / after",
            labels=["before", "after"])                              # two HALF figures
deck.bullets("Method", ["plain text, 24 pt", r"update: $\dot q = J^{+}(q)\,v$",
                        ["sub-bullet, 20 pt", "another"]])          # list = sub-bullets
deck.equation(r"\min_q \tfrac12\|q-q_0\|^2", title="Objective")      # display formula
deck.video("../videos/bunny_orbit.mp4", title="Orbit view")          # poster = .png
deck.save("../slides/<name>.pptx")
```

```
<python> SKILL_SCRIPTS/pptx_to_pdf.py <doc>/slides/<name>.pptx
```

- Any text with `$...$` (titles, bullets, labels, captions) is typeset by LaTeX
  as a whole line at that text's size (32 / 24 / 20 pt), so formulas look like the paper. Write normal LaTeX
  math; Chinese / Japanese text in the same line works.
- Use HALF figures with `image_text` / `images([a, b])`; FULL figures with
  `image`. Do not put a FULL-size figure into a half cell (it shrinks and the
  18 pt figure text becomes smaller) — re-make it at the right size instead.
- If you draw shapes / arrows on a slide directly with python-pptx, set
  `shape.line.width = Pt(1.5)` and use the slide text sizes above.
- Videos play in the .pptx; in the PDF they appear as their poster still.
- `pptx_to_pdf.py` uses PowerPoint on Windows and LibreOffice otherwise, both in
  the background (no window). After every change to the deck, re-run
  `make_slides.py` and `pptx_to_pdf.py` so the PDF opened in VS Code is
  current. If the PDF is open in another program that locks it, ask the user
  to close it.
- Check the result: render the PDF pages to PNG with PyMuPDF
  (`fitz.open(pdf)[i].get_pixmap(dpi=60).save(...)`) and look at them; fix
  overlaps, overflowing text or small pictures.

## 6. Paper (LaTeX)

- `new_doc.py --tex` writes a **two-column** `tex/main.tex` with
  `\graphicspath{{../imgs/}}` and two figure macros. Paper figures are the
  **same files** as the slide figures — never make separate paper versions:

  | Slide figure | In the paper | Macro |
  |---|---|---|
  | HALF-slide figure | one column (`figure`, `width=\columnwidth`) | `\halffig{bunny_half.png}{Caption.}{fig:bunny}` |
  | FULL-slide figure | across both columns (`figure*`, `width=\textwidth`) | `\fullfig{scene_full.png}{Caption.}{fig:scene}` |

  Never put a HALF figure across two columns or squeeze a FULL figure into one
  column; if a figure needs the other placement, re-make it at the other size.
  (Scaled to the column / text width, the 18 pt figure text prints at about
  9–10 pt, matching the paper.)
- If the user's venue template is single-column, use `width=\linewidth` for both
  and keep HALF figures at about half the text width (`width=0.5\linewidth`).
- Write the paper source in `tex/` (split into `sections/*.tex` with `\input`
  if long; bibliography in `tex/refs.bib`).
- Compile: `latexmk -xelatex -interaction=nonstopmode main.tex` inside `tex/`.
  For Chinese text uncomment `\usepackage[UTF8]{ctex}` (needs xelatex).
- With the LaTeX Workshop extension the `.vscode/settings.json` makes VS Code
  rebuild and refresh the PDF tab on every save — tell the user to open
  `tex/main.tex` and use "View LaTeX PDF" once.
- Fix every compile error before finishing; read `main.log` when needed.

## 7. Finish

Tell the user what was produced (paths of the .pptx / .pdf / main.pdf and the
scripts), and that any figure can be regenerated by re-running its script in
`scripts/`.
