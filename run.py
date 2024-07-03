#!/usr/bin/env python
# coding: utf-8

import pdfkit
from pyquery import PyQuery as pq
import sys
import os
import json
from pathlib import Path
from schedule import Schedule
from solver import PulpScheduleSolver
from render import render_schedule_to_html
from roster import Roster
from helpers import *


def write_string_to_file(s, path):
    with open(path, "w") as f:
        f.write(s)


def link(uri, label=None):
    if label is None:
        label = uri
    parameters = ""

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"

    return escape_mask.format(parameters, uri, label)


def wait_for_user_feedback():
    loop = True
    while loop:
        user_input = None
        while user_input == None:
            user_input = input(
                "\nCommit current schedule and output a pdf? Make sure the html file changes have been saved! (y/n)?: "
            )

            if user_input == "y":
                loop = False
                break


def assignments_from_html(html_file):
    doc = pq(filename=html_file)
    cells = doc("td.duty-cell")
    assignments = {}

    for i in range(len(cells)):
        date_task = cells.eq(i).attr("data-duty")
        person = cells.eq(i).find("input").attr("value")
        assignments[date_task] = person

    return assignments


def main():
    """
    TODO Use ArgParser?
    TODO handle special events (e.g. Gospel Meetings)
    """

    # Accept month and year from command line arguments
    if len(sys.argv) < 4:
        print("Usage: python schedule.py <month> <year> </path/to/output_file>")
        sys.exit(1)

    month = int(sys.argv[1])
    year = int(sys.argv[2])
    pdf_output_file = sys.argv[3]

    if len(sys.argv) == 5:
        assignment_history_file = sys.argv[4]

    if not assignment_history_file:
        assignment_history_file = "previous-assignments.csv"

    output_dir = os.path.dirname(pdf_output_file)
    output_file_stem = Path(pdf_output_file).stem
    html_dir = f"{output_dir}/output/html"
    json_dir = f"{output_dir}/output/json"
    html_filename = f"{output_file_stem}.html"
    json_filename = f"{output_file_stem}.json"
    html_output_path = f"{html_dir}/{html_filename}"
    json_output_path = f"{json_dir}/{json_filename}"

    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    # create schedule obj to hold all of our tables and initialize assignment from solver
    schedule = Schedule(year, month, Roster(assignment_history_file))

    # solve the scheduling constraint problem
    solver_result, solver_assignments, roster = PulpScheduleSolver.solve(schedule)

    # write schedule html
    html = render_schedule_to_html(schedule)
    write_string_to_file(html, html_output_path)

    # allow modifying schedule html
    print("")
    print("Please review schedule and make any necessary changes before committing.")
    print("html: " + link("file://" + html_output_path))
    wait_for_user_feedback()

    # read back html to accept any new changes (this could be skipped if user reports no changes, maybe we shouldn't trust)
    html_assignments = assignments_from_html(html_output_path)
    roster.record_assignments(html_assignments)

    # write json representation of schedule
    assignment_json = json.dumps(
        html_assignments, indent=4, sort_keys=True, default=str
    )
    write_string_to_file(assignment_json, json_output_path)

    # write pdf file
    # with --page-size=Legal and --orientation=Landscape
    pdfkit.from_file(html_output_path, pdf_output_file)

    # final output
    print("")
    print("html: " + link(f"file://{html_output_path}"))
    print("json: " + link(f"file://{json_output_path}"))
    print("pdf:  " + link(f"file://{pdf_output_file}"))


if __name__ == "__main__":
    main()
