#!/usr/bin/env python3
"""review_page.py — build the "Needs your review" pages, readable on a phone.

Every gate file under design/gates/ whose Status line says awaiting_signoff
becomes a card on design/review/index.html, plus every needs_user entry in
design/status.json. Gate records and the markdown files they link to are
rendered to HTML under design/review/doc/ (mirroring repo paths, so relative
links and images keep working); linked images and PDFs are copied alongside.
Plain-language notes, written by hand, go in design/review/notes/:
  <variant>-phase<N>.md   shown on that gate's card
  <variant>.md            shown on every card of that variant

The main page (index.html) gets a banner between the review-banner markers
naming how many sign-offs are waiting.

Usage:
  python3 scripts/review_page.py              # build into this checkout
  python3 scripts/review_page.py --ghp build/ghp
                                              # also copy into the gh-pages tree
Run it at every gate (the pcb-design skill's LESSONS.md says so).
"""
import argparse
import html
import json
import os
import re
import shutil
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
GATES = ROOT / "design" / "gates"
OUT = ROOT / "design" / "review"
DOC = OUT / "doc"
NOTES = OUT / "notes"
STATUS = ROOT / "design" / "status.json"
REPO_URL = "https://github.com/sequoia-hope/matrix-play/blob/main/"
COPY_EXT = {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".pdf"}
COPY_MAX = 10 * 1024 * 1024
BANNER_START = "<!-- review-banner:start -->"
BANNER_END = "<!-- review-banner:end -->"

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--line:#e2e5ea;--fg:#14171c;--muted:#5b6472;
--accent:#2f6feb;--warn:#a86814;--chip:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#0d1015;--card:#161b22;--line:#262d38;
--fg:#e6eaf0;--muted:#8c96a6;--accent:#5b9bff;--warn:#dfa543;--chip:#202632}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.55 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
-webkit-text-size-adjust:100%;overflow-wrap:anywhere}
.wrap{max-width:860px;margin:0 auto;padding:1rem}
a{color:var(--accent)}
h1{font-size:1.45rem;margin:.4rem 0 .2rem}
h2{font-size:1.2rem;margin:1.4rem 0 .4rem}
h3{font-size:1.05rem;margin:1.1rem 0 .3rem}
.muted{color:var(--muted);font-size:.92rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;
padding:.9rem 1rem;margin:1rem 0}
.card h2{margin-top:.2rem}
.chip{display:inline-block;background:var(--chip);border-radius:999px;padding:.05rem .6rem;
font-size:.8rem;margin-right:.3rem}
.chip.warn{color:var(--warn);font-weight:600}
.links a{display:inline-block;margin:.25rem .9rem .25rem 0}
.decide{border-left:3px solid var(--warn);padding-left:.8rem;margin:.8rem 0}
img{max-width:100%;height:auto;border-radius:8px;background:#fff}
.tbl{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:.6rem 0}
table{border-collapse:collapse;font-size:.88rem}
th,td{border:1px solid var(--line);padding:.3rem .45rem;vertical-align:top}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;
background:var(--chip);border-radius:4px;padding:0 .2em}
pre{overflow-x:auto;background:var(--chip);padding:.6rem;border-radius:8px;font-size:.8rem}
pre code{background:none;padding:0}
ul,ol{padding-left:1.3rem}
nav.top{font-size:.92rem;margin-bottom:.5rem}
"""


def page(title, body, home):
    return (f"<!doctype html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width, initial-scale=1'>"
            f"<title>{html.escape(title)}</title><style>{CSS}</style></head><body>"
            f"<div class=wrap><nav class=top><a href='{home}index.html'>&larr; Main page</a>"
            f" &middot; <a href='{home}design/review/index.html'>Needs your review</a></nav>"
            f"{body}</div></body></html>\n")


def home_prefix(rel_html: Path) -> str:
    """Relative path from a page at repo path rel_html back to the repo root."""
    return "../" * (len(rel_html.parts) - 1)


def repo_rel(target: str, src: Path):
    """Resolve a markdown link target (relative to repo file src) to a repo path, or None."""
    if re.match(r"^[a-z]+:", target) and not target.startswith("file://"):
        return None
    if target.startswith("file://"):
        p = Path(target[len("file://"):])
    else:
        p = (ROOT / src).parent / target
    try:
        return Path(os.path.normpath(p)).relative_to(ROOT)
    except ValueError:
        return None


def render_md(text, src: Path, out_rel: Path, queue, depth):
    """Markdown -> HTML. Links to repo .md become rendered pages (queued) when depth allows,
    linked images/PDFs are copied next to the rendered page, anything else goes to GitHub."""
    out_dir = out_rel.parent

    def fix(m):
        label, target = m.group(1), m.group(2)
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        if not target:
            return m.group(0)
        rel = repo_rel(target, src)
        if rel is None:
            return m.group(0)
        full = ROOT / rel
        if rel.suffix == ".md" and full.is_file() and depth < 1:
            queue.append((rel, depth + 1))
            dest = Path("design/review/doc") / rel.with_suffix(".html")
        elif rel.suffix.lower() in COPY_EXT and full.is_file() and full.stat().st_size <= COPY_MAX:
            dest = Path("design/review/doc") / rel
            (ROOT / dest).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(full, ROOT / dest)
        else:
            return f"[{label}]({REPO_URL}{rel.as_posix()}{anchor})"
        return f"[{label}]({os.path.relpath(dest, out_dir)}{anchor})"

    text = re.sub(r"(?<!\\)\[([^\]]*)\]\(([^)\s]+)\)", fix, text)
    out = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    return out.replace("<table>", "<div class=tbl><table>").replace("</table>", "</table></div>")


def render_doc(rel: Path, depth, queue, done):
    if rel in done:
        return
    done.add(rel)
    out_rel = Path("design/review/doc") / rel.with_suffix(".html")
    text = (ROOT / rel).read_text()
    body = (f"<p class=muted>Source: <a href='{REPO_URL}{rel.as_posix()}'>{rel.as_posix()}</a></p>"
            + render_md(text, rel, out_rel, queue, depth))
    title = next((l.lstrip("# ").strip() for l in text.splitlines() if l.startswith("#")), rel.name).replace("`", "")
    (ROOT / out_rel).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / out_rel).write_text(page(title, body, home_prefix(out_rel)))


def decision_section(text):
    """The gate's 'questions for the user' section: heading mentions user + sign-off/decision."""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if re.match(r"^##+ ", l) and re.search(r"(?i)(user|sign-?off)", l) and \
                re.search(r"(?i)(question|decision|sign-?off)", l) and "Checklist" not in l:
            level = len(l) - len(l.lstrip("#"))
            j = i + 1
            while j < len(lines) and not (re.match(r"^#+ ", lines[j]) and
                                          len(lines[j]) - len(lines[j].lstrip("#")) <= level):
                j += 1
            return l.lstrip("# ").strip(), "\n".join(lines[i + 1:j]).strip()
    return None, None


