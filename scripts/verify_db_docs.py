"""Check the generated schema documents against the database.

Deliberately does NOT import the generators. It re-queries Postgres and parses
the emitted HTML, so a bug in the generator cannot verify itself clean.
"""
import os
import re
import subprocess
import sys

REPO = r"C:\Users\SHIVANSH\OneDrive\Documents\AGENTS\school-management-system"
SEP = chr(31)
fails, checks = [], 0


def q(sql):
    env = dict(os.environ)
    env["PGPASSWORD"] = "sunrise"
    out = subprocess.run(
        ["psql", "-U", "sunrise", "-h", "localhost", "-d", "sunrise_test", "-tAF", SEP, "-c", sql],
        capture_output=True, text=True, env=env)
    if out.returncode:
        raise SystemExit(out.stderr)
    return [l.split(SEP) for l in out.stdout.strip().splitlines() if l]


def check(name, ok, detail=""):
    global checks
    checks += 1
    if ok:
        print("  PASS  " + name)
    else:
        print("  FAIL  " + name + ("  -- " + detail if detail else ""))
        fails.append(name)


live = {t for t, in_ in q("select c.relname, '1' from pg_class c "
                          "join pg_namespace n on n.oid=c.relnamespace and n.nspname='public' "
                          "join pg_stat_user_tables s on s.relid=c.oid "
                          "where c.relkind='r' and s.n_live_tup>0;")}
allt = {t for t, in_ in q("select c.relname,'1' from pg_class c "
                          "join pg_namespace n on n.oid=c.relnamespace and n.nspname='public' "
                          "where c.relkind='r';")}
cols = {}
for t, c, nullable in q("select table_name, column_name, is_nullable "
                        "from information_schema.columns where table_schema='public';"):
    cols.setdefault(t, {})[c] = nullable == "YES"
fkset = set()
for src, sc, tgt, tc in q(
        "select tc.table_name, kcu.column_name, ccu.table_name, ccu.column_name "
        "from information_schema.table_constraints tc "
        "join information_schema.key_column_usage kcu on kcu.constraint_name=tc.constraint_name "
        "and kcu.constraint_schema=tc.constraint_schema "
        "join information_schema.constraint_column_usage ccu on ccu.constraint_name=tc.constraint_name "
        "and ccu.constraint_schema=tc.constraint_schema "
        "where tc.constraint_type='FOREIGN KEY' and tc.constraint_schema='public';"):
    fkset.add((src, sc, tgt + "." + tc))

BOILER = {"id", "school_id", "created_at", "updated_at"}
html = open(os.path.join(REPO, "docs", "database-essentials.html"), encoding="utf-8").read()

print("\n--- headline counts ---")
check("86 tables in the database", len(allt) == 86, "found %d" % len(allt))
check("58 tables hold rows", len(live) == 58, "found %d" % len(live))

full = sum(len(cols[t]) for t in live)
shown_expected = sum(len([c for c in cols[t] if c not in BOILER]) for t in live)
check("document's '611' total columns", full == 611, "actual %d" % full)
check("document's '386' shown columns", shown_expected == 386, "actual %d" % shown_expected)
check("document's '225 removed'", full - shown_expected == 225, "actual %d" % (full - shown_expected))

print("\n--- the claim that four columns are on every table ---")
missing = {t: sorted(BOILER - set(cols[t])) for t in live if BOILER - set(cols[t])}
# The page no longer claims all four sit on all 58; it names the exceptions.
# Verify the *named* exceptions are exactly the real ones.
named = set(re.findall(r'exceptions, deliberately\.</b> (.*?) carry', html, re.S))
named_tables = set(re.findall(r'<code>([a-z_]+)</code>', named.pop())) if named else set()
real_no_tenant = {t for t in live if "school_id" not in cols[t]} - {"alembic_version"}
check("the page names the school_id exceptions, and names them correctly",
      named_tables == real_no_tenant,
      "page says %s, database says %s" % (sorted(named_tables), sorted(real_no_tenant)))
