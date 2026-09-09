#!/usr/bin/env python3
"""Draw the terminal panels the README is built from.

    gh auth status && python3 scripts/gen_sections.py

Writes seven files into assets/. Four carry numbers from the API and draw them rather than
listing them: commits.svg is a bar per weekday, timeline.svg a year axis, housekeeping.svg
two ratio bars, tour.svg a bar per shelf. The other three carry written content: fun.svg,
setup.svg and status.svg.

Why SVG and not a fenced code block: a fence cannot shrink. On a phone it holds about forty
monospace characters and anything longer needs a sideways swipe, so a fence beside a floated
image is unreadable there. An SVG scales to whatever column it is given, which is what lets
these panels sit next to a picture in one centred paragraph and stack on a narrow screen.

What decides legibility is font size divided by viewBox width, not the width attribute in
the README. 17 over 520 is 3.3 per cent, which clears 11 pixels on a 390 pixel screen.
"""
import collections
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime

OWNER = "DraxxonHD"
SKIP = {OWNER}
W = 520
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"

BG, EDGE, KEY, VAL, DOTS = "#0B0B0D", "#3A0D12", "#E0434E", "#E8E6E3", "#5A1620"
GREEN, NOTE, MUTE = "#4FE07A", "#8E8E96", "#42383E"
SHADES = ["#C1121F", "#9A2028", "#7C2A30", "#653036", "#55343A", "#4A363C", "#3C393F"]

# Which shelf a repo lands on, by the language GitHub calls primary. The blurb is mine, the
# count is not.
BUCKETS = [
    ("android", {"Kotlin"},                     "Compose, one casino app"),
    ("backend", {"Java", "PHP", "TypeScript",
                 "JavaScript"},                 "Spring, Ktor, Express, PHP"),
    ("cpp",     {"C++", "C"},                   "patterns, SIMD, a cinema"),
    ("unity",   {"C#", "ShaderLab"},            "a reverse tower defence"),
    ("ml",      {"Python", "Jupyter Notebook"}, "a Transformer by hand"),
    ("web",     {"HTML", "CSS", "Vue"},         "where all of this started"),
]


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
    return [x for c in chunks for x in c] if isinstance(chunks[0], list) else chunks[0]


def repos():
    return [r for r in gh("users/%s/repos?per_page=100" % OWNER)
            if not r["fork"] and r["name"] not in SKIP]


def oldest():
    """The first commit and the running total.

    A repository's created_at cannot answer this. These repos were recreated in one batch,
    so most of them claim the same birthday; the commits kept the real dates.
    """
    out = subprocess.run(
        ["gh", "api", "search/commits?q=author:%s&per_page=1&sort=author-date&order=asc" % OWNER],
        capture_output=True, text=True, check=True).stdout
    got = json.loads(out)
    item = got["items"][0]
    return {"date": item["commit"]["author"]["date"][:10],
            "repo": item["repository"]["name"],
            "total": got["total_count"]}


def commits():
    """The last hundred commits. The search API caps a page at a hundred, which is plenty to
    describe a habit and cheap enough to run every day."""
    out = subprocess.run(
        ["gh", "api", "search/commits?q=author:%s&per_page=100&sort=author-date" % OWNER],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)["items"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def frame(cmd, body, height, title, label, note):
    """The shared terminal frame. Everything in this file draws inside one of these."""
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}">
  <title>{title}</title>
  <style>
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", monospace; font-size: 17px; }}
    .sm {{ font-size: 13px; }}
    .key {{ fill: {key}; }}
    .val {{ fill: {val}; }}
    .note {{ fill: {note_c}; font-size: 12.5px; }}
  </style>
  <rect fill="{bg}" x="0" y="0" width="{w}" height="{h}" rx="12"/>
  <rect fill="none" stroke="{edge}" x="8.5" y="8.5" width="{iw}" height="{ih}" rx="10"/>
  <text class="mono" fill="{green}" x="28" y="42">$</text>
  <text class="mono" fill="{val}" x="46" y="42">{cmd}</text>
  <line x1="28" y1="58" x2="{line_end}" y2="58" stroke="{edge}"/>
{body}
  <text class="mono note" x="28" y="{note_y}">{note}</text>
