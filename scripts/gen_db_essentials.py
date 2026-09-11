"""The essentials edition: the 58 tables that hold data, with diagrams.

The full reference documents all 86 tables and all 990 columns, which is the
right thing to have and the wrong thing to read. This cuts it to what someone
actually needs at hand:

  * only the tables that hold data
  * only the columns that carry meaning - `id`, `school_id`, `created_at` and
    `updated_at` sit on every table and are stated once instead of 58 times,
    which removes 225 of 611 rows
  * an entity diagram per area, which the full reference only had as Mermaid in
    the markdown and never showed in the browsable page or the PDF at all

Emits two files from one pass: an artifact page, where Mermaid renders natively,
and a print page that loads Mermaid from a CDN so headless Chrome can draw the
same diagrams into a PDF.
"""
import html as H
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_db_guide as g  # noqa: E402  - side effect: rewrites docs/DATABASE.md

REPO = g.REPO
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# On every table, so stated once rather than 58 times.
BOILERPLATE = {"id", "school_id", "created_at", "updated_at"}

used = {t for t in g.schema if g.schema[t]["rows"] > 0}
DOMAINS = [(d, [t for t in ts if t in used]) for d, ts in g.DOMAINS]
DOMAINS = [(d, ts) for d, ts in DOMAINS if ts]

# Which of the four a table actually lacks. Computed, not asserted: the first
# draft of this page claimed all four sat on all 58, and three tables deriving
# from TimestampedBase rather than TenantBase make that false.
def _lacking(col):
    return sorted(t for t in used if col not in {c["name"] for c in g.schema[t]["columns"]})


NO_TENANT = [t for t in _lacking("school_id") if t != "alembic_version"]

SHOWN = sum(len([c for c in g.schema[t]["columns"] if c["name"] not in BOILERPLATE])
            for t in used)
FULL = sum(len(g.schema[t]["columns"]) for t in used)


def esc(s):
    return H.escape(str(s), quote=False)


def diagram(tables):
    """One entity diagram per area.

    The `school_id` edge is omitted: every table has it, so drawing it 58 times
    would bury the relationships that actually carry information. Edges that
    leave the area are kept, because a key crossing a boundary is the one
    somebody forgets.
    """
    seen, lines = set(), []
    for t in tables:
        for f in g.schema[t]["fk"]:
            target = f["to"].split(".")[0]
            key = (t, target, f["col"])
            if f["col"] == "school_id" or target == t or key in seen:
                continue
            seen.add(key)
            lines.append('    %s ||--o{ %s : "%s"' % (target, t, f["col"]))
    if not lines:
        return ""
    body = "erDiagram\n" + "\n".join(lines)
    return '<figure class="erd"><pre class="mermaid">%s</pre></figure>' % esc(body)


def columns(t):
    info = g.schema[t]
    fk = {f["col"]: f["to"] for f in info["fk"]}
    uniq = set()
    for u in info["unique"]:
        uniq.update(c.strip() for c in u.split(","))
    rows = []
    for c in info["columns"]:
        if c["name"] in BOILERPLATE:
            continue
        notes = []
        if c["name"] in fk:
            notes.append('<span class="ref">&rarr; %s</span>' % esc(fk[c["name"]]))
        if c["name"] in uniq:
            notes.append("unique")
        d = c["default"]
        if d and not d.startswith("nextval"):
            notes.append("default " + esc(d.split("::")[0]))
        if c["null"]:
            notes.append('<span class="opt">optional</span>')
        rows.append('<tr><td class="c">%s</td><td class="t">%s</td><td class="n">%s</td></tr>'
                    % (esc(c["name"]), esc(c["type"]), ", ".join(notes)))
    if not rows:
        return '<p class="only-boiler">Nothing but the four columns every table has.</p>'
    return ('<div class="scroller"><table><thead><tr><th>Column</th><th>Type</th>'
            '<th>Notes</th></tr></thead><tbody>%s</tbody></table></div>' % "".join(rows))


