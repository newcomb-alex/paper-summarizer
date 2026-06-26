#!/usr/bin/env python3
"""
md_to_pdf.py — Convert summary.md to a PDF using Pandoc.

Usage:
    python md_to_pdf.py                  # uses defaults (font size 14)
    python md_to_pdf.py --font-size 12
    python md_to_pdf.py --input summary.md --output summary.pdf --font-size 14
"""

import argparse
import os
import sys

import pypandoc

def md_to_pdf(input_file, output_file, font_size=14, font_family="Times New Roman",
              margin="1in"):
    if not os.path.isfile(input_file):
        sys.exit(f"Error: input file '{input_file}' not found.")

    extra_args = [
        "--pdf-engine=xelatex",
        "--variable=documentclass:extarticle",
        #"--variable=classoption:twocolumn",
        f"--variable=fontsize:{font_size}pt",
        f"--variable=mainfont:{font_family}",
        f"--variable=geometry:margin={margin}",
    ]

    try:
        pypandoc.convert_file(
            input_file,
            "pdf",
            outputfile=output_file,
            extra_args=extra_args,
        )
    except OSError:
        sys.exit(
            "Error: Pandoc and/or a LaTeX engine (xelatex) was not found.\n"
            "Install Pandoc (https://pandoc.org/installing.html) and a LaTeX\n"
            "distribution such as TeX Live or MiKTeX, then try again."
        )

    print(f"Success! Created '{output_file}' (font size {font_size}pt).")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Markdown file to PDF using Pandoc."
    )
    parser.add_argument(
        "-i", "--input", default="summary.md",
        help="Input Markdown file (default: summary.md)"
    )
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output PDF file (default: same name as input with .pdf extension)"
    )
    parser.add_argument(
        "-s", "--font-size", type=int, default=14,
        help="Font size in points (default: 14)"
    )
    parser.add_argument(
        "-f", "--font-family", default="Times New Roman",
        help="Main font family (default: 'Times New Roman')"
    )
    parser.add_argument(
        "-m", "--margin", default="1in",
        help="Page margin (default: 1in)"
    )

    args = parser.parse_args()

    # Default output name derived from input if not given
    output = args.output or os.path.splitext(args.input)[0] + ".pdf"

    md_to_pdf(
        input_file=args.input,
        output_file=output,
        font_size=args.font_size,
        font_family=args.font_family,
        margin=args.margin,
    )


if __name__ == "__main__":
    main()