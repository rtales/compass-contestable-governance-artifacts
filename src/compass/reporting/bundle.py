from __future__ import annotations

from pathlib import Path
import zipfile
import shutil

from compass.utils.io import ensure_empty_dir, atomic_write_text


def build_paper_bundle(run_dir: Path, template_dir: Path) -> Path:
    """Create an Overleaf-ready bundle.zip with stable paths."""
    paper_dir = run_dir / "paper"
    bundle_dir = paper_dir / "bundle"
    ensure_empty_dir(bundle_dir)

    # Copy template
    shutil.copytree(template_dir, bundle_dir, dirs_exist_ok=True)

    gen_dir = bundle_dir / "generated"
    gen_dir.mkdir(parents=True, exist_ok=True)

    # Minimal generated inputs (tables and summary)
    atomic_write_text(gen_dir / "run_summary.tex", "\\begin{itemize}\n\\item Auto-generated bundle.\n\\end{itemize}\n")
    atomic_write_text(gen_dir / "tables.tex", "\\begin{tabular}{ll}\\toprule Metric & Value \\\\ \\midrule\\end{tabular}\n")

    # Figure placeholder (optional). If missing, LaTeX will fail; so we include a tiny empty PDF if possible.
    fig_path = gen_dir / "figure_utility.pdf"
    if not fig_path.exists():
        # Try to generate a minimal PDF via reportlab if installed, else leave absent.
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            c = canvas.Canvas(str(fig_path), pagesize=letter)
            c.drawString(72, 720, "Figure placeholder (utility)")
            c.save()
        except Exception:
            # leave it missing; users can regenerate with full deps
            pass

    # Zip it
    zip_path = paper_dir / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in bundle_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p.relative_to(bundle_dir)))

    return zip_path
