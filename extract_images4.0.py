"""
extract_images.py

Standalone script to extract embedded images from PDFs without modifying existing project files.
Usage:
    python extract_images.py --input <file_or_folder> [--outdir <output_folder>]

By default, it will scan the provided path (file or directory) and save images to ./extracted_images.
This uses PyMuPDF (pip package name: pymupdf).
"""

import argparse
import os
import sys
from pathlib import Path
import fitz
print(fitz.__version__)

try:
    import fitz  # PyMuPDF
except Exception as e:
    print("PyMuPDF not installed. Install with: pip install pymupdf")
    raise


# ...existing code...
def extract_images_from_pdf(pdf_path: Path, out_dir: Path, rasterize: bool = False, dpi: int = 150):
    doc = fitz.open(pdf_path)
    saved = 0
    for page_index in range(len(doc)):
        page = doc[page_index]
        print(f"Processing page {page_index + 1} of {pdf_path}")
        try:
            images = page.get_images(full=True)
            print(f"Found {len(images)} image(s) on page {page_index + 1}: {images}")
        except Exception as e:
            print(f"Error getting images on page {page_index + 1}: {e}")
            images = []
        if images:
            for img_index, img in enumerate(images, start=1):
                xref = img[0]
                print(f"Attempting to extract image {img_index} (xref: {xref})")
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image.get("image")
                    ext = base_image.get("ext", "png")
                    out_name = f"{pdf_path.stem}_p{page_index + 1}_img{img_index}.{ext}"
                    out_path = out_dir / out_name
                    with open(out_path, "wb") as f:
                        f.write(image_bytes)
                    print(f"Saved image: {out_path}")
                    saved += 1
                except Exception as e:
                    print(f"Failed to extract image {img_index} (xref: {xref}) on page {page_index + 1}: {e}")
        else:
            print(f"No images found on page {page_index + 1}")
        # Fallback to rasterization if no images found and rasterize is enabled
        if saved == 0 and rasterize:
            scale = dpi / 72.0
            print(f"Rasterizing page {page_index + 1} at {dpi} DPI")
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                out_name = f"{pdf_path.stem}_p{page_index + 1}.png"
                out_path = out_dir / out_name
                pix.save(str(out_path))
                print(f"Saved rasterized page: {out_path}")
                saved += 1
            except Exception as e:
                print(f"Error rasterizing page {page_index + 1}: {e}")
    doc.close()
    return saved
# ...existing code...
def find_pdfs(input_path: Path):
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob("*.pdf") if p.is_file()])
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    return []
# ...existing code...
def main():
    parser = argparse.ArgumentParser(description="Extract images from PDFs (standalone script)")
    parser.add_argument("--input", "-i", required=False, default=".", help="Input PDF file or directory (default: cwd)")
    parser.add_argument("--outdir", "-o", required=False, default="extracted_images", help="Output directory for images")
    parser.add_argument("--rasterize", "-r", action="store_true", help="If enabled, render pages to PNGs when no embedded images are found")
    parser.add_argument("--dpi", type=int, default=150, help="DPI to use when rasterizing pages (default: 150)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    out_dir = Path(args.outdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pdfs = find_pdfs(input_path)
    if not pdfs:
        print(f"No PDF files found at: {input_path}")
        sys.exit(0)

    total = 0
    for pdf in pdfs:
        try:
            n = extract_images_from_pdf(pdf, out_dir, rasterize=args.rasterize, dpi=args.dpi)
            print(f"{pdf.name}: extracted {n} images")
            total += n
        except Exception as e:
            print(f"Error processing {pdf}: {e}")

    print(f"Done. Total images extracted: {total}. Images saved to: {out_dir}")
# ...existing code...

if __name__ == "__main__":
    main()
import argparse
import os
import sys
import re
from pathlib import Path
 
try:
    import fitz  # PyMuPDF
except Exception:
    print("PyMuPDF not installed. Install with: pip install pymupdf")
    raise
 
 
# ---------- helpers ----------
def _safe_name(s: str) -> str:
    s = (s or "").strip()
    return re.sub(r"[^-_.() a-zA-Z0-9]+", "_", s)[:80].strip().replace(" ", "_")
 
 
def _iter_widgets(page):
    """Return a list of widget-like objects for this page (works across PyMuPDF versions)."""
    widgets = []
    try:
        w = page.widgets()
        if w:
            widgets.extend(w)
    except Exception:
        pass
    # Fallback via annotations
    try:
        annot = page.first_annot
        while annot:
            try:
                if getattr(annot, "type", (None,))[0] == fitz.PDF_ANNOT_WIDGET:
                    widgets.append(annot)
            except Exception:
                pass
            annot = annot.next
    except Exception:
        pass
    return widgets
 
 
# ---------- core extraction ----------
def _save_widget_image(doc, page, widget, out_dir: Path, pdf_stem: str,
                       page_num: int, dpi: int, clip_pad: float) -> bool:
    """Render only the widget’s appearance. Returns True if a file was written."""
    rect = fitz.Rect(widget.rect)
    # tiny inset to avoid borders
    if clip_pad:
        rect = fitz.Rect(rect.x0 + clip_pad, rect.y0 + clip_pad,
                         rect.x1 - clip_pad, rect.y1 - clip_pad)
 
    scale = dpi / 72.0
    out_name = f"{pdf_stem}_p{page_num}_field_{_safe_name(getattr(widget, 'field_name', 'widget'))}.png"
    out_path = out_dir / out_name
 
    # Prefer widget-specific rendering if available; else clip the page
    try:
        if hasattr(widget, "get_pixmap"):
            pix = widget.get_pixmap(matrix=fitz.Matrix(scale, scale))
        else:
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=rect)
        pix.save(str(out_path))
        print(f"Saved widget image: {out_path.name}")
        return True
    except Exception as e:
        print(f"[WARN] Failed widget render '{getattr(widget,'field_name','')}' p{page_num}: {e}")
        return False
 
 
