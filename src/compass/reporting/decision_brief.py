from __future__ import annotations

from pathlib import Path
import json
from datetime import datetime, timezone

from compass.utils.io import atomic_write_text


def write_decision_brief_md(out_dir: Path, brief: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "decision_brief.md"
    lines = []
    lines.append(f"# Decision Brief\n")
    lines.append(f"- Generated: {datetime.now(timezone.utc).isoformat()}Z\n")
    lines.append("## Run identity\n")
    ident = brief.get("identity", {})
    for k, v in ident.items():
        lines.append(f"- **{k}**: {v}\n")
    lines.append("\n## Key metrics\n")
    for k, v in brief.get("metrics", {}).items():
        lines.append(f"- **{k}**: {v}\n")
    lines.append("\n## Policy\n")
    lines.append("```yaml\n" + brief.get("policy_yaml", "").strip() + "\n```\n")
    lines.append("\n## Notes / limitations\n")
    for n in brief.get("notes", []):
        lines.append(f"- {n}\n")

    atomic_write_text(p, "".join(lines))
    atomic_write_text(out_dir / "decision_brief.json", json.dumps(brief, indent=2))
    return p


def try_write_decision_brief_pdf(out_dir: Path, brief: dict) -> Path | None:
    """Generate decision_brief.pdf if reportlab is installed; otherwise return None."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "decision_brief.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    width, height = letter

    y = height - 48
    c.setFont("Helvetica-Bold", 16)
    c.drawString(48, y, "Decision Brief")
    y -= 28

    c.setFont("Helvetica", 10)
    c.drawString(48, y, f"Generated: {datetime.now(timezone.utc).isoformat()}Z")
    y -= 18

    c.setFont("Helvetica-Bold", 12)
    c.drawString(48, y, "Run identity")
    y -= 16
    c.setFont("Helvetica", 10)
    for k, v in brief.get("identity", {}).items():
        c.drawString(54, y, f"{k}: {v}")
        y -= 12
        if y < 72:
            c.showPage()
            y = height - 48

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(48, y, "Key metrics")
    y -= 16
    c.setFont("Helvetica", 10)
    for k, v in brief.get("metrics", {}).items():
        c.drawString(54, y, f"{k}: {v}")
        y -= 12
        if y < 72:
            c.showPage()
            y = height - 48

    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(48, y, "Notes / limitations")
    y -= 16
    c.setFont("Helvetica", 10)
    for n in brief.get("notes", []):
        c.drawString(54, y, f"- {n}")
        y -= 12
        if y < 72:
            c.showPage()
            y = height - 48

    c.save()
    return pdf_path
