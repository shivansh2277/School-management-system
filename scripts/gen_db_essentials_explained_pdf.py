"""Compiles the plain-English Database Essentials Explanation guide into an executive PDF:
Sunrise-ERP-Database-Essentials-Explained.pdf
Target: School Leadership, Technical Examiners, Non-Technical Reviewers.
"""
import os
import re
import subprocess
import html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
INPUT_MD = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Essentials-Explained.md")
OUTPUT_HTML = os.path.join(REPO, "docs", "database-essentials-explained-print.html")
OUTPUT_PDF = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Essentials-Explained.pdf")

def md_to_html(text):
    # Process markdown into structured HTML
    lines = text.splitlines()
    html_out = []
    in_process = False
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()

        # End table if active and non-table line
        if in_table and (not stripped or not stripped.startswith("|")):
            in_table = False
            html_out.append(format_table(table_rows))
            table_rows = []

        if not stripped:
            continue

        # Top Title
        if stripped.startswith("# "):
            title = html.escape(stripped[2:])
            html_out.append(f"""
            <div class="header-banner">
              <div class="banner-badge">Database Architecture &amp; Process Flows</div>
              <h1>{title}</h1>
              <div class="header-subtitle">A Step-by-Step Plain-English Guide to the 68 Active PostgreSQL Tables &amp; How Data Moves Behind the UI</div>
              <div class="meta-pills">
                <span class="meta-pill">🏢 16 End-to-End Processes Explained</span>
                <span class="meta-pill">🗄️ 68 Active Populated Tables</span>
                <span class="meta-pill">💡 5 Core Design Principles</span>
                <span class="meta-pill">🔄 Live Transaction &amp; Query Flows</span>
              </div>
            </div>
            """)
            continue

        # Golden Rules Section
        if stripped.startswith("## The 5 Golden Rules"):
            html_out.append('<div class="golden-rules-box">')
            html_out.append('<h2>🛡️ The 5 Golden Rules of the Database Architecture</h2>')
            continue

        # Process Section
        if stripped.startswith("## PROCESS"):
            if in_process:
                html_out.append('</div>') # Close previous process card
            in_process = True
            proc_title = html.escape(stripped[3:])
            html_out.append(f"""
            <div class="process-card">
              <div class="process-header">
                <span class="process-badge">PROCESS</span>
                <span class="process-title">{proc_title}</span>
              </div>
            """)
            continue

        # Section headings (Goal, Tables, Data Flow, Design Rule)
        if stripped.startswith("### "):
            heading = stripped[4:]
            icon = ""
            if "Goal" in heading:
                icon = "🎯"
            elif "Tables" in heading:
                icon = "🗄️"
            elif "Data Move" in heading or "Step-by-Step" in heading:
                icon = "🔄"
            elif "Clever" in heading or "Design Rule" in heading or "Why" in heading:
                icon = "💡"
            elif "Summary" in heading:
                icon = "📋"

            clean_h = html.escape(re.sub(r"[🎯🗄️🔄💡📋⚠️]", "", heading).strip())
            html_out.append(f'<div class="subheading"><span class="sub-icon">{icon}</span> {clean_h}</div>')
            continue

        # Summary Table Heading
        if stripped.startswith("## Summary"):
            if in_process:
                html_out.append('</div>')
                in_process = False
            html_out.append(f'<div class="summary-header"><h2>📋 {html.escape(stripped[3:])}</h2></div>')
            continue

        # Tables (Markdown table)
        if stripped.startswith("|"):
            in_table = True
            table_rows.append(stripped)
            continue

        # Code block representation (ASCII diagram)
        if stripped.startswith("```"):
            continue

        if "──" in stripped or "┌" in stripped or "▼" in stripped or "│" in stripped:
            escaped_diagram = html.escape(stripped)
            html_out.append(f'<div class="ascii-diagram">{escaped_diagram}</div>')
            continue

        # Numbered list
        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            n = num_match.group(1)
            body = format_inline(num_match.group(2))
            html_out.append(f'<div class="flow-step"><span class="step-num">{n}</span><div class="step-content">{body}</div></div>')
            continue

        # Bullet item
        if stripped.startswith("- ") or stripped.startswith("* "):
            body = format_inline(stripped[2:])
            html_out.append(f'<div class="bullet-item">• {body}</div>')
            continue

        # Standard paragraph
        body = format_inline(stripped)
        html_out.append(f'<p>{body}</p>')

    if in_table:
        html_out.append(format_table(table_rows))
    if in_process:
        html_out.append('</div>')

    return "\n".join(html_out)

def format_inline(text):
    out = html.escape(text)
    out = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"`(.*?)`", r"<code>\1</code>", out)
    return out

def format_table(rows):
    if not rows:
        return ""
    parsed = []
    for r in rows:
        cells = [c.strip() for c in r.split("|")[1:-1]]
        if cells and not all(c == "" or "-" in c for c in cells):
            parsed.append(cells)
    
    if not parsed:
        return ""

    headers = parsed[0]
    data_rows = parsed[1:]

    h_out = '<table class="ref-table">\n<thead>\n<tr>\n'
    for h in headers:
        h_out += f'  <th>{html.escape(h)}</th>\n'
    h_out += '</tr>\n</thead>\n<tbody>\n'

    for r in data_rows:
        h_out += '<tr>\n'
        for c in r:
            h_out += f'  <td>{format_inline(c)}</td>\n'
        h_out += '</tr>\n'
    h_out += '</tbody>\n</table>\n'
    return h_out

