"""Build the browsable version of the schema reference.

Imports `gen_db_guide` for its introspection, domain map and purposes, so the
two documents can never disagree about what the database contains. That import
also rewrites docs/DATABASE.md, which is harmless: it regenerates the same file
from the same source.

Palette and type follow the product's own system (web/src/theme.ts) rather than
inventing a second identity for the same software.
"""
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_db_guide as g  # noqa: E402  - side effect: rewrites docs/DATABASE.md

REPO = g.REPO
used = {t for t in g.schema if g.schema[t]["rows"] > 0}

payload = []
for domain, tables in g.DOMAINS:
    for t in tables:
        if t not in g.schema:
            continue
        info = g.schema[t]
        payload.append({
            "name": t,
            "domain": domain,
            "rows": info["rows"],
            "purpose": g.purpose(t),
            "columns": info["columns"],
            "fk": info["fk"],
            "refs": info["referenced_by"],
            "unique": info["unique"],
        })

TOTAL_COLS = sum(len(t["columns"]) for t in g.schema.values())
TOTAL_FKS = sum(len(t["fk"]) for t in g.schema.values())

RULES = [
    ("Every table carries <code>school_id</code>",
     "The product is sold to separate, independent schools; a tenant is a customer, not a branch. "
     "The column is declared on a shared base class so a new table cannot quietly be created without "
     "one. A missing tenant key is a data leak between customers, not a style problem."),
    ("Year-scoped facts hang off <code>enrolment_id</code>",
     "A fee, an attendance mark, a bus seat and a set of marks all belong to a child's <em>year in a "
     "class</em>, so they point at <code>enrolments</code>. A name and a date of birth belong to the "
     "child for life, so they point at <code>students</code>. Backwards, and last year's data follows "
     "a child into the new class."),
    ("Money is never edited",
     "An invoice is voided and reissued; a payment is reversed by a contra entry — a second row with a "
     "negative amount and <code>reverses_payment_id</code> pointing at the original. Nothing is "
     "rewritten in place, so the history stays reconstructable."),
    ("A balance is always a SUM",
     "Payments allocate to invoice <em>lines</em> through <code>payment_allocations</code>, oldest "
     "first. What a family owes is computed from those rows every time it is asked for, never read "
     "from a stored column."),
    ("Destructive actions carry a reason",
     "<code>void</code>, <code>status_change</code> and <code>delete</code> refuse to commit without "
     "one, and what is stored is the words the person typed — never a string the software made up."),
]

rules_html = "\n".join(
    '<li><h3>{t}</h3><p>{b}</p></li>'.format(t=t, b=b) for t, b in RULES)

domain_options = "\n".join(
    '<option value="{d}">{d}</option>'.format(d=html.escape(d))
    for d, _ in g.DOMAINS)