def links(t):
    info = g.schema[t]
    bits = []
    pts = sorted({f["to"].split(".")[0] for f in info["fk"] if f["col"] != "school_id"})
    if pts:
        bits.append("<span><b>needs</b> %s</span>" % ", ".join(esc(p) for p in pts))
    if info["referenced_by"]:
        refs = info["referenced_by"]
        shown = ", ".join(esc(r) for r in refs[:6])
        if len(refs) > 6:
            shown += " and %d more" % (len(refs) - 6)
        bits.append("<span><b>used by</b> %s</span>" % shown)
    return '<p class="links">%s</p>' % "".join(bits) if bits else ""


def table_card(t):
    info = g.schema[t]
    return ('<article class="tbl"><header><h3>%s</h3>'
            '<span class="rows">%s rows</span></header>'
            '<p class="use">%s</p>%s%s</article>'
            % (esc(t), format(info["rows"], ","), g.purpose(t), links(t), columns(t)))


def sections():
    out = []
    for domain, tables in DOMAINS:
        out.append(
            '<section class="area" id="%s"><h2>%s</h2>%s<div class="cards">%s</div></section>'
            % (domain.lower().replace(" ", "-").replace(",", "").replace("---", "-"),
               esc(domain), diagram(tables),
               "".join(table_card(t) for t in tables)))
    return "".join(out)


nav = "".join(
    '<a href="#%s">%s <span>%d</span></a>'
    % (d.lower().replace(" ", "-").replace(",", "").replace("---", "-"), esc(d), len(ts))
    for d, ts in DOMAINS)