def build_full_html(body_html):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sunrise School ERP — Database Essentials Explained</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    @page {{
      size: A4 portrait;
      margin: 11mm 13mm 13mm 13mm;
      @bottom-right {{
        content: "Page " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        font-weight: 500;
        color: #94a3b8;
      }}
      @bottom-left {{
        content: "Sunrise School ERP — Database Essentials Explained (61 Active Tables)";
        font-family: 'Inter', sans-serif;
        font-size: 7.5pt;
        color: #94a3b8;
      }}
    }}

    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    body {{
      font-family: 'Inter', sans-serif;
      font-size: 8.6pt;
      line-height: 1.5;
      color: #1e293b;
      background: #ffffff;
      margin: 0;
      padding: 0;
    }}

    h1, h2, h3, h4 {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      margin: 0;
    }}

    /* Header Banner */
    .header-banner {{
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #3730a3 100%);
      color: #ffffff;
      padding: 18px 22px;
      border-radius: 9px;
      margin-bottom: 14px;
      border-bottom: 3px solid #6366f1;
    }}

    .banner-badge {{
      display: inline-block;
      background: rgba(99, 102, 241, 0.35);
      border: 1px solid rgba(165, 180, 252, 0.4);
      color: #c7d2fe;
      font-size: 7.5pt;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      padding: 2.5px 8px;
      border-radius: 4px;
      margin-bottom: 6px;
    }}

    .header-banner h1 {{
      font-size: 16pt;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 4px;
      color: #ffffff;
    }}

    .header-subtitle {{
      font-size: 8.5pt;
      color: #cbd5e1;
      margin-bottom: 10px;
    }}

    .meta-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }}

    .meta-pill {{
      background: rgba(255, 255, 255, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.18);
      font-size: 7.5pt;
      color: #e2e8f0;
      padding: 2.5px 8px;
      border-radius: 4px;
      font-weight: 500;
    }}

    /* Golden Rules Box */
    .golden-rules-box {{
      background: #f8fafc;
      border: 1.5px solid #cbd5e1;
      border-left: 5px solid #3b82f6;
      border-radius: 7px;
      padding: 11px 15px;
      margin-bottom: 14px;
      break-inside: avoid;
    }}

    .golden-rules-box h2 {{
      font-size: 10.5pt;
      font-weight: 700;
      color: #1e3a8a;
      margin-bottom: 8px;
    }}

    /* Process Card */
    .process-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 7px;
      padding: 10px 14px;
      margin-bottom: 11px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .process-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 7px;
      border-bottom: 1.5px solid #f1f5f9;
      padding-bottom: 6px;
    }}

    .process-badge {{
      background: #1e1b4b;
      color: #ffffff;
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.2pt;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 0.05em;
    }}

    .process-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 9.8pt;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.01em;
    }}

    .subheading {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 8.3pt;
      font-weight: 700;
      color: #334155;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      margin: 8px 0 4px 0;
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .sub-icon {{
      font-size: 9pt;
    }}

    p {{
      margin: 2px 0 5px 0;
      color: #334155;
    }}

    /* Flow Step */
    .flow-step {{
      display: flex;
      gap: 8px;
      margin: 4px 0;
      align-items: flex-start;
    }}

    .step-num {{
      background: #e0e7ff;
      color: #3730a3;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
      font-size: 7.5pt;
      width: 17px;
      height: 17px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      flex-shrink: 0;
      margin-top: 2px;
    }}

    .step-content {{
      flex: 1;
      font-size: 8.3pt;
      color: #1e293b;
    }}

    .bullet-item {{
      margin: 2px 0 2px 10px;
      font-size: 8.3pt;
      color: #334155;
    }}

    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.6pt;
      background: #f1f5f9;
      color: #0f172a;
      padding: 1px 3px;
      border-radius: 3px;
      border: 1px solid #e2e8f0;
    }}

    .ascii-diagram {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.4pt;
      background: #0f172a;
      color: #38bdf8;
      padding: 7px 10px;
      border-radius: 5px;
      margin: 6px 0;
      line-height: 1.35;
      white-space: pre-wrap;
    }}

    /* Reference Table */
    .summary-header {{
      margin: 18px 0 8px 0;
      break-before: page;
      page-break-before: always;
    }}

    .summary-header h2 {{
      font-size: 11pt;
      font-weight: 800;
      color: #0f172a;
    }}

    .ref-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 8pt;
      margin-top: 6px;
    }}

    .ref-table th {{
      background: #1e1b4b;
      color: #ffffff;
      padding: 6px 8px;
      text-align: left;
      font-weight: 700;
      border: 1px solid #312e81;
    }}

    .ref-table td {{
      padding: 5px 8px;
      border: 1px solid #cbd5e1;
      vertical-align: middle;
      color: #1e293b;
    }}

    .ref-table tr:nth-child(even) {{
      background: #f8fafc;
    }}

    .ref-table td:nth-child(1) {{
      font-weight: 700;
      color: #3730a3;
      width: 15%;
    }}

    .ref-table td:nth-child(2) {{
      width: 25%;
    }}

    .ref-table td:nth-child(3) {{
      width: 35%;
    }}

    .ref-table td:nth-child(4) {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.4pt;
      width: 25%;
      color: #0f172a;
    }}
  </style>
</head>
<body>
  {body_html}
</body>
</html>
"""

def main():
    print("Reading markdown:", INPUT_MD)
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    body_html = md_to_html(md_text)
    full_html = build_full_html(body_html)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)
    print("Saved HTML to:", OUTPUT_HTML)

    print("Generating PDF via Headless Chrome...")
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--print-to-pdf={OUTPUT_PDF}",
        "--print-to-pdf-no-header",
        OUTPUT_HTML,
    ]
    subprocess.run(cmd, check=True)
    size = os.path.getsize(OUTPUT_PDF)
    print(f"PDF generated successfully: {OUTPUT_PDF} ({size:,} bytes)")

if __name__ == "__main__":
    main()
