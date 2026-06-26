#!/usr/bin/env python3
import argparse
import os
import sys
import tempfile
import pypandoc


def md_to_pdf(input_file, output_file, font_size=14, font_family="Times New Roman",
              margin="1in", two_column=False, column_sep="20pt",
              paper_width=None, paper_height=None):
    if not os.path.isfile(input_file):
        sys.exit(f"Error: input file '{input_file}' not found.")

    extra_args = [
        "--pdf-engine=xelatex",
        "--variable=documentclass:extarticle",
        f"--variable=fontsize:{font_size}pt",
        f"--variable=mainfont:{font_family}",
        f"--variable=geometry:margin={margin}",
    ]

    # Custom page size (e.g. for e-readers)
    if paper_width and paper_height:
        extra_args.append(f"--variable=geometry:paperwidth={paper_width}")
        extra_args.append(f"--variable=geometry:paperheight={paper_height}")

    header_path = None
    if two_column:
        extra_args.append("--variable=classoption:twocolumn")
        header = rf"\setlength{{\columnsep}}{{{column_sep}}}"
        with tempfile.NamedTemporaryFile("w", suffix=".tex", delete=False,
                                         encoding="utf-8") as f:
            f.write(header)
            header_path = f.name
        extra_args.append(f"--include-in-header={header_path}")

    try:
        pypandoc.convert_file(input_file, "pdf", outputfile=output_file,
                              extra_args=extra_args)
    finally:
        if header_path and os.path.exists(header_path):
            os.remove(header_path)

    size = f"{paper_width} x {paper_height}" if paper_width else "default (Letter)"
    print(f"Success! Created '{output_file}' ({font_size}pt, page: {size}).")


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Markdown file to PDF using Pandoc."
    )
    parser.add_argument("-i", "--input", default="summary.md")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-s", "--font-size", type=int, default=14)
    parser.add_argument("-f", "--font-family", default="Times New Roman")
    parser.add_argument("-m", "--margin", default="1in")
    parser.add_argument("-2", "--two-column", action="store_true")
    parser.add_argument("--column-sep", default="20pt")

    # Page-size options
    parser.add_argument("--kindle", action="store_true",
                        help="Use a 6-inch Kindle-friendly page size with tight margins")
    parser.add_argument("--paper-width", default=None,
                        help="Custom page width, e.g. 4.7in")
    parser.add_argument("--paper-height", default=None,
                        help="Custom page height, e.g. 6.3in")

    args = parser.parse_args()
    output = args.output or os.path.splitext(args.input)[0] + ".pdf"

    # Resolve page size / margin
    paper_width = args.paper_width
    paper_height = args.paper_height
    margin = args.margin

    if args.kindle:
        paper_width = paper_width or "4.7in"
        paper_height = paper_height or "6.3in"
        # Only shrink the margin if the user didn't set one explicitly
        if margin == "1in":
            margin = "0.3in"

    md_to_pdf(
        input_file=args.input,
        output_file=output,
        font_size=args.font_size,
        font_family=args.font_family,
        margin=margin,
        two_column=args.two_column,
        column_sep=args.column_sep,
        paper_width=paper_width,
        paper_height=paper_height,
    )


if __name__ == "__main__":
    main()