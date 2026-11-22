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

## 3. Figures and videos with `one`

For every picture or video write a script in `<doc>/scripts/` (e.g.
`scripts/fig_grasp_bunny.py`) and run it **from `<doc>/scripts/`** so the
relative output paths `../imgs/…` and `../videos/…` work. Never call
`base.run()` and always create the World with `visible=False` — nothing should
pop up on the screen.

```python
import sys; sys.path.insert(0, r"SKILL_SCRIPTS")      # absolute path
from one import ovw, ossop, osso, ouc
from one_capture import OffscreenCapture

base = ovw.World(win_size=(1920, 1080), visible=False)
obj = osso.SceneObject.from_file("bunny.stl")
obj.attach_to(base.scene)
ossop.frame().attach_to(base.scene)

cap = OffscreenCapture(base)
cap.frame(obj, view="auto")            # camera fits the target, see below
cap.snapshot("../imgs/bunny.png")      # auto-crops empty background

def step(i):                           # move robot / objects / camera per frame
    base.camera.orbit(angle_rad=0.02)
cap.record("../videos/bunny_orbit.mp4", n_frames=180, fps=30, step=step)
# also writes ../videos/bunny_orbit.png (poster: shown in slides PDF)
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
- `snapshot()` crops the leftover background automatically; keep it on.
- Pick `win_size` with the shape of where the image goes: a single slide
  picture → about 1920×1000 (wide); a paper figure column → about 1200×900;
  two side-by-side slide pictures → about 1000×1000 each.
- For videos, frame on the whole motion: call `frame()` on the targets at the
  pose where they are spread out most (or frame a list of the start and end
  poses' objects), so nothing leaves the picture during the clip.
- **Look at every image you produce** (open the PNG) before using it. If the
  subject is small, cut off, hidden behind something, or the view does not show
  what the user asked about, change the view / targets and re-render.

## 4. Slides

Build the deck with a script `<doc>/scripts/make_slides.py` using the helper,
then export the PDF:

```python
import sys; sys.path.insert(0, r"SKILL_SCRIPTS")
from slides import Deck
deck = Deck()
deck.title("Grasp Planning with one", "Lab meeting · 2026-11-22")
deck.image("../imgs/bunny.png", title="Antipodal grasps")            # fills the slide
deck.images(["../imgs/a.png", "../imgs/b.png"], title="Before / after",
            labels=["before", "after"])                               # 1-4 pictures
deck.video("../videos/bunny_orbit.mp4", title="Orbit view")           # poster = .png
deck.bullets("Summary", ["…", "…"])
deck.save("../slides/<name>.pptx")
```

```
<python> SKILL_SCRIPTS/pptx_to_pdf.py <doc>/slides/<name>.pptx
```

- Pictures and videos are scaled as large as the slide allows; keep at most a
  short title and caption so they stay big. Prefer one strong picture per slide
  over many small ones.
- Videos play in the .pptx; in the PDF they appear as their poster still.
- `pptx_to_pdf.py` uses PowerPoint on Windows and LibreOffice otherwise, both in
  the background (no window). After every change to the deck, re-run
  `make_slides.py` and `pptx_to_pdf.py` so the PDF opened in VS Code is
  current. If the PDF is open in another program that locks it, ask the user
  to close it.
- Check the result: render a couple of PDF pages to PNG (e.g. with PyMuPDF if
  installed) or open the PDF, and fix overlaps or small pictures.

## 5. Paper (LaTeX)

- `new_doc.py --tex` writes `tex/main.tex`; `\graphicspath{{../imgs/}}` is set,
  so use `\includegraphics[width=\linewidth]{bunny.png}`.
- Write the paper source in `tex/` (split into `sections/*.tex` with `\input`
  if long; bibliography in `tex/refs.bib`).
- Compile: `latexmk -xelatex -interaction=nonstopmode main.tex` inside `tex/`.
  For Chinese text uncomment `\usepackage[UTF8]{ctex}` (needs xelatex).
- With the LaTeX Workshop extension the `.vscode/settings.json` makes VS Code
  rebuild and refresh the PDF tab on every save — tell the user to open
  `tex/main.tex` and use "View LaTeX PDF" once.
- Fix every compile error before finishing; read `main.log` when needed.

## 6. Finish

Tell the user what was produced (paths of the .pptx / .pdf / main.pdf and the
scripts), and that any figure can be regenerated by re-running its script in
`scripts/`.
