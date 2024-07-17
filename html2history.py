#!/usr/bin/env python
# coding: utf-8

import argparse
from roster import Roster
from pyquery import PyQuery as pq

input_history_html_file_args = {
    "dest": "input",
    "help": "The history HTML file to add/subtract with",
}

dest_history_csv_file_args = {
    "dest": "dest",
    "default": "previous-assignments.csv",
    "help": "The history csv file to apply changes to",
}


def assignments_from_html(html_file):
    print("file://" + html_file)
    doc = pq(filename=html_file)
    cells = doc("td.duty-cell")
    assignments = {}

    for i in range(len(cells)):
        date_task = cells.eq(i).attr("data-duty")
        person = cells.eq(i).find("input").attr("value")
        assignments[date_task] = person

    if not assignments:
        raise ValueError(f"No assignments found in {html_file}")

    return assignments


def sub(args):
    roster = Roster(args.dest)
    assignments = assignments_from_html(args.input)
    roster.remove_assignments(assignments)


def add(args):
    roster = Roster(args.dest)
    assignments = assignments_from_html(args.input)
    roster.record_assignments(assignments)


def init_subparser(subparsers, name, func):
    subparser = subparsers.add_parser(name)
    subparser.add_argument(**input_history_html_file_args)
    subparser.add_argument(**dest_history_csv_file_args)
    subparser.set_defaults(func=func)
    return subparser


def main():
    """
    This could be a subcommand within run
    """
    parser = argparse.ArgumentParser(
        description="Congregational Scheduling History Utility. Main use case is to add/subtract assignments from a history csv file, using the schedule html"
    )
    subparsers = parser.add_subparsers(required=True)

    init_subparser(subparsers, "add", add)
    init_subparser(subparsers, "subtract", sub)

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