STYLE = """
  :root {
    --ground:#FAFAFD; --surface:#FFFFFF; --sunk:#F3F4F9;
    --ink:#1B2333; --soft:#5A6478; --faint:#8A93A6; --rule:#E4E7EF;
    --primary:#5B4BE0; --primary-soft:#EEEBFC; --live:#197A4B; --live-soft:#E3F3EA;
    color-scheme: light;
  }
  :root:not([data-theme="light"]) {
    @media (prefers-color-scheme: dark) {
      --ground:#13151D; --surface:#1B1E29; --sunk:#171A24;
      --ink:#E9EBF3; --soft:#A2AABD; --faint:#767E92; --rule:#2B3040;
      --primary:#9C8FFF; --primary-soft:#26224A; --live:#6FD49B; --live-soft:#16301F;
      color-scheme: dark;
    }
  }
  :root[data-theme="dark"] {
    --ground:#13151D; --surface:#1B1E29; --sunk:#171A24;
    --ink:#E9EBF3; --soft:#A2AABD; --faint:#767E92; --rule:#2B3040;
    --primary:#9C8FFF; --primary-soft:#26224A; --live:#6FD49B; --live-soft:#16301F;
    color-scheme: dark;
  }
  * { box-sizing: border-box; }
  body {
    margin:0; background:var(--ground); color:var(--ink);
    font:400 16px/1.6 "IBM Plex Sans", system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  code { font-family:"IBM Plex Mono",monospace; font-size:.88em; background:var(--sunk);
         padding:.08em .32em; border-radius:4px; }
  .wrap { max-width:1080px; margin:0 auto; padding:0 24px; }

  header.top { background:var(--surface); border-bottom:1px solid var(--rule); }
  header.top .wrap { padding:52px 24px 36px; }
  .eyebrow { font-size:12px; letter-spacing:.14em; text-transform:uppercase;
             color:var(--faint); margin:0 0 12px; }
  h1 { font-family:"Instrument Serif",Georgia,serif; font-weight:400;
       font-size:clamp(34px,5.5vw,54px); line-height:1.05; margin:0 0 12px;
       letter-spacing:-.01em; text-wrap:balance; }
  .lede { margin:0; max-width:64ch; color:var(--soft); font-size:16.5px; }
  .boiler {
    margin:26px 0 0; padding:14px 18px; background:var(--primary-soft);
    border-radius:9px; font-size:14px; color:var(--ink); max-width:72ch;
  }
  .boiler b { font-weight:600; }

  nav.areas { background:var(--ground); border-bottom:1px solid var(--rule);
              position:sticky; top:0; z-index:4; }
  nav.areas .wrap { display:flex; flex-wrap:wrap; gap:6px; padding:12px 24px; }
  nav.areas a {
    font-size:13px; text-decoration:none; color:var(--soft);
    background:var(--surface); border:1px solid var(--rule); border-radius:999px;
    padding:5px 12px; display:inline-flex; gap:7px; align-items:center;
  }
  nav.areas a span { font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--faint); }
  nav.areas a:hover { border-color:var(--primary); color:var(--primary); }

  main { padding:16px 0 80px; }
  .area { padding-top:40px; }
  .area > h2 {
    font-family:"Instrument Serif",Georgia,serif; font-weight:400; font-size:28px;
    margin:0 0 16px; letter-spacing:-.01em;
  }
  figure.erd {
    margin:0 0 22px; padding:18px; background:var(--surface);
    border:1px solid var(--rule); border-radius:10px; overflow-x:auto;
  }
  figure.erd pre { margin:0; }

  .cards { display:grid; gap:10px; }
  article.tbl { background:var(--surface); border:1px solid var(--rule); border-radius:10px;
                padding:16px 18px; }
  article.tbl header { display:flex; align-items:baseline; gap:10px; margin-bottom:6px; }
  article.tbl h3 { margin:0; font-family:"IBM Plex Mono",monospace; font-size:14.5px;
                   font-weight:500; }
  .rows { font-size:11.5px; padding:2px 8px; border-radius:999px;
          background:var(--live-soft); color:var(--live);
          font-variant-numeric:tabular-nums; white-space:nowrap; }
  .use { margin:0 0 8px; color:var(--soft); font-size:14.5px; max-width:76ch; }
  .links { margin:0 0 12px; font-size:13px; color:var(--faint);
           display:flex; flex-wrap:wrap; gap:4px 20px; }
  .links b { color:var(--soft); font-weight:500; }
  .only-boiler { margin:0; font-size:13.5px; color:var(--faint); }

  .scroller { overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:13.5px; }
  th { text-align:left; font-size:11px; letter-spacing:.07em; text-transform:uppercase;
       color:var(--faint); font-weight:500; padding:0 14px 6px 0;
       border-bottom:1px solid var(--rule); }
  td { padding:6px 14px 6px 0; border-bottom:1px solid var(--rule); vertical-align:top; }
  tbody tr:last-child td { border-bottom:0; }
  td.c { font-family:"IBM Plex Mono",monospace; white-space:nowrap; }
  td.t { font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--soft);
         white-space:nowrap; }
  td.n { color:var(--faint); font-size:12.5px; }
  .ref { font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--primary); }
  .opt { color:var(--faint); }

  footer { border-top:1px solid var(--rule); background:var(--surface); }
  footer .wrap { padding:26px 24px 52px; color:var(--soft); font-size:14px; }
  footer p { margin:0 0 8px; max-width:72ch; }
  @media (prefers-reduced-motion: reduce) { * { transition:none !important; } }
"""

