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
            print(f"Found {len(images)} image(s) on page {page_index + 1}")
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
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            out_name = f"{pdf_path.stem}_p{page_index + 1}.png"
            out_path = out_dir / out_name
            pix.save(str(out_path))
            print(f"Saved rasterized page: {out_path}")
            saved += 1
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
