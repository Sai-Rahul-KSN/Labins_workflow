"""
extract_images_force_raster.py

Force rasterize all PDF pages to PNGs to extract visible content.
Usage: python extract_images_force_raster.py --input <file_or_folder> [--outdir <output_folder>] [--dpi <dpi>]
"""

import argparse
from pathlib import Path
import sys
import fitz  # PyMuPDF

def find_pdfs(input_path: Path):
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob("*.pdf") if p.is_file()])
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    return []

def rasterize_pdf(pdf_path: Path, out_dir: Path, dpi: int = 150):
    doc = fitz.open(pdf_path)
    saved = 0
    scale = dpi / 72.0
    for page_index in range(len(doc)):
        page = doc[page_index]
        print(f"Rasterizing page {page_index + 1} of {pdf_path}")
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

def main():
    parser = argparse.ArgumentParser(description="Force rasterize PDF pages to PNGs")
    parser.add_argument("--input", "-i", required=False, default=".", help="Input PDF file or directory (default: cwd)")
    parser.add_argument("--outdir", "-o", required=False, default="extracted_images", help="Output directory for images")
    parser.add_argument("--dpi", type=int, default=150, help="DPI for rasterization (default: 150)")
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
            n = rasterize_pdf(pdf, out_dir, dpi=args.dpi)
            print(f"{pdf.name}: rasterized {n} pages")
            total += n
        except Exception as e:
            print(f"Error processing {pdf}: {e}")

    print(f"Done. Total pages rasterized: {total}. Images saved to: {out_dir}")

if __name__ == "__main__":
    main()