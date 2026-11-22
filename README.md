<div align="center">

# Claude Skills

**English** · [日本語](README.ja.md) · [中文](README.zh.md)

</div>

Skills for [Claude Code](https://claude.com/claude-code) used in our lab. A skill
is a folder of instructions and scripts that teaches Claude a workflow; once
installed, Claude uses it automatically when your request matches.

| Skill | What it does |
|---|---|
| [doc-maker](doc-maker/) | Makes slides (PowerPoint + PDF) and papers (LaTeX). Figures and videos are rendered with the [one](https://github.com/wanweiwei07/one) robotics library, everything goes into one dated folder, and you watch the results update in VS Code. |

## 1. Install

Claude Code reads personal skills from a folder named `.claude/skills` inside
your **home folder** (the folder that belongs to your user account):

| OS | Home folder | Skills folder |
|---|---|---|
| Windows | `C:\Users\<your user name>` | `C:\Users\<your user name>\.claude\skills` |
| Linux (Ubuntu) | `/home/<your user name>` (written `~`) | `/home/<your user name>/.claude/skills` |
| macOS | `/Users/<your user name>` (written `~`) | `/Users/<your user name>/.claude/skills` |

The `.claude` and `skills` folders may not exist yet — that is fine, the
command below creates them.

### Windows

1. Open **PowerShell** (Start menu → type `PowerShell`).
2. Paste and run:

   ```powershell
   git clone https://github.com/wanweiwei07/skills "$env:USERPROFILE\.claude\skills"
   ```

   `$env:USERPROFILE` is a built-in Windows variable that always points to
   your home folder, e.g. `C:\Users\taro`. Run `echo $env:USERPROFILE` to see
   yours.
3. Check: `dir "$env:USERPROFILE\.claude\skills\doc-maker"` should list `SKILL.md`.
   (In Explorer, type `%USERPROFILE%\.claude\skills` in the address bar.)

### Linux (Ubuntu) / macOS

1. Open a **Terminal** (Ubuntu: `Ctrl+Alt+T`).
2. Paste and run:

   ```bash
   git clone https://github.com/wanweiwei07/skills ~/.claude/skills
   ```

   `~` means your home folder, e.g. `/home/taro`. Run `echo ~` to see yours.
3. Check: `ls ~/.claude/skills/doc-maker` should list `SKILL.md`.
   `.claude` starts with a dot, so it is **hidden**: use `ls -a ~`, or press
   `Ctrl+H` in the Ubuntu file manager to see it.

No `git`? Windows: `winget install Git.Git`; Ubuntu: `sudo apt install git`.
Or click **Code → Download ZIP** on GitHub, unzip, and copy the `doc-maker`
folder into the skills folder from the table above (create the folders if needed).

**Already have a `skills` folder** with your own skills? Then `git clone` will
refuse. Clone somewhere else and copy the `doc-maker` folder into your skills folder.

**Update** later:

```powershell
git -C "$env:USERPROFILE\.claude\skills" pull      # Windows
```

```bash
git -C ~/.claude/skills pull                       # Linux / macOS
```

Restart Claude Code after installing or updating.

## 2. Use

Open a terminal in the folder where the document should be created (or open
that folder in VS Code and start Claude Code there) and just ask, e.g.

- "Make slides about antipodal grasp planning on the bunny, with a video of the robot."
- "Render the robot from the front and from the top and put both in a slide."
- "Write a paper draft about this experiment, with figures made with one."

Claude creates `YYYYMMDD_<name>/` in the current folder (`YYYYMMDD_document`
if you give no name):

```
20261122_grasp_planning/
├── scripts/   one programs that produce each figure / video (re-run to regenerate)
├── imgs/      screenshots (rendered off screen, auto-framed so the subject is big)
├── videos/    animations (.mp4) + a poster image for each
├── slides/    <name>.pptx and the exported <name>.pdf
└── tex/       main.tex (paper source) and main.pdf
```

Keep the PDFs open in VS Code: slides are re-exported after each change, and
the LaTeX PDF is rebuilt every time you save `main.tex`.

## 3. Requirements

At the start Claude runs a check (`doc-maker/scripts/check_env.py`). For anything
missing it shows the install command and **asks you before installing**. You
can also install things yourself:

| Needed for | Windows | Linux (Ubuntu) | macOS |
|---|---|---|---|
| Python ≥ 3.12 | python.org or `winget install Python.Python.3.12` | `sudo apt install python3.12 python3.12-venv` | `brew install python@3.12` |
| one | see below | see below | see below |
| VS Code | `winget install Microsoft.VisualStudioCode` | `sudo snap install code --classic` | `brew install --cask visual-studio-code` |
| Python packages | `pip install python-pptx pillow imageio imageio-ffmpeg pywin32` | `pip install python-pptx pillow imageio imageio-ffmpeg` | same as Linux |
| Slides → PDF | **Microsoft PowerPoint** (install it yourself), or LibreOffice: `winget install TheDocumentFoundation.LibreOffice` | **LibreOffice**: `sudo apt install libreoffice-impress` | LibreOffice: `brew install --cask libreoffice` |
| Paper (LaTeX) | MiKTeX `winget install MiKTeX.MiKTeX` or TeX Live | `sudo apt install texlive-xetex texlive-lang-cjk latexmk` | `brew install --cask mactex-no-gui` |
| VS Code extensions | `code --install-extension james-yu.latex-workshop` and `code --install-extension tomoki1207.pdf` | same | same |

Notes:

- **Office on Linux:** use LibreOffice. WPS can open the .pptx but cannot be
  driven from scripts, so it cannot export the PDF automatically.
- **Linux without a desktop (SSH / server):** rendering needs an OpenGL display;
  install `xvfb` (`sudo apt install xvfb`) — Claude then runs figure scripts with
  `xvfb-run`.
- PowerPoint cannot be installed by Claude; everything else can, with your OK.

### Installing one manually

```bash
git clone https://github.com/wanweiwei07/one.git
cd one
python -m venv venv                # optional but recommended
venv\Scripts\activate              # Windows   (Linux/macOS: source venv/bin/activate)
pip install -e .
```

Use the same Python (or venv) when you work with Claude, so that `import one`
works. Check with `python -c "import one; print(one.__file__)"`.

## 4. Troubleshooting

| Problem | Fix |
|---|---|
| Claude does not use the skill | Check that `SKILL.md` is at `<skills folder>/doc-maker/SKILL.md` (not nested one level deeper), then restart Claude Code. You can also say "use the doc-maker skill". |
| `import one` fails | Activate the venv where one is installed, or tell Claude which Python to use. |
| PDF export fails | Close the deck if it is open in PowerPoint / LibreOffice and ask again. |
| Black or empty images on Linux | Update the GPU driver, or run under `xvfb-run`. |

## Adding a new skill (maintainers)

Create a new folder next to `doc-maker/` with its own `SKILL.md`, add it to the
table at the top of all three READMEs, commit and push. Students get it with
`git pull`.
