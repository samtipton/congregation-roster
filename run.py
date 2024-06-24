#!/usr/bin/env python
# coding: utf-8

import pdfkit
import pandas as pd
import sys
import os
from schedule import Schedule
from solver import PulpScheduleSolver
from render import render_schedule_to_html
from roster import Roster
from helpers import *


def main():
    # Accept month and year from command line arguments
    if len(sys.argv) < 4:
        print("Usage: python schedule.py <month> <year> </path/to/output_file>")
        sys.exit(1)

    month = int(sys.argv[1])
    year = int(sys.argv[2])
    pdf_output_file = sys.argv[3]

    debug = "--debug" in sys.argv

    # result, assignments, roster = solve_schedule(year, month)

    schedule = Schedule(year, month, Roster())
    result, assignments, roster = PulpScheduleSolver.solve(schedule)

    # TODO handle special events (e.g. Gospel Meetings)

    # with --page-size=Legal and --orientation=Landscape
    output_filename = os.path.basename(pdf_output_file)

    json_output_dir = os.path.dirname(pdf_output_file) + "/output/json"
    os.makedirs(json_output_dir, exist_ok=True)
    with open(f"{json_output_dir}/{output_filename}.json", "w") as f:
        f.write(schedule.__str__())

    html = render_schedule_to_html(schedule)
    html_output_dir = os.path.dirname(pdf_output_file) + "/output/html"
    os.makedirs(html_output_dir, exist_ok=True)

    with open(f"{html_output_dir}/{output_filename}.html", "w") as f:
        f.write(html)

    pdfkit.from_string(html, pdf_output_file)


if __name__ == "__main__":
    main()
