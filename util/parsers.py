#!/usr/bin/env python
# coding: utf-8

from pyquery import PyQuery as pq


def assignments_from_html(html):
    doc = pq(html)
    cells = doc("td.duty-cell")
    assignments = {}

    for i in range(len(cells)):
        date_task = cells.eq(i).attr("data-duty")
        person = cells.eq(i).find("input").attr("value")
        assignments[date_task] = person

    if not assignments:
        raise ValueError("No assignments found in provided html")

    return assignments


def assignments_from_html_file(html_filename):
    print("file://" + html_filename)
    doc = pq(filename=html_filename)
    cells = doc("td.duty-cell")
    assignments = {}

    for i in range(len(cells)):
        date_task = cells.eq(i).attr("data-duty")
        person = cells.eq(i).find("input").attr("value")
        assignments[date_task] = person

    if not assignments:
        raise ValueError(f"No assignments found in {html_filename}")

    return assignments
