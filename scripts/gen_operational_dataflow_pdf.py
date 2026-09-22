"""Build and compile the complete Operational Data-Flow Documentation PDF:
Sunrise-ERP-Operational-Data-Flows.pdf
"""

import os
import subprocess
import sys

# Ensure scripts directory is in python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, REPO)

from scripts.doc_gen.styles import wrap_html
from scripts.doc_gen.ch1_executive_scope import render_ch1
from scripts.doc_gen.ch2_inventory import render_ch2
from scripts.doc_gen.ch3_workflows_part1 import render_ch3_part1
from scripts.doc_gen.ch3_workflows_part2 import render_ch3_part2
from scripts.doc_gen.ch3_workflows_part3 import render_ch3_part3
from scripts.doc_gen.ch3_workflows_part4 import render_ch3_part4
from scripts.doc_gen.ch4_student_vs_enrollment import render_ch4
from scripts.doc_gen.ch5_cross_module import render_ch5
from scripts.doc_gen.ch6_consolidated_tables import render_ch6
from scripts.doc_gen.ch7_verification_notes import render_ch7

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_HTML = os.path.join(REPO, "docs", "operational-dataflow.html")
OUTPUT_PDF = os.path.join(REPO, "docs", "Sunrise-ERP-Operational-Data-Flows.pdf")

def main():
    print("Assembling operational data-flow documentation chapters...")
    body_content = "\n".join([
        render_ch1(),
        render_ch2(),
        render_ch3_part1(),
        render_ch3_part2(),
        render_ch3_part3(),
        render_ch3_part4(),
        render_ch4(),
        render_ch5(),
        render_ch6(),
        render_ch7()
    ])

    full_html = wrap_html(
        title="Sunrise School ERP — Operational Features, Database Data Flows & Entity Relationships",
        content=body_content
    )

    print(f"Writing HTML document to: {OUTPUT_HTML}...")
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"Wrote {OUTPUT_HTML} ({len(full_html):,} bytes)")

    print(f"Compiling PDF via headless Chrome to: {OUTPUT_PDF}...")
    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--print-to-pdf=" + OUTPUT_PDF,
        "file:///" + OUTPUT_HTML.replace("\\", "/"),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("Chrome compilation error:", res.stderr)
        sys.exit(1)

    pdf_size = os.path.getsize(OUTPUT_PDF)
    print(f"SUCCESS: Generated PDF '{OUTPUT_PDF}' ({pdf_size:,} bytes)")

if __name__ == "__main__":
    main()
