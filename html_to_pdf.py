#!/usr/bin/env python
# coding: utf-8

import pdfkit
import sys


def main():
    """
    Simple utility for converting a schedule html file to pdf.

    Use-case: edit html in browser and resubmit to render pdf.

    This could instead by included in the run script as a -c option.

    Or, run script could have an interactive option to allow inplace
    editing of the schedule, re-render to preview, complete to output
    final pdf
    """
    # Accept path to html
    if len(sys.argv) < 3:
        print(
            "Usage: python html_to_pdf.py </path/to/html_file> </path/to/output_file>"
        )
        sys.exit(1)

    with open(sys.argv[1], "r") as file:
        html = file.read()

    pdfkit.from_string(html, sys.argv[2])


if __name__ == "__main__":
    main()
