"""CSS Styles and HTML Shell definitions for Sunrise ERP Operational Data-Flow PDF."""

CSS_STYLES = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

@page {
  size: A4 portrait;
  margin: 14mm 14mm 14mm 14mm;
  @bottom-right {
    content: "Page " counter(page);
    font-family: 'Inter', sans-serif;
    font-size: 7.5pt;
    color: #64748b;
  }
  @bottom-left {
    content: "Sunrise School ERP • Code-Verified Operational Data-Flow & Architectural Reference";
    font-family: 'Inter', sans-serif;
    font-size: 7.5pt;
    color: #94a3b8;
  }
}

* {
  box-sizing: border-box;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

body {
  font-family: 'Inter', sans-serif;
  font-size: 8.5pt;
  line-height: 1.45;
  color: #1e293b;
  background: #ffffff;
  margin: 0;
  padding: 0;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Plus Jakarta Sans', sans-serif;
  color: #0f172a;
  margin-top: 0;
}

code, pre, .mono {
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 7.8pt;
}

/* Page Break Utilities */
.page-break {
  page-break-before: always;
}
.no-break {
  break-inside: avoid;
  page-break-inside: avoid;
}

/* Cover / Header Banner */
.cover-hero {
  background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
  color: #ffffff;
  padding: 24px 28px;
  border-radius: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.12);
}
.cover-hero h1 {
  color: #ffffff;
  font-size: 20pt;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 6px;
  letter-spacing: -0.4px;
}
.cover-hero .subtitle {
  color: #cbd5e1;
  font-size: 10.5pt;
  font-weight: 500;
  margin-bottom: 14px;
  line-height: 1.4;
}
.cover-hero .meta-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  background: rgba(255, 255, 255, 0.08);
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 7.5pt;
}
.cover-hero .meta-item strong {
  display: block;
  color: #38bdf8;
  font-size: 8.5pt;
}

/* Section Header Banners */
.section-banner {
  background: #f8fafc;
  border-left: 4px solid #4338ca;
  padding: 10px 14px;
  margin-top: 18px;
  margin-bottom: 12px;
  border-radius: 0 8px 8px 0;
  break-inside: avoid;
}
.section-banner h2 {
  font-size: 13pt;
  font-weight: 700;
  color: #1e1b4b;
  margin: 0 0 2px 0;
}
.section-banner .desc {
  font-size: 8pt;
  color: #64748b;
  margin: 0;
}

/* Workflow Container Card */
.workflow-box {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 16px;
  break-inside: avoid;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.workflow-title {
  font-size: 10.5pt;
  font-weight: 700;
  color: #0f172a;
  border-bottom: 1.5px solid #e2e8f0;
  padding-bottom: 6px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.workflow-title .badge {
  font-size: 7pt;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
  background: #e0e7ff;
  color: #3730a3;
  text-transform: uppercase;
}

/* Sub-headings */
.sub-heading {
  font-size: 8.5pt;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #4338ca;
  margin: 8px 0 4px 0;
}

/* Operational Overview Table / Callout */
.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: #f8fafc;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
  font-size: 8pt;
  margin-bottom: 8px;
}
.overview-item strong {
  color: #475569;
}

/* Data Flow Diagram Card */
.diagram-card {
  background: #0f172a;
  color: #f8fafc;
  border-radius: 6px;
  padding: 10px 14px;
  margin: 8px 0;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 7.2pt;
  line-height: 1.4;
  overflow-x: auto;
  border: 1px solid #1e293b;
}
.diagram-node-user { color: #38bdf8; font-weight: 600; }
.diagram-node-service { color: #a78bfa; font-weight: 600; }
.diagram-node-table { color: #34d399; font-weight: 600; }
.diagram-op-insert { background: #065f46; color: #a7f3d0; padding: 1px 4px; border-radius: 3px; font-weight: 600; font-size: 6.8pt; }
.diagram-op-update { background: #92400e; color: #fde68a; padding: 1px 4px; border-radius: 3px; font-weight: 600; font-size: 6.8pt; }
.diagram-op-read   { background: #1e3a8a; color: #bfdbfe; padding: 1px 4px; border-radius: 3px; font-weight: 600; font-size: 6.8pt; }
.diagram-op-alloc  { background: #831843; color: #fbcfe8; padding: 1px 4px; border-radius: 3px; font-weight: 600; font-size: 6.8pt; }
.diagram-op-link   { background: #3730a3; color: #c7d2fe; padding: 1px 4px; border-radius: 3px; font-weight: 600; font-size: 6.8pt; }
.diagram-arrow     { color: #94a3b8; }

/* Tables */
table.doc-table {
  width: 100%;
  border-collapse: collapse;
  margin: 6px 0 10px 0;
  font-size: 7.8pt;
  break-inside: avoid;
}
table.doc-table th {
  background: #f1f5f9;
  color: #334155;
  font-weight: 700;
  text-align: left;
  padding: 5px 8px;
  border: 1px solid #cbd5e1;
  font-size: 7.6pt;
}
table.doc-table td {
  padding: 4px 8px;
  border: 1px solid #e2e8f0;
  vertical-align: top;
  line-height: 1.35;
}
table.doc-table tr:nth-child(even) td {
  background: #f8fafc;
}

/* Step list */
.step-list {
  margin: 4px 0 8px 0;
  padding-left: 16px;
  font-size: 8pt;
}
.step-list li {
  margin-bottom: 3px;
}

/* Scenario / Real Life Box */
.scenario-box {
  background: #fdf4ff;
  border-left: 3px solid #c026d3;
  padding: 8px 10px;
  border-radius: 0 6px 6px 0;
  font-size: 7.9pt;
  margin-top: 6px;
  color: #581c87;
}
.scenario-box strong {
  color: #701a75;
}

/* Status Badges */
.badge-verified {
  background: #dcfce7;
  color: #166534;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 6.8pt;
  font-weight: 600;
  display: inline-block;
}
.badge-inferred {
  background: #fef3c7;
  color: #92400e;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 6.8pt;
  font-weight: 600;
  display: inline-block;
}

/* Callout alerts */
.alert-box {
  border-radius: 6px;
  padding: 8px 12px;
  margin: 8px 0;
  font-size: 8pt;
  break-inside: avoid;
}
.alert-blue { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
.alert-amber { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; }
.alert-emerald { background: #ecfdf5; border: 1px solid #a7f3d0; color: #065f46; }
"""

def wrap_html(title: str, content: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    {CSS_STYLES}
  </style>
</head>
<body>
  {content}
</body>
</html>
"""