def _extract_widgets(doc, page, pdf_stem, page_num, out_dir,
                     target_names, dpi, clip_pad):
    """Extract targeted widgets by exact name (case-insensitive)."""
    saved = 0
    widgets = _iter_widgets(page)
    if not widgets:
        return 0
 
    wanted = {n.strip().lower() for n in target_names if n.strip()}
    for w in widgets:
        fname = (getattr(w, "field_name", "") or "").strip()
        if fname.lower() in wanted:
            ok = _save_widget_image(doc, page, w, out_dir, pdf_stem, page_num, dpi, clip_pad)
            if ok:
                saved += 1
    return saved
 
 
def _extract_page_images(doc, page, pdf_stem, page_num, out_dir):
    """Extract embedded images in the page content stream."""
    saved = 0
    try:
        images = page.get_images(full=True)
    except Exception as e:
        print(f"[WARN] get_images failed on page {page_num}: {e}")
        images = []
    print(f"Found {len(images)} embedded image(s) in page content")
 
    for idx, img in enumerate(images, 1):
        xref = img[0]
        base = f"{pdf_stem}_p{page_num}_img{idx}"
        try:
            pix = fitz.Pixmap(doc, xref)
            if pix.n >= 5:  # CMYK/etc -> RGB
                pix = fitz.Pixmap(fitz.csRGB, pix)
            out_path = out_dir / f"{base}.png"
            pix.save(str(out_path))
            print(f"Saved image (pixmap): {out_path.name}")
            saved += 1
        except Exception as e:
            print(f"[INFO] Pixmap failed (xref {xref}), trying extract_image: {e}")
            try:
                bi = doc.extract_image(xref)
                img_bytes = bi.get("image")
                ext = bi.get("ext", "png")
                out_path = out_dir / f"{base}.{ext}"
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                print(f"Saved image (extract_image): {out_path.name}")
                saved += 1
            except Exception as e2:
                print(f"[WARN] Failed xref {xref}: {e2}")
    return saved
 
 
