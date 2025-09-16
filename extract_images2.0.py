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
        # use Page.get_images(full=True) to catch images in nested objects/forms
        page = doc[page_index]
        try:
            images = page.get_images(full=True)
        except Exception:
            images = []
        if images:
            for img_index, img in enumerate(images, start=1):
                xref = img[0]
                try:
                    base_image = doc.extract_image(xref)
                except Exception:
                    continue
                image_bytes = base_image.get("image")
                ext = base_image.get("ext", "png")
                out_name = f"{pdf_path.stem}_p{page_index+1}_img{img_index}.{ext}"
                out_path = out_dir / out_name
                with open(out_path, "wb") as f:
                    f.write(image_bytes)
                saved += 1
    # if nothing found and rasterize requested, render pages to images as a fallback
    if saved == 0 and rasterize:
        scale = dpi / 72.0
        for page_index in range(len(doc)):
            page = doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            out_name = f"{pdf_path.stem}_p{page_index+1}.png"
            out_path = out_dir / out_name
            pix.save(str(out_path))
            saved += 1
    return saved
# ...existing code...
def main():
    parser = argparse.ArgumentParser(description="Extract images from PDFs (standalone script)")
    parser.add_argument("--input", "-i", required=False, default=".", help="Input PDF file or directory (default: cwd)")
    parser.add_argument("--outdir", "-o", required=False, default="extracted_images", help="Output directory for images")
    parser.add_argument("--rasterize", "-r", action="store_true", help="If enabled, render pages to PNGs when no embedded images are found")
    parser.add_argument("--dpi", type=int, default=150, help="DPI to use when rasterizing pages (default: 150)")
    args = parser.parse_args()
# ...existing code...
    for pdf in pdfs:
        try:
            n = extract_images_from_pdf(pdf, out_dir, rasterize=args.rasterize, dpi=args.dpi)
            print(f"{pdf.name}: extracted {n} images")
            total += n
        except Exception as e:
            print(f"Error processing {pdf}: {e}")
# ...existing code...

if __name__ == "__main__":
    main()
