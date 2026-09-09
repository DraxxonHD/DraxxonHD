#!/usr/bin/env python3
"""Regenerate assets/languages.svg and assets/stats.svg from what GitHub reports.

Run it whenever the repo list changes:

    gh auth status && python scripts/gen-languages.py

It shells out to `gh api`, so it uses the authenticated rate limit. Forks and the profile
repo itself are skipped. The output is a plain static SVG committed to the repo, which is
the whole point: no live widget, nothing that rots when someone else's server goes away.
"""
import json
import pathlib
import subprocess
import sys

from gen_sections import oldest as oldest_commit

OWNER = "DraxxonHD"
SKIP = {OWNER}
TOP = 8
IGNORE = {"Batchfile", "Shell", "Makefile", "Dockerfile", "Roff"}
SHADES = ["#C1121F", "#9A2028", "#7C2A30", "#653036",
          "#55343A", "#4A363C", "#42383E", "#3C393F"]


def gh(path):
    """Call `gh api --paginate` and stitch the concatenated JSON documents back together."""
    out = subprocess.run(["gh", "api", path, "--paginate"],
                         capture_output=True, text=True, check=True).stdout
    chunks, depth, start = [], 0, None
    for i, ch in enumerate(out):
        if ch in "[{":
            if depth == 0:
                start = i
            depth += 1
        elif ch in "]}":
            depth -= 1
            if depth == 0:
                chunks.append(json.loads(out[start:i + 1]))
    if not chunks:
        return []
    if isinstance(chunks[0], list):
        return [x for c in chunks for x in c]
    merged = {}
    for c in chunks:
        for k, v in c.items():
            merged[k] = merged.get(k, 0) + v
    return merged