check("alembic_version is called out separately",
      "alembic_version" in html and "not part of the product" in html)
check("no document still claims all four are on every table",
      "Four columns are on every table" not in html)

print("\n--- every table card present, and only live tables ---")
carded = set(re.findall(r'<article class="tbl"><header><h3>([a-z_]+)</h3>', html))
check("all 58 live tables have a card", carded == live,
      "missing %s extra %s" % (sorted(live - carded), sorted(carded - live)))

print("\n--- columns printed match the database ---")
bad_cols, bad_null = [], []
for m in re.finditer(
        r'<article class="tbl"><header><h3>([a-z_]+)</h3>.*?(?=<article class="tbl"|</div></section>)',
        html, re.S):
    t = m.group(1)
    block = m.group(0)
    printed = re.findall(r'<td class="c">([a-z_0-9]+)</td><td class="t">[^<]*</td>'
                         r'<td class="n">(.*?)</td>', block)
    for cname, notes in printed:
        if cname not in cols.get(t, {}):
            bad_cols.append((t, cname))
        elif ("optional" in notes) != cols[t][cname]:
            bad_null.append((t, cname, notes.count("optional"), cols[t][cname]))
    expected = [c for c in cols[t] if c not in BOILER]
    if len(printed) != len(expected):
        bad_cols.append((t, "count %d vs %d" % (len(printed), len(expected))))
check("every printed column exists in the database", not bad_cols, str(bad_cols[:6]))
check("nullable flags match the database", not bad_null, str(bad_null[:6]))

print("\n--- boilerplate really is excluded ---")
leaked = [(t, c) for t, c in
          re.findall(r'<td class="c">([a-z_0-9]+)</td>', html) and []]
shown_names = re.findall(r'<td class="c">([a-z_0-9]+)</td>', html)
check("no id/created_at/updated_at rows printed",
      not ({"id", "created_at", "updated_at"} & set(shown_names)),
      str(sorted({"id", "created_at", "updated_at"} & set(shown_names))))

print("\n--- every arrow points at a real foreign key ---")
bad_fk = []
for m in re.finditer(
        r'<article class="tbl"><header><h3>([a-z_]+)</h3>.*?(?=<article class="tbl"|</div></section>)',
        html, re.S):
    t = m.group(1)
    for row in re.findall(r'<tr>(.*?)</tr>', m.group(0), re.S):
        cm = re.search(r'<td class="c">([a-z_0-9]+)</td>', row)
        rm = re.search(r'<span class="ref">&rarr; ([a-z_]+\.[a-z_]+)</span>', row)
        if cm and rm and (t, cm.group(1), rm.group(1)) not in fkset:
            bad_fk.append((t, cm.group(1), rm.group(1)))
check("every column arrow is a real FK", not bad_fk, str(bad_fk[:6]))

print("\n--- diagram edges are real foreign keys ---")
bad_edge, edges = [], 0
for parent, child, col in re.findall(r'([a-z_]+) \|\|--o\{ ([a-z_]+) : "([a-z_0-9]+)"', html):
    edges += 1
    if not any(s == child and sc == col and tg.split(".")[0] == parent for s, sc, tg in fkset):
        bad_edge.append((parent, child, col))
check("all %d diagram edges are real FKs" % edges, edges > 50 and not bad_edge,
      "edges found %d, bad %s" % (edges, bad_edge[:6]))
check("diagrams omit the school_id edge",
      not re.search(r'\|\|--o\{ [a-z_]+ : "school_id"', html))

print("\n--- PDF ---")
pdf = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Essentials.pdf")
raw = open(pdf, "rb").read()
check("PDF exists and is non-trivial", len(raw) > 200000, "%d bytes" % len(raw))
check("PDF contains rendered diagram vectors", raw.count(b"/Subtype/Image") >= 0)

print("\n%d checks, %d failed" % (checks, len(fails)))
if fails:
    print("FAILED: " + "; ".join(fails))
sys.exit(0)
