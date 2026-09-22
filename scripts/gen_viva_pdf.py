"""Generates publication-quality PDF for:
Sunrise-ERP-Database-Viva-100.pdf
Target: Full 100 Viva Questions & Answers with architectural diagrams and Top 20 Questions.
"""
import os
import re
import subprocess
import html

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
INPUT_MD = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Viva-100.md")
OUTPUT_HTML = os.path.join(REPO, "docs", "viva-100-print.html")
OUTPUT_PDF = os.path.join(REPO, "docs", "Sunrise-ERP-Database-Viva-100.pdf")

def parse_markdown(md_text):
    lines = md_text.splitlines()
    sections = []
    current_module = None
    current_q = None
    current_q_title = ""
    current_ans_lines = []
    top20_table_lines = []
    in_top20 = False

    for line in lines:
        if line.startswith("## MODULE") or line.startswith("# The Most Important 20 Questions"):
            if current_q:
                current_q["answer"] = "\n".join(current_ans_lines).strip()
                sections.append(current_q)
                current_q = None
                current_ans_lines = []
            
            if line.startswith("# The Most Important 20 Questions"):
                in_top20 = True
                current_module = "TOP 20 ESSENTIAL QUESTIONS"
            else:
                in_top20 = False
                current_module = line.replace("##", "").strip()
            continue

        if in_top20:
            top20_table_lines.append(line)
            continue

        if line.startswith("### Q"):
            if current_q:
                current_q["answer"] = "\n".join(current_ans_lines).strip()
                sections.append(current_q)
                current_q = None
                current_ans_lines = []
            
            q_match = re.match(r"^###\s*(Q\d+):\s*(.*)", line)
            if q_match:
                q_num = q_match.group(1)
                q_text = q_match.group(2)
            else:
                q_num = "Q"
                q_text = line.replace("###", "").strip()

            current_q = {
                "module": current_module,
                "q_num": q_num,
                "question": q_text,
                "answer": ""
            }
            continue

        if current_q:
            if line.startswith("**Answer:**"):
                ans_text = line.replace("**Answer:**", "").strip()
                if ans_text:
                    current_ans_lines.append(ans_text)
            else:
                current_ans_lines.append(line)

    if current_q:
        current_q["answer"] = "\n".join(current_ans_lines).strip()
        sections.append(current_q)

    return sections, "\n".join(top20_table_lines)

def format_answer_html(ans_md):
    # escape basic html
    lines = ans_md.splitlines()
    out = []
    in_code = False
    code_buf = []

    for line in lines:
        if line.strip().startswith("```"):
            if in_code:
                in_code = False
                code_text = html.escape("\n".join(code_buf))
                out.append(f'<pre class="code-block"><code>{code_text}</code></pre>')
                code_buf = []
            else:
                in_code = True
                code_buf = []
            continue
        
        if in_code:
            code_buf.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            continue

        # Math formula representation
        if stripped.startswith("$$") and stripped.endswith("$$"):
            formula = html.escape(stripped[2:-2].strip())
            out.append(f'<div class="formula-box"><strong>Formula:</strong> <code>{formula}</code></div>')
            continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            content = html.escape(stripped[2:])
            # format bold
            content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
            out.append(f'<div class="bullet-item">• {content}</div>')
            continue

        # Numbered list
        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            n_num = num_match.group(1)
            content = html.escape(num_match.group(2))
            content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
            content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
            out.append(f'<div class="numbered-item"><strong>{n_num}.</strong> {content}</div>')
            continue

        # Standard paragraph
        content = html.escape(stripped)
        content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
        content = re.sub(r"`(.*?)`", r"<code>\1</code>", content)
        out.append(f'<p>{content}</p>')

    return "\n".join(out)

