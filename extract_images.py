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


def extract_images_from_pdf(pdf_path: Path, out_dir: Path):
    doc = fitz.open(pdf_path)
    saved = 0
    for page_index in range(len(doc)):
        images = doc.get_page_images(page_index)
        if not images:
            continue
        for img_index, img in enumerate(images, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image.get("image")
            ext = base_image.get("ext", "png")
            out_name = f"{pdf_path.stem}_p{page_index+1}_img{img_index}.{ext}"
            out_path = out_dir / out_name
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            saved += 1
    return saved


def find_pdfs(input_path: Path):
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob("*.pdf") if p.is_file()])
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        return [input_path]
    return []


def main():
    parser = argparse.ArgumentParser(description="Extract images from PDFs (standalone script)")
    parser.add_argument("--input", "-i", required=False, default=".", help="Input PDF file or directory (default: cwd)")
    parser.add_argument("--outdir", "-o", required=False, default="extracted_images", help="Output directory for images")
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
            n = extract_images_from_pdf(pdf, out_dir)
            print(f"{pdf.name}: extracted {n} images")
            total += n
        except Exception as e:
            print(f"Error processing {pdf}: {e}")

    print(f"Done. Total images extracted: {total}. Images saved to: {out_dir}")

if __name__ == "__main__":
    main()