</svg>
'''.format(w=W, h=height, iw=W - 17, ih=height - 17, bg=BG, edge=EDGE, green=GREEN,
           val=VAL, key=KEY, note_c=NOTE, cmd=esc(cmd), body=body,
           line_end=W - 28, note_y=height - 16, note=esc(note), title=esc(title),
           label=esc(label))


def row(y, key, value, pad=11):
    return ('  <text class="mono" x="28" y="%d"><tspan class="key">%s</tspan>'
            '<tspan fill="%s"> %s </tspan><tspan class="val">%s</tspan></text>'
            % (y, key, DOTS, "." * max(2, pad - len(key)), esc(value)))


def build_commits(data):
    items = data["commits"]
    n = len(items)
    days = collections.Counter()
    verbs = collections.Counter()
    lengths, night = [], 0
    for c in items:
        t = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
        days[t.weekday()] += 1
        if t.hour < 6 or t.hour >= 22:
            night += 1
        first = c["commit"]["message"].strip().splitlines()[0]
        lengths.append(len(first))
        verbs[re.split(r"[\s:(]", first.lower())[0][:10]] += 1

    names = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    peak = max(days, key=lambda d: days[d])
    tallest = days[peak]

    body = []
    base, cell = 148, (W - 56) / 7.0
    for i in range(7):
        v = days.get(i, 0)
        h = max(2, round(58 * v / tallest))
        x = 28 + i * cell
        body.append('  <rect x="%.1f" y="%d" width="%.1f" height="%d" rx="2" fill="%s"/>'
                    % (x + 3, base - h, cell - 6, h, SHADES[0] if i == peak else MUTE))
        body.append('  <text class="mono sm" x="%.1f" y="%d" text-anchor="middle" fill="%s">%s</text>'
                    % (x + cell / 2, base + 18, VAL if i == peak else NOTE, names[i]))
    body.append('  <line x1="28" y1="%d" x2="%d" y2="%d" stroke="%s"/>'
                % (base, W - 28, base, EDGE))

    rows = [
        ("weekday", "%d%% of them on a %s" % (round(100 * tallest / n), names[peak])),
        ("midnight", "none, I sleep" if night == 0 else "%d of the last %d" % (night, n)),
        ("verbs", ", ".join("%s %d" % (w, v) for w, v in verbs.most_common(3))),
        ("length", "%d characters, median" % sorted(lengths)[len(lengths) // 2]),
    ]
    for i, (k, v) in enumerate(rows):
        body.append(row(base + 52 + i * 28, k, v))

    height = base + 52 + len(rows) * 28 + 12
    label = "Panel of commit habits: " + "; ".join("%s %s" % kv for kv in rows) + "."
    return frame("git log --author=me --stat", "\n".join(body), height,
                 "commit habits", label, "the last %d commits, straight from the API" % n)


def build_timeline(data):
    o = data["oldest"]
    last = max(r["pushed_at"][:10] for r in data["repos"])
    start = datetime.strptime(o["date"], "%Y-%m-%d")
    end = datetime.strptime(last, "%Y-%m-%d")
    span = max(1, (end - start).days)

    axis_y, x0, x1 = 122, 44, W - 44
    body = ['  <line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>'
            % (x0, axis_y, x1, axis_y, MUTE)]
    for year in range(start.year, end.year + 1):
        mark = max(datetime(year, 1, 1), start)
        x = x0 + (x1 - x0) * (mark - start).days / span
        body.append('  <line x1="%.1f" y1="%d" x2="%.1f" y2="%d" stroke="%s"/>'
                    % (x, axis_y - 7, x, axis_y + 7, EDGE))
        body.append('  <text class="mono sm" x="%.1f" y="%d" text-anchor="middle" fill="%s">%d</text>'
                    % (x, axis_y + 28, NOTE, year))
    body.append('  <circle cx="%d" cy="%d" r="6" fill="%s"/>' % (x0, axis_y, SHADES[0]))
    body.append('  <circle cx="%d" cy="%d" r="6" fill="%s"/>' % (x1, axis_y, GREEN))
    body.append('  <text class="mono sm" x="%d" y="%d" fill="%s">%s</text>'
                % (x0 - 10, axis_y - 18, VAL, o["date"]))
    body.append('  <text class="mono sm" x="%d" y="%d" text-anchor="end" fill="%s">%s</text>'
                % (x1 + 10, axis_y - 18, VAL, last))

    rows = [
        ("first", "a %s" % ("website" if "website" in o["repo"] else "repo")),
        ("commits", "%d since then" % o["total"]),
        ("repos", "%d public, none of them done" % len(data["repos"])),
    ]
    for i, (k, v) in enumerate(rows):
        body.append(row(axis_y + 70 + i * 28, k, v))

    height = axis_y + 70 + len(rows) * 28 + 12
    label = ("A timeline from %s to %s: %s."
             % (o["date"], last, "; ".join("%s %s" % kv for kv in rows)))
    return frame("git log --reverse --date=short", "\n".join(body), height,
                 "since %s" % o["date"][:4], label,
                 "dates from the commits, because a repo birthday lies")


def bar(y, label, part, whole, note):
    """One ratio bar: filled to part over whole, with the count on the right."""
    x, width = 150, W - 150 - 110      # the count sits to the right of the track
    w = max(3, round(width * part / whole))
    return "\n".join([
        '  <text class="mono" x="28" y="%d" fill="%s">%s</text>' % (y + 14, KEY, label),
        '  <rect x="%d" y="%d" width="%d" height="18" rx="3" fill="%s"/>' % (x, y, width, MUTE),
        '  <rect x="%d" y="%d" width="%d" height="18" rx="3" fill="%s"/>' % (x, y, w, SHADES[0]),
        '  <text class="mono sm" x="%d" y="%d" text-anchor="end" fill="%s">%d of %d</text>'
        % (W - 28, y + 14, VAL, part, whole),
        '  <text class="mono sm" x="28" y="%d" fill="%s">%s</text>' % (y + 36, NOTE, esc(note)),
    ])


def build_housekeeping(data):
    rs = data["repos"]
    n = len(rs)
    licensed = sum(1 for r in rs if r.get("license"))
    described = sum(1 for r in rs if (r.get("description") or "").strip())

    body = [bar(96, "licence", licensed, n, "so nobody has to guess what they may do with it"),
            bar(164, "described", described, n, "the rest are scratch repos and will stay that way")]
    rows = [("docs", "German, my brain insists"),
            ("code", "English, like everyone else")]
    for i, (k, v) in enumerate(rows):
        body.append(row(238 + i * 28, k, v))

    height = 238 + len(rows) * 28 + 12
    label = ("Two ratio bars: %d of %d repos carry a licence, %d of %d have a description."
             % (licensed, n, described, n))
    return frame("gh repo list --json license", "\n".join(body), height,
                 "housekeeping", label, "teammates in group projects show up as Contributor")


def build_tour(data):
    by_lang = collections.Counter(r.get("language") or "" for r in data["repos"])
    shelves = [(name, sum(v for l, v in by_lang.items() if l in langs), blurb)
               for name, langs, blurb in BUCKETS]
    shelves = [s for s in shelves if s[1]]
    widest = max(s[1] for s in shelves)

    body, top, rh = [], 88, 34
    for i, (name, count, blurb) in enumerate(shelves):
        y = top + i * rh
        w = max(6, round(84 * count / widest))
        body.append('  <text class="mono" x="28" y="%d" fill="%s">%s/</text>' % (y + 14, KEY, name))
        body.append('  <rect x="122" y="%d" width="%d" height="17" rx="2" fill="%s"/>'
                    % (y, w, SHADES[min(i, len(SHADES) - 1)]))
        body.append('  <text class="mono sm" x="%d" y="%d" fill="%s">%d</text>'
                    % (122 + w + 8, y + 13, NOTE, count))
        body.append('  <text class="mono sm" x="238" y="%d" fill="%s">%s</text>'
                    % (y + 13, VAL, esc(blurb)))

    height = top + len(shelves) * rh + 26
    label = "Repositories by shelf: " + "; ".join("%s %d" % (n, c) for n, c, _ in shelves) + "."
    return frame("tree -L 1 ~/repos", "\n".join(body), height, "the tour", label,
                 "university handed me the deadlines, I picked the stacks")


# The three panels below carry no numbers from the API. They live here rather than as hand
# written SVG files because the frame, the palette and the type sit in this one place; a
# hand written copy would drift from the generated ones the first time a colour changes.
FUN = [
    ("1337", "league of legends", "still climbing, ask again next split"),
    ("4711", "valorant", "my aim is a work in progress"),
    ("2077", "overwatch", "support main, partly your fault"),
    ("9001", "painting", "whenever the queue says 12 minutes"),
]

SETUP = [
    ("editor", "JetBrains, more plugins than sense"),
    ("terminal", "Windows Terminal, sometimes WSL"),
    ("os", "Windows to play, Linux to work"),
    ("keyboard", "mechanical, loud, no regrets"),
    ("notes", "German, my brain insists"),
]

STATUS = [
    ("val", "On branch main"),
    ("val", "Your branch is ahead by 3 commits"),
    ("", ""),
    ("val", "Changes not staged for commit:"),
    ("key", "  modified:   everything"),
    ("key", "  deleted:    the sleep schedule"),
    ("", ""),
    ("note", "no changes added to commit, but"),
    ("note", "untracked ambitions are present"),
]


def build_fun(_):
    top, rh = 92, 46
    body = []
    for i, (pid, name, note) in enumerate(FUN):
        y = top + i * rh
        body.append('  <text class="mono" x="28" y="%d" fill="%s">%s</text>' % (y, NOTE, pid))
        body.append('  <text class="mono" x="88" y="%d" fill="%s">%s</text>' % (y, VAL, esc(name)))
        body.append('  <text class="mono sm" x="88" y="%d" fill="%s">%s</text>'
                    % (y + 20, KEY, esc(note)))
    height = top + len(FUN) * rh + 18
    label = ("A process list of what I do off the clock: "
             + "; ".join("%s, %s" % (n, note) for _, n, note in FUN) + ".")
    return frame("ps aux | grep -i fun", chr(10).join(body), height, "off the clock", label,
                 "four processes, none of them ever exit cleanly")


def build_setup(_):
    top, rh = 88, 30
    body = [row(top + i * rh, k, v) for i, (k, v) in enumerate(SETUP)]
    height = top + len(SETUP) * rh + 18
    label = "What I work with: " + "; ".join("%s %s" % kv for kv in SETUP) + "."
    return frame("cat ~/.config/what-i-use", chr(10).join(body), height, "setup", label,
                 "nothing exotic, everything replaceable")


def build_status(_):
    top, lh = 92, 26
    fills = {"val": VAL, "key": KEY, "note": NOTE}
    body = ['  <text class="mono" x="28" y="%d" fill="%s">%s</text>'
            % (top + i * lh, fills[k], esc(t))
            for i, (k, t) in enumerate(STATUS) if t]
    height = top + len(STATUS) * lh + 12
    label = ("A joke git status: everything modified, the sleep schedule deleted, "
             "ambitions untracked.")
    return frame("git status", chr(10).join(body), height, "git status", label,
                 "the only repo here without a clean working tree")


PANELS = {
    "commits": (build_commits, {"commits"}),
    "timeline": (build_timeline, {"oldest"}),
    "housekeeping": (build_housekeeping, set()),
    "tour": (build_tour, set()),
    "fun": (build_fun, set()),
    "setup": (build_setup, set()),
    "status": (build_status, set()),
}


def main():
    data = {"repos": repos()}
    wanted = {k for _, need in PANELS.values() for k in need}
    if "commits" in wanted:
        data["commits"] = commits()
    if "oldest" in wanted:
        data["oldest"] = oldest()

    for name, (build, _) in sorted(PANELS.items()):
        target = OUT / ("%s.svg" % name)
        target.write_text(build(data), encoding="utf-8")
        print("wrote %-18s %5.1f KB" % (target.name, target.stat().st_size / 1024))


def selftest():
    """A panel is legible on a phone only if the type is a large enough share of the viewBox."""
    assert 17 / W >= 0.028, "17px in a %d wide viewBox is too small for a 390px screen" % W
    out = frame("x", row(40, "k", "v"), 120, "t", "l", "n")
    assert out.startswith("<svg") and out.rstrip().endswith("</svg>")
    assert esc("a & b <c>") == "a &amp; b &lt;c&gt;"
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
