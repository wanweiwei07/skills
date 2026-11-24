"""Find "runt" lines in a PDF: a paragraph whose last line holds only a word or
two and is mostly empty. Works on the paper (tex/main.pdf) and on the slide
PDF (slides/<name>.pdf).

    python check_lines.py ../tex/main.pdf        # paper: flags last lines < 1/3 full
    python check_lines.py ../slides/talk.pdf     # slides (landscape pages): < 1/2 full

Each hit prints the page, how full the last line is, and its text. Fix it by
rewording the paragraph / bullet (drop a redundant word, use a shorter
phrase) so the leftover pulls up into the line above. Never fix it by
shrinking the font, squeezing the margins or adding \\vspace.
Exit code 1 if anything was found.
"""
import argparse
import sys

PAPER_MIN = 1 / 3    # paper: a last line less than a third full is a runt
SLIDE_MIN = 1 / 2    # slides: a wrapped line less than half full is a runt


def _blocks(page):
    """{block: [[x0, x1, y_bottom, text, height]]} built from word boxes, words
    on the same baseline merged into one row, rows sorted top-down."""
    blocks = {}
    for x0, y0, x1, y1, word, bno, _lno, _wno in page.get_text("words"):
        rows = blocks.setdefault(bno, [])
        for r in rows:
            if abs(r[2] - y1) < (y1 - y0) * 0.4:      # same baseline
                r[0], r[1] = min(r[0], x0), max(r[1], x1)
                r[3].append((x0, word))
                break
        else:
            rows.append([x0, x1, y1, [(x0, word)], y1 - y0])
    for rows in blocks.values():
        for r in rows:
            r[3] = " ".join(w for _, w in sorted(r[3]))
        rows.sort(key=lambda r: r[2])
    return blocks


def runts_in_page(page, min_frac=None):
    """[(frac, text, previous line)] for one fitz page."""
    if min_frac is None:
        min_frac = SLIDE_MIN if page.rect.width > page.rect.height else PAPER_MIN
    hits = []
    for rows in _blocks(page).values():
        if len(rows) < 2:
            continue
        left = min(r[0] for r in rows)
        width = max(r[1] for r in rows) - left
        if width <= 0:
            continue
        for prev, cur in zip(rows, rows[1:]):
            if cur[2] - prev[2] > prev[4] * 1.8:     # gap: not the same paragraph
                continue
            prev_full = (prev[1] - left) / width > 0.9
            frac = (cur[1] - cur[0]) / width
            if prev_full and frac < min_frac:
                hits.append((frac, cur[3], prev[3]))
    return hits


def check(pdf, min_frac=None):
    """[(page_no starting at 1, frac, text, previous line)]."""
    import fitz
    out = []
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc):
            for frac, text, prev in runts_in_page(page, min_frac):
                out.append((i + 1, frac, text, prev))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf")
    ap.add_argument("--min", type=float, default=None,
                    help="flag a last line filled less than this fraction "
                         "(default 1/2 on slide pages, 1/3 on paper pages)")
    a = ap.parse_args()
    hits = check(a.pdf, a.min)
    for page, frac, text, prev in hits:
        print(f"page {page}: last line {frac:4.0%} full: '{text}'   (after: '...{prev[-40:]}')")
    print(f"{len(hits)} short line(s) found" if hits else "no short lines")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
