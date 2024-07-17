#!/usr/bin/env python
# coding: utf-8

import argparse
import pdfkit
import os
import json
from pathlib import Path
from schedule import Schedule
from solver import SchedulingProblem
from render import render_schedule_to_html
from roster import Roster
from html2history import assignments_from_html
from helpers import *


def wait_for_schedule_commit():
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Congregational Scheduling Constraint Solver"
    )
    parser.add_argument("month", type=int, help="the month (1-12)")
    parser.add_argument("year", type=int, help="the year (e.g. 2025)")
    parser.add_argument(
        "dest_file",
        help="the output path for the pdf file",
    )
    parser.add_argument(
        "-s",
        "--save_file",
        default="previous-assignments.csv",
        help="optional alternative 'save' csv file. If not specified previous-assignments.csv will be used",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="turn on additional logging"
    )

    return parser.parse_args()


def main():
    """
    TODO handle special events (e.g. Gospel Meetings)
    """

    args = parse_args()

    month = args.month
    year = args.year
    pdf_output_file = args.dest_file

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
    schedule = Schedule(year, month, Roster(args.save_file))

    schedule_problem = SchedulingProblem(schedule)
    solver_result, solver_assignments, roster = schedule_problem.solve(
        verbose=args.verbose
    )

    # write schedule html
    html = render_schedule_to_html(schedule)
    write_string_to_file(html, html_output_path)

    # allow modifying schedule html
    print("")
    print("Please review schedule and make any necessary changes before committing.")
    print("html: " + term_link("file://" + html_output_path))
    wait_for_schedule_commit()

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
    print("html: " + term_link(f"file://{html_output_path}"))
    print("json: " + term_link(f"file://{json_output_path}"))
    print("pdf:  " + term_link(f"file://{pdf_output_file}"))


if __name__ == "__main__":
    main()
