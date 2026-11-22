"""Create (or reuse) the document folder  <cwd>/YYYYMMDD_<name>/ .

    python new_doc.py "grasp planning report"        -> 20261122_grasp_planning_report/
    python new_doc.py                                -> 20261122_document/
    python new_doc.py "my paper" --tex               -> also writes tex/main.tex
    python new_doc.py "x" --date 20261120            -> explicit date

Prints the absolute path of the folder on the last line.
"""
import argparse
import datetime
import json
import os
import re

SUBDIRS = ("scripts", "imgs", "videos", "slides", "tex")

MAIN_TEX = r"""\documentclass[11pt]{article}
\usepackage[a4paper,margin=2.5cm]{geometry}
\usepackage{graphicx}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
%% Chinese text: compile with xelatex and uncomment the next line
%% \usepackage[UTF8]{ctex}
\graphicspath{{../imgs/}}

\title{%(title)s}
\author{}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
\end{abstract}

\section{Introduction}

\end{document}
"""

# LaTeX Workshop: rebuild on every save, show the PDF in a VS Code tab
VSCODE_SETTINGS = {
    "latex-workshop.latex.autoBuild.run": "onSave",
    "latex-workshop.latex.recipe.default": "latexmk (xelatex)",
    "latex-workshop.view.pdf.viewer": "tab",
    "latex-workshop.latex.autoClean.run": "onBuilt",
}


def slug(name):
    s = re.sub(r"[\\/:*?\"<>|]+", "", name.strip())
    s = re.sub(r"\s+", "_", s)
    return s or "document"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", nargs="?", default="document")
    ap.add_argument("--tex", action="store_true", help="write tex/main.tex skeleton")
    ap.add_argument("--date", default=None, help="YYYYMMDD, default today")
    ap.add_argument("--root", default=os.getcwd())
    a = ap.parse_args()

    date = a.date or datetime.date.today().strftime("%Y%m%d")
    root = os.path.abspath(os.path.join(a.root, f"{date}_{slug(a.name)}"))
    existed = os.path.isdir(root)
    for d in SUBDIRS:
        os.makedirs(os.path.join(root, d), exist_ok=True)

    vs_dir = os.path.join(root, ".vscode")
    vs_file = os.path.join(vs_dir, "settings.json")
    if not os.path.exists(vs_file):
        os.makedirs(vs_dir, exist_ok=True)
        with open(vs_file, "w", encoding="utf-8") as f:
            json.dump(VSCODE_SETTINGS, f, indent=2)

    if a.tex:
        main_tex = os.path.join(root, "tex", "main.tex")
        if not os.path.exists(main_tex):
            with open(main_tex, "w", encoding="utf-8") as f:
                f.write(MAIN_TEX % {"title": a.name if a.name != "document" else "Document"})

    print(("reused existing folder: " if existed else "created: ") + root)
    print(root)


if __name__ == "__main__":
    main()
