#!/usr/bin/env python
# coding: utf-8

import argparse
from logging import info
import os
import json
from pathlib import Path
from core.schedule import Schedule
from core.solver import SchedulingProblem
from core.roster import Roster
from util.helpers import *

import app


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
        default="data/previous-assignments.csv",
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
    tmp_working_path = f"/tmp/{json_filename}"

    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)

    schedule = Schedule(year, month, Roster(args.save_file))

    if os.path.exists(json_output_path):
        with open(json_output_path, "r") as f:
            print(f"\n\nFound previous schedule in {json_output_path}\n\n")
            assignments = json.loads(f.read())
            schedule.set_assignments(assignments)
    else:
        print("Solving new Schedule...")
        schedule_problem = SchedulingProblem(schedule)
        solver_result, solver_assignments, roster = schedule_problem.solve(
            verbose=args.verbose
        )
        write_dict_to_file(schedule.assignments, json_output_path)

    options = {
        "HTML_OUTPUT_PATH": html_output_path,
        "PDF_OUTPUT_PATH": pdf_output_file,
        "JSON_OUTPUT_PATH": json_output_path,
        "TMP_WORKING_PATH": tmp_working_path,
    }

    # debug=True causes main to run twice because of the werkzeug reloader process, very sad
    # see https://stackoverflow.com/questions/25504149/why-does-running-the-flask-dev-server-run-itself-twice
    app.create_app(schedule, options=options).run(debug=False)

    print("")
    print("html: " + term_link(f"file://{html_output_path}"))
    print("json: " + term_link(f"file://{json_output_path}"))
    print("pdf:  " + term_link(f"file://{pdf_output_file}"))


if __name__ == "__main__":
    main()