def pending_gates():
    out = []
    for f in GATES.rglob("phase*.md"):
        text = f.read_text()
        status = next((l for l in text.splitlines() if l.startswith("Status:")), "")
        if "awaiting_signoff" not in status:
            continue
        variant = f.parent.name if f.parent != GATES else ""
        num = int(re.search(r"phase(\d+)", f.name).group(1))
        out.append((f.parent.stat().st_mtime, variant, num, f, text))
    # newest variant first, gates in order within a variant
    newest = {}
    for m, v, *_ in out:
        newest[v] = max(newest.get(v, 0), m)
    out.sort(key=lambda t: (-newest[t[1]], t[1], t[2]))
    return out


def build():
    # rendered pages are overwritten in place; nothing is deleted
    DOC.mkdir(parents=True, exist_ok=True)
    queue, done = [], set()
    cards = []
    for _, variant, num, f, text in pending_gates():
        rel = f.relative_to(ROOT)
        render_doc(rel, 0, queue, done)
        out_rel = Path("design/review/index.html")
        title = text.splitlines()[0].lstrip("# ").strip().replace("`", "")
        notes = ""
        for n in (NOTES / f"{variant}.md", NOTES / f"{variant}-phase{num}.md"):
            if n.is_file():
                notes += render_md(n.read_text(), n.relative_to(ROOT), out_rel, queue, 0)
        head, sect = decision_section(text)
        decide = ""
        if sect:
            decide = (f"<div class=decide><h3>{html.escape(head)}</h3>"
                      + render_md(sect, rel, out_rel, queue, 0) + "</div>")
        links = [f"<a href='doc/{rel.with_suffix('.html').as_posix()}'>Full gate record</a>"]
        if variant and (ROOT / "viewer" / f"{variant}.html").is_file():
            links.append(f"<a href='../../viewer/{variant}.html'>Board viewer</a>")
        cards.append(
            f"<section class=card id='{variant}-g{num}'>"
            f"<span class='chip warn'>Gate {num} &middot; awaiting your sign-off</span>"
            f"<span class=chip>{html.escape(variant or 'main board')}</span>"
            f"<h2>{html.escape(title)}</h2>{notes}{decide}"
            f"<div class=links>{''.join(links)}</div></section>")
    while queue:
        rel, depth = queue.pop(0)
        render_doc(rel, depth, queue, done)

    needs = json.loads(STATUS.read_text()).get("needs_user", [])
    qs = []
    for n in needs:
        opts = "".join(f"<li>{html.escape(o)}</li>" for o in n.get("options", []))
        qs.append(f"<section class=card><span class=chip>{html.escape(n.get('kind', ''))}</span>"
                  f"<span class=chip>gate {n.get('gate', '?')}</span>"
                  f"<p>{html.escape(n.get('text', ''))}</p>"
                  + (f"<ol>{opts}</ol>" if opts else "") + "</section>")

    body = (f"<h1>Needs your review</h1>"
            f"<p class=muted>{len(cards)} gate sign-offs and {len(qs)} open questions. "
            f"Built by <code>scripts/review_page.py</code> from the gate records and "
            f"<code>design/status.json</code>. Reply in the chat with your choices.</p>"
            f"<h2>Gate sign-offs</h2>" + ("".join(cards) or "<p>None.</p>")
            + "<h2>Open questions</h2>" + ("".join(qs) or "<p>None.</p>"))
    (OUT / "index.html").write_text(page("Needs your review", body, "../../"))
    return len(cards), len(qs)


