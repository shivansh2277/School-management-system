"""Build a print edition of the schema reference, and render it to PDF.

The browsable page collapses each table behind a <details>, which is right on
screen and useless on paper - a PDF of it would be 86 summary lines. This emits
the same content fully expanded, drops the search controls, and adds the things
paper needs and a screen does not: a contents page, page breaks that fall
between domains rather than through them, and running table names.

Rendered with headless Chrome, the same way the resume PDF in this repo is
built. Imports gen_db_guide for the data so all three documents agree.
"""
import html as H
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_db_guide as g  # noqa: E402  - side effect: rewrites docs/DATABASE.md

REPO = g.REPO
used = {t for t in g.schema if g.schema[t]["rows"] > 0}
TOTAL_COLS = sum(len(t["columns"]) for t in g.schema.values())
TOTAL_FKS = sum(len(t["fk"]) for t in g.schema.values())

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def esc(s):
    return H.escape(str(s), quote=False)


def columns_table(t):
    info = g.schema[t]
    fk = {f["col"]: f["to"] for f in info["fk"]}
    uniq = set()
    for u in info["unique"]:
        uniq.update(c.strip() for c in u.split(","))
    rows = []
    for c in info["columns"]:
        notes = []
        if c["name"] == "id":
            notes.append('<span class="pk">primary key</span>')
        if c["name"] in fk:
            notes.append("&rarr; " + esc(fk[c["name"]]))
        if c["name"] in uniq:
            notes.append("unique")
        d = c["default"]
        if d and not d.startswith("nextval"):
            notes.append("default " + esc(d.split("::")[0]))
        rows.append(
            '<tr><td class="c">%s</td><td class="t">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td></tr>'
            % (esc(c["name"]), esc(c["type"]),
               "nullable" if c["null"] else "", ", ".join(notes)))
    return ('<table><thead><tr><th>Column</th><th>Type</th><th>Null</th>'
            '<th>Notes</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows))


def relations(t):
    info = g.schema[t]
    bits = []
    if info["fk"]:
        pts = sorted({f["to"].split(".")[0] for f in info["fk"]})
        bits.append("<div><b>Points at</b> %s</div>" % ", ".join(esc(p) for p in pts))
    if info["referenced_by"]:
        bits.append("<div><b>Pointed at by</b> %s</div>"
                    % ", ".join(esc(r) for r in info["referenced_by"]))
    if info["unique"]:
        bits.append("<div><b>Unique on</b> %s</div>"
                    % " &middot; ".join(esc(u) for u in info["unique"]))
    return '<div class="rel">%s</div>' % "".join(bits) if bits else ""


def table_block(t):
    info = g.schema[t]
    chip = ('<span class="chip live">%s rows</span>' % format(info["rows"], ",")
            if info["rows"] else '<span class="chip dormant">empty</span>')
    return ('<article class="tbl"><h3><span class="tname">%s</span>%s</h3>'
            '<p class="purpose">%s</p>%s%s</article>'
            % (esc(t), chip, g.purpose(t), relations(t), columns_table(t)))


def part(title, tables_in_part, note):
    out = ['<h1 class="part">%s</h1><p class="part-note">%s</p>' % (esc(title), note)]
    for domain, tables in g.DOMAINS:
        present = [t for t in tables if t in tables_in_part]
        if not present:
            continue
        out.append('<section class="domain"><h2>%s</h2>%s</section>'
                   % (esc(domain), "".join(table_block(t) for t in present)))
    return "".join(out)


contents = []
for domain, tables in g.DOMAINS:
    live = [t for t in tables if t in used]
    empty = [t for t in tables if t not in used]
    contents.append(
        "<tr><td>%s</td><td class='num'>%d</td><td class='num'>%d</td></tr>"
        % (esc(domain), len(live), len(empty)))

RULES = [
    ("Almost every table carries <code>school_id</code>",
     "The product is sold to separate, independent schools; a tenant is a customer, not a "
     "branch. The column is declared on <code>TenantBase</code> so a new table cannot "
     "quietly be created without one. Three tables derive from <code>TimestampedBase</code> "
     "instead and have none: <code>schools</code> is the tenant, and "
     "<code>permissions</code> and <code>scheduled_jobs</code> belong to the software "
     "rather than to any one school."),
    ("Year-scoped facts hang off <code>enrolment_id</code>",
     "A fee, an attendance mark, a bus seat and a set of marks belong to a child's year in "
     "a class, so they point at <code>enrolments</code>. A name and a date of birth belong "
     "to the child for life, so they point at <code>students</code>."),
    ("Money is never edited",
     "An invoice is voided and reissued; a payment is reversed by a contra entry with a "
     "negative amount and <code>reverses_payment_id</code> pointing at the original."),
    ("A balance is always a SUM",
     "Payments allocate to invoice lines through <code>payment_allocations</code>, oldest "
     "first. What a family owes is computed every time it is asked for."),
    ("Destructive actions carry a reason",
     "<code>void</code>, <code>status_change</code> and <code>delete</code> refuse to commit "
     "without one, and what is stored is the words the person typed."),
]
rules_html = "".join("<li><h3>%s</h3><p>%s</p></li>" % r for r in RULES)

DOC = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Sunrise ERP Schema</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  @page { size: A4; margin: 16mm 14mm 18mm; }
  * { box-sizing: border-box; }
  body {
    margin: 0; color: #1B2333; background: #fff;
    font: 400 9.6pt/1.5 "IBM Plex Sans", system-ui, sans-serif;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }
  code, .mono { font-family: "IBM Plex Mono", monospace; }
  code { font-size: .9em; background: #F2F3F8; padding: .05em .3em; border-radius: 3px; }

  .cover { height: 245mm; display: flex; flex-direction: column; justify-content: center; }
  .eyebrow { font-size: 8pt; letter-spacing: .16em; text-transform: uppercase; color: #8A93A6; margin: 0 0 10mm; }
  .cover h1 {
    font-family: "Instrument Serif", Georgia, serif; font-weight: 400;
    font-size: 40pt; line-height: 1.02; margin: 0 0 6mm; letter-spacing: -.01em;
  }
  .cover p.lede { font-size: 11pt; color: #4E586E; max-width: 120mm; margin: 0 0 12mm; }
  .figures { display: flex; flex-wrap: wrap; gap: 0; border: 1px solid #D9DDE8; border-radius: 2mm; overflow: hidden; max-width: 150mm; }
  .figure { flex: 1 1 28mm; padding: 4mm 5mm; border-right: 1px solid #D9DDE8; }
  .figure:last-child { border-right: 0; }
  .figure b { display: block; font-family: "IBM Plex Mono", monospace; font-size: 15pt; font-weight: 500; font-variant-numeric: tabular-nums; }
  .figure span { font-size: 7.5pt; color: #8A93A6; }
  .provenance { margin-top: 12mm; font-size: 8.5pt; color: #6B7488; max-width: 120mm; }

  h1.part {
    font-family: "Instrument Serif", Georgia, serif; font-weight: 400; font-size: 26pt;
    margin: 0 0 2mm; break-before: page; letter-spacing: -.01em;
  }
  .part-note { margin: 0 0 8mm; color: #4E586E; max-width: 140mm; font-size: 9.5pt; }
  h2 {
    font-family: "Instrument Serif", Georgia, serif; font-weight: 400; font-size: 17pt;
    margin: 0 0 4mm; padding-bottom: 2mm; border-bottom: 1px solid #D9DDE8;
    break-after: avoid;
  }
  .domain { break-before: page; }
  .domain:first-of-type { break-before: auto; }

  .contents h2 { border: 0; }
  table.toc { width: 110mm; border-collapse: collapse; font-size: 9.5pt; }
  table.toc td { padding: 1.6mm 2mm; border-bottom: 1px solid #E8EBF2; }
  table.toc td.num { text-align: right; font-family: "IBM Plex Mono", monospace; font-variant-numeric: tabular-nums; color: #6B7488; }
  table.toc thead td { font-size: 7.5pt; text-transform: uppercase; letter-spacing: .08em; color: #8A93A6; }

  ol.rules { list-style: none; counter-reset: r; margin: 0; padding: 0; }
  ol.rules li { counter-increment: r; position: relative; padding: 0 0 4mm 10mm; break-inside: avoid; }
  ol.rules li::before {
    content: counter(r); position: absolute; left: 0; top: .2mm;
    font-family: "IBM Plex Mono", monospace; font-size: 8pt; color: #4A3BD0;
    background: #ECE9FB; width: 6mm; height: 6mm; display: grid; place-items: center; border-radius: 1.5mm;
  }
  ol.rules h3 { margin: 0 0 1mm; font-size: 10pt; font-weight: 600; }
  ol.rules p { margin: 0; color: #4E586E; font-size: 9pt; }

  article.tbl { break-inside: avoid; margin: 0 0 6mm; }
  article.tbl h3 {
    margin: 0 0 1.5mm; font-size: 11pt; font-weight: 600; display: flex;
    align-items: baseline; gap: 3mm; break-after: avoid;
  }
  .tname { font-family: "IBM Plex Mono", monospace; font-size: 10.5pt; font-weight: 500; }
  .chip { font-size: 7pt; padding: .6mm 2mm; border-radius: 3mm; font-variant-numeric: tabular-nums; }
  .chip.live { background: #E3F3EA; color: #14653E; }
  .chip.dormant { background: #F5EFDD; color: #7A6119; }
  .purpose { margin: 0 0 2mm; color: #38415A; font-size: 9.2pt; max-width: 150mm; }
  .rel { font-size: 8.4pt; color: #5A6478; margin: 0 0 2mm; }
  .rel div { margin-bottom: .6mm; }
  .rel b { color: #1B2333; font-weight: 500; }

  article.tbl table { width: 100%; border-collapse: collapse; font-size: 8.2pt; }
  article.tbl th {
    text-align: left; font-size: 6.8pt; text-transform: uppercase; letter-spacing: .07em;
    color: #8A93A6; font-weight: 500; padding: 1mm 3mm 1mm 0; border-bottom: 1px solid #D9DDE8;
  }
  article.tbl td { padding: 1.1mm 3mm 1.1mm 0; border-bottom: 1px solid #EDEFF5; vertical-align: top; }
  td.c { font-family: "IBM Plex Mono", monospace; }
  td.t { font-family: "IBM Plex Mono", monospace; color: #5A6478; font-size: 7.6pt; }
  td.n { color: #6B7488; font-size: 7.8pt; }
  .pk { color: #4A3BD0; font-weight: 500; }
</style></head><body>

<div class="cover">
  <p class="eyebrow">Sunrise School ERP &middot; database sunrise_test</p>
  <h1>Every table,<br>and what it is for</h1>
  <p class="lede">What each table holds, every column it has, and how it joins to the
  rest. Columns, types, keys and row counts are read from the running database rather
  than written by hand, so they cannot drift from what Postgres actually enforces.</p>
  <div class="figures">
    <div class="figure"><b>__TABLES__</b><span>tables</span></div>
    <div class="figure"><b>__COLS__</b><span>columns</span></div>
    <div class="figure"><b>__FKS__</b><span>foreign keys</span></div>
    <div class="figure"><b>__USED__</b><span>holding data</span></div>
    <div class="figure"><b>__UNUSED__</b><span>still empty</span></div>
  </div>
  <p class="provenance">Generated against migration <code>c3f61e0a77d2</code> on branch
  <code>slice/office-feedback</code>. Row counts come from the seeded demo school and
  will differ on another installation.</p>
</div>

<section class="contents" style="break-before: page">
  <h2>How to read it</h2>
  <p class="part-note">Five rules explain why the tables look the way they do. Without
  them the list that follows is just nouns. They are numbered because the rest of the
  documentation refers to them by number.</p>
  <ol class="rules">__RULES__</ol>

  <h2 style="margin-top:10mm">What is in here</h2>
  <table class="toc">
    <thead><tr><td>Area</td><td class="num">In use</td><td class="num">Empty</td></tr></thead>
    <tbody>__TOC__</tbody>
  </table>
  <p class="provenance">An empty table is not an unfinished one. Each belongs to a
  feature that is built and has working endpoints; this demo school simply has not
  used it.</p>
</section>

__PART1__
__PART2__
</body></html>
"""

doc = (DOC
       .replace("__TABLES__", str(len(g.schema)))
       .replace("__COLS__", str(TOTAL_COLS))
       .replace("__FKS__", str(TOTAL_FKS))
       .replace("__USED__", str(len(used)))
       .replace("__UNUSED__", str(len(g.schema) - len(used)))
       .replace("__RULES__", rules_html)
       .replace("__TOC__", "".join(contents))
       .replace("__PART1__", part(
           "Part one: tables in use", used,
           "Every table here holds data in the seeded school, and the row counts are live."))
       .replace("__PART2__", part(
           "Part two: tables not yet used", set(g.schema) - used,
           "These are empty in the demo school. Each belongs to a feature that is built "
           "and has working endpoints - admission has taken no applications, payroll has "
           "run no cycle, nobody has requested leave. The schema is real; only the rows "
           "are missing.")))

src = os.path.join(REPO, "docs", "database-schema-print.html")
pdf = os.path.join(REPO, "docs", "Sunrise-ERP-Database.pdf")
open(src, "w", encoding="utf-8", newline="\n").write(doc)

subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                "--virtual-time-budget=20000",
                "--print-to-pdf=" + pdf, "file:///" + src.replace("\\", "/")],
               check=True, capture_output=True)
print("wrote", pdf, os.path.getsize(pdf), "bytes")
