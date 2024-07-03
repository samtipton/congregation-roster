#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from itertools import zip_longest
from collections import OrderedDict
from pulp import *
from schedule import Schedule
from helpers import *


class PulpScheduleSolver:
    @staticmethod
    def solve(schedule: Schedule):
        return solve_schedule(schedule)


def solve_schedule(schedule: Schedule):
    roster = schedule.roster

    people = roster.people
    tasks = roster.tasks
    assignment_history_df = roster.assignment_history_df
    is_eligible = roster.is_eligible
    get_eligible = roster.get_eligible
    is_excluded = roster.is_excluded
    ideal_avg = roster.ideal_avg

    all_date_tasks = schedule.all_date_tasks
    get_date_tasks = schedule.get_date_tasks

    # Calculate the average assignment frequency for each task
    avg_assignments = pd.DataFrame(index=people, columns=tasks)
    for person in people:
        for task in tasks:
            avg_assignments.loc[person, task] = assignment_history_df.loc[
                person, task
            ] / max(assignment_history_df.loc[person, "Rounds"], 1)

    # # Problem / Objective

    # Create the LP problem
    # We want to choose asignees so as to Maximize the deviation between their historical mean and the ideal mean
    # Over time, we should converge to everyone having the ideal mean
    prob = LpProblem("Task_Assignment", LpMaximize)

    # Define decision variables

    # assignments
    x = LpVariable.dicts(
        "assign",
        ((person, task) for person in people for task in all_date_tasks),
        cat="Binary",
    )

    ###
    # Objective function: maximize the each persons deviation from the ideal average for each task
    ###

    prob += lpSum(
        (
            ideal_avg[trim_task_name(date_task)]
            - avg_assignments.loc[person, trim_task_name(date_task)]
        )
        * x[(person, date_task)]
        for person in people
        for date_task in all_date_tasks
        if is_eligible(person, trim_task_name(date_task))
    )

    ###
    # Constraints
    ###

    # Only assign eligible people
    for person in people:
        for task in tasks:
            if not is_eligible(person, task):
                for ineligible_task in get_date_tasks(task):
                    prob += x[(person, ineligible_task)] == 0

    # Do not assign a person to two excluded tasks in the same period
    for task1 in tasks:
        for task2 in tasks:
            if is_excluded(task1, task2):
                for person in people:
                    if is_eligible(person, task1) and is_eligible(person, task2):
                        for ineligible_pair in zip_longest(
                            get_date_tasks(task1), get_date_tasks(task2), fillvalue=0
                        ):
                            if (
                                0 not in ineligible_pair
                                and ineligible_pair[0] != ineligible_pair[1]
                            ):
                                for person in people:
                                    prob += (
                                        x[(person, ineligible_pair[0])]
                                        + x[(person, ineligible_pair[1])]
                                        <= 1
                                    )

    # do not schedule the same person for the same task in the same month before pool exhausted
    for person in people:
        for task in tasks:
            num_eligible = len(get_eligible(task))
            date_tasks = get_date_tasks(task)

            if num_eligible >= len(date_tasks):
                # we have an abundance everyone should go at least once
                prob += lpSum(x[(person, date_task)] for date_task in date_tasks) <= 1
            else:
                # Some may repeat, but no one should repeat more than one more than the other people
                prob += (
                    lpSum(x[(person, date_task)] for date_task in date_tasks)
                    <= (len(date_tasks) + num_eligible - 1) / num_eligible
                )

    # Task limit constraints
    # Task assignment constraints: each task is assigned to exactly one person
    for task in all_date_tasks:
        prob += lpSum(x[(person, task)] for person in people) == 1

    # hardcoding a custom constraint
    # not working

    # security_date_tasks = get_date_tasks("security")
    # usher_date_tasks = get_date_tasks("usher")

    # for custom_assignee in ["Smiley, Justin", "Purcell, Lance"]:
    #     for i in range(len(security_date_tasks)):
    #         prob += (
    #             x[(custom_assignee, usher_date_tasks[i])]
    #             + x[(custom_assignee, security_date_tasks[i])]
    #             == 2
    #             or x[(custom_assignee, usher_date_tasks[i])]
    #             + x[(custom_assignee, security_date_tasks[i])]
    #             == 0
    #         )

    # Solve the problem
    # result = prob.solve()
    result = prob.solve(PULP_CBC_CMD(msg=False))

    # Output the results
    assignment = {}
    for person in people:
        assigned_tasks = [
            task for task in all_date_tasks if x[(person, task)].varValue == 1
        ]
        if assigned_tasks:
            assignment[person] = assigned_tasks
            for task in assigned_tasks:
                if not is_eligible(person, trim_task_name(task)):
                    print(f"{person} is NOT eligilbe for {task}")

    schedule_assignments = OrderedDict()
    for person in people:
        if person in assignment:
            for task in assignment[person]:
                schedule_assignments[task] = person

    schedule_entries = []
    for key, value in list(schedule_assignments.items()):
        schedule_entries.append(f"{key}: {value}")

    expected_tasks = set(all_date_tasks)
    for etask in expected_tasks:
        if etask not in schedule_assignments.keys():
            print(f"{etask} MISSING!")

    schedule.set_assignments(schedule_assignments)

    return result, schedule, roster