def banner(index: Path, n_gates, n_qs):
    text = index.read_text()
    total = n_gates + n_qs
    if total:
        inner = (f"<a href='design/review/index.html' style='display:block;margin:.8rem auto;"
                 f"max-width:1200px;padding:.75rem 1rem;border-radius:12px;border:2px solid var(--warn);"
                 f"background:var(--card);color:var(--fg);font-weight:600;text-decoration:none'>"
                 f"&#9888; Needs your review: {n_gates} gate sign-offs, {n_qs} open questions "
                 f"&rarr;</a>")
    else:
        inner = ""
    block = f"{BANNER_START}{inner}{BANNER_END}"
    if BANNER_START in text:
        text = re.sub(re.escape(BANNER_START) + ".*?" + re.escape(BANNER_END), lambda _: block,
                      text, flags=re.S)
    else:
        text = text.replace("  <main>\n", f"  {block}\n  <main>\n", 1)
        if block not in text:
            raise SystemExit(f"{index}: no <main> to put the review banner before")
    index.write_text(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ghp", help="gh-pages worktree to copy design/review/ and the banner into")
    a = ap.parse_args()
    n_gates, n_qs = build()
    banner(ROOT / "index.html", n_gates, n_qs)
    print(f"design/review/index.html: {n_gates} gate sign-offs, {n_qs} open questions")
    if a.ghp:
        ghp = Path(a.ghp).resolve()
        dst = ghp / "design" / "review"
        shutil.copytree(OUT, dst, ignore=shutil.ignore_patterns("notes"), dirs_exist_ok=True)
        banner(ghp / "index.html", n_gates, n_qs)
        print(f"copied into {dst}")


if __name__ == "__main__":
    main()