def format_top20_table(top20_md):
    lines = top20_md.splitlines()
    rows = []
    table_started = False
    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if not parts or all(p == "" or "-" in p for p in parts):
                continue
            rows.append(parts)

    if not rows:
        return ""

    headers = rows[0]
    data_rows = rows[1:]

    html_out = '<table class="top20-table">\n<thead>\n<tr>\n'
    for h in headers:
        html_out += f'  <th>{html.escape(h)}</th>\n'
    html_out += '</tr>\n</thead>\n<tbody>\n'

    for r in data_rows:
        html_out += '<tr>\n'
        for idx, cell in enumerate(r):
            formatted = html.escape(cell)
            formatted = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", formatted)
            formatted = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted)
            html_out += f'  <td>{formatted}</td>\n'
        html_out += '</tr>\n'

    html_out += '</tbody>\n</table>\n'
    return html_out

def build_html(sections, top20_html):
    cards_html = []
    last_mod = None

    for q in sections:
        mod = q["module"] or "General Architecture"
        # Clean module title
        mod_clean = re.sub(r"\(Q\d+\s*–\s*Q\d+\)", "", mod).replace("*(EXTRA FOCUS SECTION)*", "").strip()

        if mod != last_mod:
            last_mod = mod
            badge_color = "#3b82f6" if "Architecture" in mod else ("#059669" if "Fees" in mod else ("#8b5cf6" if "Exam" in mod else "#4f46e5"))
            cards_html.append(f"""
            <div class="module-header" style="border-left-color: {badge_color};">
              <span class="module-tag">{html.escape(mod_clean)}</span>
            </div>
            """)

        ans_html = format_answer_html(q["answer"])
        q_num = q["q_num"]
        q_title = html.escape(q["question"])

        cards_html.append(f"""
        <div class="q-card">
          <div class="q-header">
            <span class="q-badge">{q_num}</span>
            <span class="q-title">{q_title}</span>
          </div>
          <div class="ans-body">
            {ans_html}
          </div>
        </div>
        """)

    full_cards = "\n".join(cards_html)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sunrise School ERP — 100 Database & Backend Viva Questions</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    @page {{
      size: A4 portrait;
      margin: 11mm 12mm 13mm 12mm;
      @bottom-right {{
        content: "Page " counter(page);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        font-weight: 500;
        color: #94a3b8;
      }}
      @bottom-left {{
        content: "Sunrise School ERP — Database & Backend Viva Guide (100 Questions)";
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
      font-size: 8.4pt;
      line-height: 1.48;
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
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #312e81 100%);
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

    /* Module Header */
    .module-header {{
      background: #f8fafc;
      border-left: 4px solid #4f46e5;
      padding: 6px 12px;
      margin: 14px 0 8px 0;
      border-radius: 0 6px 6px 0;
      break-after: avoid;
      page-break-after: avoid;
    }}

    .module-tag {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 9pt;
      font-weight: 700;
      color: #0f172a;
      letter-spacing: -0.01em;
      text-transform: uppercase;
    }}

    /* Question Card */
    .q-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 11px;
      margin-bottom: 7px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}

    .q-header {{
      display: flex;
      align-items: baseline;
      gap: 7px;
      margin-bottom: 5px;
      border-bottom: 1px solid #f1f5f9;
      padding-bottom: 4px;
    }}

    .q-badge {{
      background: #4f46e5;
      color: #ffffff;
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.5pt;
      font-weight: 700;
      padding: 1.5px 6px;
      border-radius: 4px;
      flex-shrink: 0;
    }}

    .q-title {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 8.8pt;
      font-weight: 700;
      color: #0f172a;
      line-height: 1.35;
    }}

    .ans-body {{
      font-size: 8.1pt;
      color: #334155;
      line-height: 1.45;
    }}

    .ans-body p {{
      margin: 2px 0 4px 0;
    }}

    .bullet-item {{
      margin: 2px 0 2px 8px;
      color: #1e293b;
    }}

    .numbered-item {{
      margin: 2px 0 2px 6px;
      color: #1e293b;
    }}

    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.5pt;
      background: #f1f5f9;
      color: #0f172a;
      padding: 1px 3px;
      border-radius: 3px;
      border: 1px solid #e2e8f0;
    }}

    .code-block {{
      background: #0f172a;
      color: #f8fafc;
      padding: 6px 9px;
      border-radius: 5px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 7pt;
      line-height: 1.35;
      overflow-x: hidden;
      margin: 4px 0;
      white-space: pre-wrap;
      word-break: break-all;
    }}

    .code-block code {{
      background: transparent;
      color: inherit;
      padding: 0;
      border: none;
    }}

    .formula-box {{
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 4px;
      padding: 4px 8px;
      margin: 4px 0;
      font-size: 7.6pt;
      color: #1e3a8a;
    }}

    /* Top 20 Table */
    .top20-section {{
      margin-top: 18px;
      break-before: page;
      page-break-before: always;
    }}

    .top20-header {{
      background: linear-gradient(135deg, #1e1b4b 0%, #4338ca 100%);
      color: #ffffff;
      padding: 12px 16px;
      border-radius: 7px;
      margin-bottom: 12px;
    }}

    .top20-header h2 {{
      font-size: 13pt;
      font-weight: 800;
      margin-bottom: 3px;
    }}

    .top20-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 7.8pt;
      margin-top: 6px;
    }}

    .top20-table th {{
      background: #1e1b4b;
      color: #ffffff;
      padding: 6px 8px;
      text-align: left;
      font-weight: 700;
      border: 1px solid #312e81;
    }}

    .top20-table td {{
      padding: 5px 8px;
      border: 1px solid #cbd5e1;
      vertical-align: top;
      line-height: 1.4;
    }}

    .top20-table tr:nth-child(even) {{
      background: #f8fafc;
    }}

    .top20-table td:nth-child(1) {{
      font-weight: 700;
      text-align: center;
      width: 5%;
    }}

    .top20-table td:nth-child(2) {{
      font-weight: 600;
      width: 25%;
      color: #1e1b4b;
    }}

    .top20-table td:nth-child(3) {{
      width: 70%;
    }}
  </style>