TEMPLATE = """<title>Sunrise ERP Schema</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root {
    --ground: #FAFAFD;
    --surface: #FFFFFF;
    --surface-sunk: #F3F4F9;
    --ink: #1B2333;
    --ink-soft: #5A6478;
    --ink-faint: #8A93A6;
    --rule: #E4E7EF;
    --primary: #5B4BE0;
    --primary-soft: #EEEBFC;
    --live: #197A4B;
    --live-soft: #E3F3EA;
    --dormant: #8A6D1F;
    --dormant-soft: #F7F0DC;
    --shadow: 0 1px 2px rgba(27, 35, 51, .06), 0 8px 24px -16px rgba(27, 35, 51, .25);
    color-scheme: light;
  }
  :root:not([data-theme="light"]) {
    @media (prefers-color-scheme: dark) {
      --ground: #13151D;
      --surface: #1B1E29;
      --surface-sunk: #171A24;
      --ink: #E9EBF3;
      --ink-soft: #A2AABD;
      --ink-faint: #767E92;
      --rule: #2B3040;
      --primary: #9C8FFF;
      --primary-soft: #26224A;
      --live: #6FD49B;
      --live-soft: #16301F;
      --dormant: #D9BC6A;
      --dormant-soft: #2E2715;
      --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px -16px rgba(0, 0, 0, .8);
      color-scheme: dark;
    }
  }
  :root[data-theme="dark"] {
    --ground: #13151D;
    --surface: #1B1E29;
    --surface-sunk: #171A24;
    --ink: #E9EBF3;
    --ink-soft: #A2AABD;
    --ink-faint: #767E92;
    --rule: #2B3040;
    --primary: #9C8FFF;
    --primary-soft: #26224A;
    --live: #6FD49B;
    --live-soft: #16301F;
    --dormant: #D9BC6A;
    --dormant-soft: #2E2715;
    --shadow: 0 1px 2px rgba(0, 0, 0, .4), 0 8px 24px -16px rgba(0, 0, 0, .8);
    color-scheme: dark;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--ground);
    color: var(--ink);
    font: 400 16px/1.6 "IBM Plex Sans", system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  code, .mono { font-family: "IBM Plex Mono", ui-monospace, Menlo, monospace; }
  code {
    font-size: .88em;
    background: var(--surface-sunk);
    padding: .1em .34em;
    border-radius: 4px;
  }
  .wrap { max-width: 1040px; margin: 0 auto; padding: 0 24px; }

  /* ---- masthead ---------------------------------------------------- */
  header.masthead { border-bottom: 1px solid var(--rule); background: var(--surface); }
  .masthead .wrap { padding-top: 56px; padding-bottom: 40px; }
  .eyebrow {
    font-size: 12px; letter-spacing: .14em; text-transform: uppercase;
    color: var(--ink-faint); margin: 0 0 14px;
  }
  h1 {
    font-family: "Instrument Serif", Georgia, serif;
    font-weight: 400; font-size: clamp(38px, 6vw, 60px); line-height: 1.04;
    margin: 0 0 14px; letter-spacing: -.01em; text-wrap: balance;
  }
  .standfirst {
    margin: 0; max-width: 62ch; color: var(--ink-soft); font-size: 17px;
  }
  .figures {
    /* Flex, not grid: five figures across four columns left a dead grey block
       on the second row. Letting them stretch keeps the band solid at any width. */
    display: flex; flex-wrap: wrap;
    gap: 1px; margin-top: 36px; background: var(--rule);
    border: 1px solid var(--rule); border-radius: 10px; overflow: hidden;
  }
  .figure { background: var(--surface); padding: 16px 18px; flex: 1 1 128px; }
  .figure b {
    display: block; font-family: "IBM Plex Mono", monospace; font-weight: 500;
    font-size: 26px; letter-spacing: -.02em; font-variant-numeric: tabular-nums;
  }
  .figure span { font-size: 12.5px; color: var(--ink-faint); }

  /* ---- rules ------------------------------------------------------- */
  section.rules { padding: 48px 0 8px; }
  .rules h2, .listing h2 {
    font-family: "Instrument Serif", Georgia, serif; font-weight: 400;
    font-size: 30px; margin: 0 0 6px; letter-spacing: -.01em;
  }
  .section-note { margin: 0 0 26px; color: var(--ink-soft); max-width: 62ch; }
  ol.rules-list { list-style: none; counter-reset: r; margin: 0; padding: 0;
    display: grid; gap: 2px; }
  ol.rules-list li {
    counter-increment: r; position: relative;
    padding: 18px 20px 18px 58px; background: var(--surface);
    border: 1px solid var(--rule); border-radius: 8px;
  }
  ol.rules-list li::before {
    content: counter(r); position: absolute; left: 20px; top: 18px;
    font-family: "IBM Plex Mono", monospace; font-size: 13px;
    color: var(--primary); background: var(--primary-soft);
    width: 24px; height: 24px; display: grid; place-items: center;
    border-radius: 6px; font-weight: 500;
  }
  ol.rules-list h3 { margin: 0 0 4px; font-size: 15.5px; font-weight: 600; }
  ol.rules-list p { margin: 0; color: var(--ink-soft); font-size: 14.5px; max-width: 68ch; }

  /* ---- controls ---------------------------------------------------- */
  .controls {
    position: sticky; top: 0; z-index: 5; background: var(--ground);
    border-bottom: 1px solid var(--rule); padding: 14px 0; margin-top: 44px;
  }
  .controls .wrap { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  input[type="search"], select {
    font: inherit; font-size: 14.5px; color: var(--ink);
    background: var(--surface); border: 1px solid var(--rule);
    border-radius: 7px; padding: 9px 12px;
  }
  input[type="search"] { flex: 1 1 260px; min-width: 0; }
  input[type="search"]::placeholder { color: var(--ink-faint); }
  :focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
  .seg { display: flex; border: 1px solid var(--rule); border-radius: 7px; overflow: hidden; }
  .seg button {
    font: inherit; font-size: 13.5px; padding: 9px 13px; border: 0; cursor: pointer;
    background: var(--surface); color: var(--ink-soft);
  }
  .seg button + button { border-left: 1px solid var(--rule); }
  .seg button[aria-pressed="true"] { background: var(--primary); color: #fff; }
  .count { font-size: 13px; color: var(--ink-faint); margin-left: auto; font-variant-numeric: tabular-nums; }

  /* ---- listing ----------------------------------------------------- */
  .listing { padding: 34px 0 72px; }
  .domain { margin-bottom: 38px; }
  .domain > h2 { font-size: 23px; margin-bottom: 14px; }
  details.tbl {
    background: var(--surface); border: 1px solid var(--rule);
    border-radius: 9px; margin-bottom: 8px;
  }
  details.tbl[open] { box-shadow: var(--shadow); }
  details.tbl > summary {
    cursor: pointer; list-style: none; padding: 14px 18px;
    display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap;
  }
  details.tbl > summary::-webkit-details-marker { display: none; }
  .tname { font-family: "IBM Plex Mono", monospace; font-size: 14.5px; font-weight: 500; }
  .chip {
    font-size: 11.5px; padding: 2px 8px; border-radius: 999px;
    font-variant-numeric: tabular-nums; white-space: nowrap;
  }
  .chip.live { background: var(--live-soft); color: var(--live); }
  .chip.dormant { background: var(--dormant-soft); color: var(--dormant); }
  .tsum { color: var(--ink-soft); font-size: 14px; flex: 1 1 320px; min-width: 0; }
  .body { padding: 0 18px 18px; border-top: 1px solid var(--rule); }
  .rel { display: flex; flex-wrap: wrap; gap: 8px 18px; padding: 14px 0; font-size: 13.5px; }
  .rel div { color: var(--ink-soft); }
  .rel b { color: var(--ink); font-weight: 500; }
  .scroller { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; font-size: 13.5px; }
  th, td { text-align: left; padding: 7px 12px 7px 0; border-bottom: 1px solid var(--rule); }
  th { font-size: 11.5px; letter-spacing: .07em; text-transform: uppercase; color: var(--ink-faint); font-weight: 500; }
  tbody tr:last-child td { border-bottom: 0; }
  td.c { font-family: "IBM Plex Mono", monospace; white-space: nowrap; }
  td.t { color: var(--ink-soft); font-family: "IBM Plex Mono", monospace; font-size: 12.5px; white-space: nowrap; }
  td.n { color: var(--ink-faint); font-size: 12.5px; }
  .pk { color: var(--primary); font-weight: 500; }
  .empty-note { padding: 40px 0; color: var(--ink-faint); text-align: center; }

  footer { border-top: 1px solid var(--rule); background: var(--surface); }
  footer .wrap { padding: 28px 24px 56px; color: var(--ink-soft); font-size: 14px; }
  footer p { margin: 0 0 8px; max-width: 70ch; }

  @media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
</style>

<header class="masthead">
  <div class="wrap">
    <p class="eyebrow">Sunrise School ERP &middot; sunrise_test</p>
    <h1>Every table, and what it is for</h1>
    <p class="standfirst">
      A reference to the school database: what each table holds, every column it has, and
      how it joins to the rest. Columns, types, keys and row counts are read from the
      running database rather than written by hand, so they cannot drift from what
      Postgres actually enforces.
    </p>
    <div class="figures">
      <div class="figure"><b>__TABLES__</b><span>tables</span></div>
      <div class="figure"><b>__COLS__</b><span>columns</span></div>
      <div class="figure"><b>__FKS__</b><span>foreign keys</span></div>
      <div class="figure"><b>__USED__</b><span>holding data</span></div>
      <div class="figure"><b>__UNUSED__</b><span>still empty</span></div>
    </div>
  </div>
</header>

<section class="rules">
  <div class="wrap">
    <h2>How to read it</h2>
    <p class="section-note">
      Five rules explain why the tables look the way they do. Without them the list below
      is just nouns. They are numbered because the rest of the documentation refers to
      them by number.
    </p>
    <ol class="rules-list">__RULES__</ol>
  </div>
</section>

<div class="controls">
  <div class="wrap">
    <input type="search" id="q" placeholder="Search a table, a column, or what it does" aria-label="Search tables and columns">
    <select id="domain" aria-label="Filter by area">
      <option value="">Every area</option>
      __DOMAINS__
    </select>
    <div class="seg" role="group" aria-label="Filter by whether the table holds data">
      <button type="button" data-state="" aria-pressed="true">All</button>
      <button type="button" data-state="live" aria-pressed="false">In use</button>
      <button type="button" data-state="dormant" aria-pressed="false">Empty</button>
    </div>
    <span class="count" id="count"></span>
  </div>
</div>

<main class="listing">
  <div class="wrap" id="out"></div>
</main>

<footer>
  <div class="wrap">
    <p><strong>Empty does not mean unfinished.</strong> Each of the __UNUSED__ empty tables
    belongs to a feature that is built and has working endpoints — admission has taken no
    applications, payroll has run no cycle, nobody has requested leave. The schema is real;
    only the rows are missing.</p>
    <p>Generated against migration <code>c3f61e0a77d2</code> on branch
    <code>slice/office-feedback</code>. Row counts come from the seeded demo school.
    Regenerate with <code>python scripts/gen_db_html.py</code> after any migration rather
    than editing by hand.</p>
  </div>
</footer>

<script>
  const TABLES = __DATA__;
  const out = document.getElementById("out");
  const q = document.getElementById("q");
  const domainSel = document.getElementById("domain");
  const countEl = document.getElementById("count");
  let state = "";

  const esc = (s) => String(s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function columns(t) {
    const fk = Object.fromEntries(t.fk.map((f) => [f.col, f.to]));
    const uniq = new Set(t.unique.flatMap((u) => u.split(",").map((c) => c.trim())));
    const rows = t.columns.map((c) => {
      const notes = [];
      if (c.name === "id") notes.push('<span class="pk">primary key</span>');
      if (fk[c.name]) notes.push("&rarr; " + esc(fk[c.name]));
      if (uniq.has(c.name)) notes.push("unique");
      if (c.default && !c.default.startsWith("nextval")) {
        notes.push("default " + esc(c.default.split("::")[0]));
      }
      return `<tr><td class="c">${esc(c.name)}</td><td class="t">${esc(c.type)}</td>` +
        `<td class="n">${c.null ? "nullable" : ""}</td><td class="n">${notes.join(", ")}</td></tr>`;
    }).join("");
    return `<div class="scroller"><table><thead><tr><th>Column</th><th>Type</th>` +
      `<th>Null</th><th>Notes</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  function relations(t) {
    const bits = [];
    const points = [...new Set(t.fk.map((f) => f.to.split(".")[0]))].sort();
    if (points.length) bits.push(`<div><b>Points at</b> ${points.map(esc).join(", ")}</div>`);
    if (t.refs.length) bits.push(`<div><b>Pointed at by</b> ${t.refs.map(esc).join(", ")}</div>`);
    if (t.unique.length) bits.push(`<div><b>Unique on</b> ${t.unique.map(esc).join(" &middot; ")}</div>`);
    return bits.length ? `<div class="rel">${bits.join("")}</div>` : "";
  }

  function render() {
    const needle = q.value.trim().toLowerCase();
    const dom = domainSel.value;
    const hits = TABLES.filter((t) => {
      if (dom && t.domain !== dom) return false;
      if (state === "live" && t.rows === 0) return false;
      if (state === "dormant" && t.rows > 0) return false;
      if (!needle) return true;
      return t.name.includes(needle)
        || t.purpose.toLowerCase().includes(needle)
        || t.columns.some((c) => c.name.includes(needle));
    });

    countEl.textContent = hits.length === TABLES.length
      ? `${TABLES.length} tables`
      : `${hits.length} of ${TABLES.length}`;

    if (!hits.length) {
      out.innerHTML = `<p class="empty-note">Nothing matches &ldquo;${esc(q.value)}&rdquo;.
        Try a table name like <code>enrolments</code>, or a column like <code>school_id</code>.</p>`;
      return;
    }

    const byDomain = new Map();
    for (const t of hits) {
      if (!byDomain.has(t.domain)) byDomain.set(t.domain, []);
      byDomain.get(t.domain).push(t);
    }

    out.innerHTML = [...byDomain].map(([domain, list]) => `
      <section class="domain">
        <h2>${esc(domain)}</h2>
        ${list.map((t) => `
          <details class="tbl">
            <summary>
              <span class="tname">${esc(t.name)}</span>
              <span class="chip ${t.rows ? "live" : "dormant"}">${
                t.rows ? t.rows.toLocaleString() + " rows" : "empty"}</span>
              <span class="tsum">${t.purpose}</span>
            </summary>
            <div class="body">${relations(t)}${columns(t)}</div>
          </details>`).join("")}
      </section>`).join("");
  }

  q.addEventListener("input", render);
  domainSel.addEventListener("change", render);
  document.querySelectorAll(".seg button").forEach((b) => {
    b.addEventListener("click", () => {
      state = b.dataset.state;
      document.querySelectorAll(".seg button").forEach((o) =>
        o.setAttribute("aria-pressed", String(o === b)));
      render();
    });
  });
  render();
</script>
"""

out_html = (TEMPLATE
            .replace("__TABLES__", str(len(g.schema)))
            .replace("__COLS__", str(TOTAL_COLS))
            .replace("__FKS__", str(TOTAL_FKS))
            .replace("__USED__", str(len(used)))
            .replace("__UNUSED__", str(len(g.schema) - len(used)))
            .replace("__RULES__", rules_html)
            .replace("__DOMAINS__", domain_options)
            .replace("__DATA__", json.dumps(payload, separators=(",", ":"))))

target = os.path.join(REPO, "docs", "database-schema.html")
open(target, "w", encoding="utf-8", newline="\n").write(out_html)
print("wrote", target, len(out_html), "bytes")