BODY = """
<header class="top">
  <div class="wrap">
    <p class="eyebrow">Sunrise School ERP &middot; the working set</p>
    <h1>The 58 tables that hold data</h1>
    <p class="lede">Every table the seeded school actually uses, what each one is for,
    the columns that carry meaning, and an entity diagram per area. The full reference
    covers all 86 tables and all 990 columns; this is the part you keep open.</p>
    <p class="boiler"><b>Four columns are left out below</b> because they repeat on
    almost every table: <code>id</code>, <code>school_id</code>, <code>created_at</code>
    and <code>updated_at</code>. Stating them once rather than 58 times removes __SAVED__
    of __FULL__ rows. <code>school_id</code> is the tenant key, so its edge is left off the
    diagrams too, which would otherwise draw it on nearly every table.</p>
    <p class="boiler"><b>Four tables are exceptions, deliberately.</b> __NO_TENANT__ carry
    no <code>school_id</code>: they derive from <code>TimestampedBase</code> rather than
    <code>TenantBase</code>, because <code>schools</code> <em>is</em> the tenant, and the
    permission vocabulary and the job schedule belong to the software rather than to any
    one school. <code>alembic_version</code> has none of the four &mdash; it is Alembic's
    own bookkeeping and not part of the product.</p>
  </div>
</header>

<nav class="areas"><div class="wrap">__NAV__</div></nav>

<main><div class="wrap">__SECTIONS__</div></main>

<footer>
  <div class="wrap">
    <p>Diagrams read <code>parent ||--o{ child</code>, labelled with the column that
    carries the key. Edges leaving an area are drawn, because a key that crosses a
    boundary is the one that gets forgotten.</p>
    <p>Columns, types, keys and row counts are read from the running database, not
    written by hand. Generated against migration <code>c3f61e0a77d2</code> on branch
    <code>slice/office-feedback</code>; row counts are the seeded demo school's.
    Regenerate with <code>python scripts/gen_db_essentials.py</code>.</p>
  </div>
</footer>
"""

body = (BODY
        .replace("__NAV__", nav)
        .replace("__SECTIONS__", sections())
        .replace("__SAVED__", str(FULL - SHOWN))
        .replace("__FULL__", str(FULL))
        .replace("__NO_TENANT__", ", ".join(
            "<code>%s</code>" % t for t in NO_TENANT)))

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Instrument+Serif&family=IBM+Plex+Sans:wght@400;500;600&'
         'family=IBM+Plex+Mono:wght@400;500&display=swap">')

# --- the artifact page: Mermaid renders natively, no library needed ---------
artifact = ("<title>Sunrise Schema Essentials</title>\n" + FONTS
            + "\n<style>" + STYLE + "</style>\n" + body)
art_path = os.path.join(REPO, "docs", "database-essentials.html")
open(art_path, "w", encoding="utf-8", newline="\n").write(artifact)
print("wrote", art_path, len(artifact), "bytes")

# --- the print page: same content, Mermaid loaded so Chrome can draw it -----
PRINT_EXTRA = """
  @page { size: A4 landscape; margin: 12mm; }
  body { background:#fff; font-size:9.4pt; }
  nav.areas { display:none; }
  header.top .wrap { padding:0 0 10mm; }
  .wrap { max-width:none; padding:0; }
  .area { break-before:page; padding-top:0; }
  /* Keep an area's heading with its diagram: `break-inside: avoid` on the
     figure was pushing the diagram to the next page and leaving the title
     alone at the bottom of the previous one. */
  .area > h2 { break-after:avoid; margin-bottom:4mm; }
  .area:first-of-type { break-before:auto; }
  article.tbl, figure.erd { break-inside:avoid; }
  .cards { grid-template-columns:repeat(2,1fr); }
  footer { break-before:page; }
"""

print_html = (
    "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
    "<title>Sunrise Schema Essentials</title>" + FONTS
    + "<style>" + STYLE + PRINT_EXTRA + "</style></head><body>" + body
    + '<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>'
    + '<script>mermaid.initialize({startOnLoad:true,theme:"neutral",'
      'er:{useMaxWidth:true}});</script>'
    + "</body></html>")
print_path = os.path.join(REPO, "docs", "database-essentials-print.html")
open(print_path, "w", encoding="utf-8", newline="\n").write(print_html)

pdf = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Essentials.pdf")
subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                "--virtual-time-budget=40000", "--run-all-compositor-stages-before-draw",
                "--print-to-pdf=" + pdf, "file:///" + print_path.replace("\\", "/")],
               check=True, capture_output=True)
print("wrote", pdf, os.path.getsize(pdf), "bytes")
print("tables %d, columns shown %d of %d" % (len(used), SHOWN, FULL))