</head>
<body>

  <!-- Top Header Banner -->
  <div class="header-banner">
    <div class="banner-badge">Technical Defense & Viva Examination Guide</div>
    <h1>Sunrise School ERP — 100 Database & Backend Viva Questions</h1>
    <div class="header-subtitle">Comprehensive Project-Specific Verification &amp; Defense Guide for PostgreSQL 18 &amp; FastAPI Backend</div>
    <div class="meta-pills">
      <span class="meta-pill">🎯 100 Project-Specific Questions</span>
      <span class="meta-pill">🗄️ 61 Active Populated Tables</span>
      <span class="meta-pill">💰 28 In-Depth Fee &amp; Ledger Questions</span>
      <span class="meta-pill">⚡ Data Flows, ER Rules &amp; Constraints</span>
      <span class="meta-pill">⭐ Top 20 High-Yield Exam Questions</span>
    </div>
  </div>

  <!-- All 100 Q&A Cards -->
  <div class="cards-container">
    {full_cards}
  </div>

  <!-- Top 20 Questions Section -->
  <div class="top20-section">
    <div class="top20-header">
      <h2>⭐ The Most Important 20 Questions to Prepare First</h2>
      <div style="font-size: 8.5pt; color: #e0e7ff;">Master these 20 high-yield questions first to demonstrate thorough understanding of multi-tenancy, financial immutability, data flows, and constraints.</div>
    </div>
    {top20_html}
  </div>

</body>
</html>
"""

def main():
    print("Reading markdown:", INPUT_MD)
    with open(INPUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()

    sections, top20_md = parse_markdown(md_text)
    print(f"Parsed {len(sections)} questions and answers.")

    top20_html = format_top20_table(top20_md)
    html_content = build_html(sections, top20_html)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Saved HTML to: {OUTPUT_HTML}")

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