def build_svg(ranked, grand, repo_count):
    row_h, top, left, bar_x, bar_w = 28, 78, 32, 140, 340
    height = top + row_h * len(ranked) + 34
    widest = ranked[0][1]

    rows = []
    for i, (lang, size) in enumerate(ranked):
        y = top + i * row_h
        w = max(3, round(bar_w * size / widest))
        pct = 100 * size / grand
        rows.append(
            '    <text class="mono lang" x="%d" y="%d">%s</text>' % (left, y + 13, lang.lower()))
        rows.append(
            '    <rect x="%d" y="%d" width="%d" height="17" fill="%s"/>' % (bar_x, y, w, SHADES[i]))
        rows.append(
            '    <text class="mono pct" x="%d" y="%d" text-anchor="end">%.1f%%</text>'
            % (bar_x + bar_w + 88, y + 13, pct))

    label = ", ".join("%s %.0f percent" % (l, 100 * s / grand) for l, s in ranked)
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 {h}" width="600" height="{h}" role="img" aria-label="Bar chart of languages by bytes across my public repositories: {label}.">
  <title>languages by bytes across my public repos</title>
  <style>
    .bg {{ fill: #0B0B0D; }}
    .edge {{ fill: none; stroke: #3A0D12; stroke-width: 1; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", monospace; font-size: 17px; }}
    .lang {{ fill: #E8E6E3; }}
    .pct {{ fill: #8E8E96; }}
    .prompt {{ fill: #4FE07A; }}
    .cmd {{ fill: #E8E6E3; }}
    .note {{ fill: #8E8E96; font-size: 12.5px; }}
  </style>
  <rect class="bg" x="0" y="0" width="600" height="{h}" rx="12"/>
  <rect class="edge" x="8.5" y="8.5" width="583" height="{inner}" rx="10"/>
  <text class="mono prompt" x="32" y="44">$</text>
  <text class="mono cmd" x="52" y="44">cloc ~/repos --by-language</text>
  <line x1="32" y1="60" x2="568" y2="60" stroke="#3A0D12" stroke-width="1"/>
{rows}
  <text class="mono note" x="32" y="{note_y}">bytes across {repos} repos. yes, c++ is last. university picked this list, not me.</text>
</svg>
""".format(h=height, inner=height - 17, label=label, rows="\n".join(rows),
           note_y=height - 14, repos=repo_count)


def build_stats(repos, totals):
    """A second panel: the numbers behind the chart, in the same terminal frame."""
    stars = sum(r["stargazers_count"] for r in repos)
    forks = sum(r["forks_count"] for r in repos)
    first = oldest_commit()["date"][:4]      # created_at lies, the repos were recreated in one batch
    latest = max(r["pushed_at"][:10] for r in repos)
    megabytes = sum(totals.values()) / 1_000_000

    rows = [
        ("repos",     "%d public" % len(repos)),
        ("languages", "%d, and one of them is a build system" % len(totals)),
        ("code",      "%.1f MB, most of it coursework" % megabytes),
        ("stars",     "none yet, the bar is on the floor" if stars == 0
                      else "%d, mostly from people I know" % stars if stars < 20
                      else "%d" % stars),
        ("since",     first),
        ("last push", latest),
    ]
    if forks:
        rows.insert(4, ("forks", "%d" % forks))

    top, row_h = 78, 30
    height = top + row_h * len(rows) + 26
    body = []
    for i, (key, value) in enumerate(rows):
        y = top + i * row_h
        body.append('    <text class="mono" x="32" y="%d"><tspan class="key">%s</tspan>'
                    '<tspan class="dots"> %s </tspan><tspan class="val">%s</tspan></text>'
                    % (y, key, "." * max(2, 13 - len(key)), value))

    label = "; ".join("%s %s" % (k, v) for k, v in rows)
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 {h}" width="600" height="{h}" role="img" aria-label="A terminal panel of numbers about my public repositories: {label}.">
  <title>the numbers</title>
  <style>
    .bg {{ fill: #0B0B0D; }}
    .edge {{ fill: none; stroke: #3A0D12; stroke-width: 1; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", monospace; font-size: 17px; }}
    .key {{ fill: #E0434E; }}
    .dots {{ fill: #5A1620; }}
    .val {{ fill: #E8E6E3; }}
    .prompt {{ fill: #4FE07A; }}
    .cmd {{ fill: #E8E6E3; }}
    .note {{ fill: #8E8E96; font-size: 12.5px; }}
  </style>
  <rect class="bg" x="0" y="0" width="600" height="{h}" rx="12"/>
  <rect class="edge" x="8.5" y="8.5" width="583" height="{inner}" rx="10"/>
  <text class="mono prompt" x="32" y="44">$</text>
  <text class="mono cmd" x="52" y="44">gh api me --numbers</text>
  <line x1="32" y1="60" x2="568" y2="60" stroke="#3A0D12" stroke-width="1"/>
{body}
  <text class="mono note" x="32" y="{note}">counted straight from the API, not from a badge on someone else's server.</text>
</svg>
""".format(h=height, inner=height - 18, body=chr(10).join(body), note=height - 18, label=label)


def main():
    repos = [r for r in gh("users/%s/repos?per_page=100" % OWNER)
             if not r["fork"] and r["name"] not in SKIP]
    totals = {}
    for r in repos:
        for lang, size in gh("repos/%s/%s/languages" % (OWNER, r["name"])).items():
            if lang not in IGNORE:
                totals[lang] = totals.get(lang, 0) + size

    if not totals:
        sys.exit("no language data came back")

    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:TOP]
    out = pathlib.Path(__file__).resolve().parent.parent / "assets" / "languages.svg"
    out.write_text(build_svg(ranked, sum(totals.values()), len(repos)), encoding="utf-8")
    print("wrote %s (%d languages, %d repos)" % (out, len(ranked), len(repos)))

    stats = out.parent / "stats.svg"
    stats.write_text(build_stats(repos, totals), encoding="utf-8")
    print("wrote %s" % stats)


if __name__ == "__main__":
    main()