def extract_images_from_pdf(pdf_path: Path, out_dir: Path,
                            rasterize_mode: str, dpi: int,
                            fields: list, clip_pad: float, include_page_images: bool) -> int:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[ERROR] Could not open {pdf_path}: {e}")
        return 0
 
    pdf_stem = pdf_path.stem
    total_saved = 0
    out_dir.mkdir(parents=True, exist_ok=True)
 
    for i in range(len(doc)):
        page = doc[i]
        page_num = i + 1
        print(f"\n-- Page {page_num} --")
 
        saved_page = 0
 
        # 1) Targeted widgets by exact field names
        if fields:
            saved_page += _extract_widgets(doc, page, pdf_stem, page_num, out_dir,
                                           target_names=fields, dpi=dpi, clip_pad=clip_pad)
 
        # 2) Optional embedded page images
        if include_page_images:
            saved_page += _extract_page_images(doc, page, pdf_stem, page_num, out_dir)
 
        # 3) Optional full-page rasterization
        do_rasterize = (rasterize_mode == "always") or (rasterize_mode == "auto" and saved_page == 0)
        if do_rasterize:
            try:
                scale = dpi / 72.0
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
                out_path = out_dir / f"{pdf_stem}_p{page_num}.png"
                pix.save(str(out_path))
                print(f"Saved rasterized page: {out_path.name} (DPI={dpi})")
                saved_page += 1
            except Exception as e:
                print(f"[WARN] Rasterization failed on page {page_num}: {e}")
 
        total_saved += saved_page
 
    doc.close()
    return total_saved
 
 
# ---------- field listing ----------
def list_form_fields(pdf_path: Path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[ERROR] Could not open {pdf_path}: {e}")
        return
    print(f"\n=== Form Fields in {pdf_path.name} ===")
    for i in range(len(doc)):
        page = doc[i]
        page_num = i + 1
        widgets = _iter_widgets(page)
        if not widgets:
            continue
        print(f"\nPage {page_num}:")
        for w in widgets:
            fname = getattr(w, "field_name", "") or "(unnamed)"
            ftype = getattr(w, "field_type", "unknown")
            rect = getattr(w, "rect", None)
            fval  = getattr(w, "field_value", None)
            print(f"  - Name: {fname} | Type: {ftype} | Rect: {rect} | Value: {fval}")
    doc.close()
 
 
# ---------- CLI ----------
def find_pdfs(input_path: Path):
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob("*.pdf") if p.is_file()])
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    return []
 
 
def main():
    parser = argparse.ArgumentParser(description="Extract widget images and (optionally) page images from PDFs")
    parser.add_argument("--workdir", "-w",
                        default=r"C:\Users\sk23dg\Desktop\Labins_Workflow\PDF_Extractor\test_pdfs",
                        help="Directory to chdir into before running")
    parser.add_argument("--input", "-i", default=".", help="Input PDF file or directory")
    parser.add_argument("--outdir", "-o", default="extracted_images", help="Output directory")
    parser.add_argument("--rasterize", choices=["auto", "off", "always"], default="off",
                        help="Render whole pages to PNGs (auto/off/always). Default: off")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for widget crops / rasterization")
    parser.add_argument("--fields", default="Survey Image",
                        help="Comma-separated exact field names to extract (case-insensitive). "
                             "Default: 'Survey Image'. For your form: "
                             "'Doc Num,Corner of Section,Township,Range,County,Survey Image'")
    parser.add_argument("--clip-pad", type=float, default=1.0,
                        help="Inset (PDF points) to avoid field borders when cropping")
    parser.add_argument("--include-page-images", action="store_true",
                        help="Also extract embedded images from page content")
    parser.add_argument("--list-fields", action="store_true",
                        help="List all form fields and exit")
    args = parser.parse_args()
 
    # chdir first (so relative paths behave like you expect)
    try:
        wd = Path(args.workdir)
        if wd.exists():
            os.chdir(str(wd))
            print(f"Working directory: {wd}")
    except Exception as e:
        print(f"[WARN] Could not change directory: {e}")
 
    input_path = Path(args.input)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
 
    pdfs = find_pdfs(input_path)
    if not pdfs:
        print(f"No PDF files found at: {input_path.resolve()}")
        sys.exit(0)
 
    # List mode
    if args.list_fields:
        for pdf in pdfs:
            list_form_fields(pdf)
        return
 
    # Parse target fields
    fields = [s.strip() for s in args.fields.split(",")] if args.fields else []
 
    total = 0
    for pdf in pdfs:
        try:
            n = extract_images_from_pdf(
                pdf, out_dir,
                rasterize_mode=args.rasterize, dpi=args.dpi,
                fields=fields, clip_pad=args.clip_pad,
                include_page_images=args.include_page_images
            )
            print(f"\n{pdf.name}: wrote {n} file(s)")
            total += n
        except Exception as e:
            print(f"[ERROR] {pdf}: {e}")
 
    print(f"\nDone. Total files written: {total}. Saved to: {out_dir.resolve()}")
 
 
if __name__ == "__main__":
    main()