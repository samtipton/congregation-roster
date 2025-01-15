from itertools import zip_longest
from collections import OrderedDict
from logging import info
from pulp import *
from .schedule import Schedule
from util import *


class SchedulingProblem:
    def __init__(self, schedule: Schedule):
        self.schedule = schedule

        self.roster = schedule.roster

        self.people = self.roster.people
        self.tasks = self.roster.tasks
        self.is_eligible = self.roster.is_eligible
        self.get_eligible = self.roster.get_eligible
        self.is_excluded = self.roster.is_excluded
        self.bias = self.roster.bias
        self.ideal_avg = self.roster.ideal_avg
        self.actual_avg = self.roster.actual_avg
        self.excluded_tasks = self.roster.excluded_tasks

        self.all_date_tasks = schedule.all_date_tasks
        self.get_date_tasks = schedule.get_date_tasks

        self.x = LpVariable.dicts(
            "assignment",
            ((person, task) for person in self.people for task in self.all_date_tasks),
            cat="Binary",
        )

        self.set_objective_function()
        self.constrain_one_person_per_task()
        self.constrain_assign_only_eligible_people()
        self.constrain_do_not_assign_excluded_tasks()
        self.constrain_do_not_over_assign_in_month()

    def solve(self, verbose=False):
        result = self.prob.solve(PULP_CBC_CMD(msg=verbose))

        assignment = {}
        for person in self.people:
            assigned_tasks = [
                task
                for task in self.all_date_tasks
                if self.x[(person, task)].varValue == 1
            ]
            if assigned_tasks:
                assignment[person] = assigned_tasks
                for task in assigned_tasks:
                    if not self.is_eligible(person, trim_task_name(task)):
                        print(f"{person} is NOT eligible for {task}")

        schedule_assignments = OrderedDict()
        for person in self.people:
            if person in assignment:
                for task in assignment[person]:
                    schedule_assignments[task] = person

        schedule_entries = []
        for key, value in list(schedule_assignments.items()):
            schedule_entries.append(f"{key}: {value}")

        expected_tasks = set(self.all_date_tasks)
        for expected_task in expected_tasks:
            if expected_task not in schedule_assignments.keys():
                print(f"{expected_task} MISSING!")

        self.schedule.set_assignments(schedule_assignments)

        return result, self.schedule, self.roster

    def set_objective_function(self):
        """
        We want to choose assignees so as to Maximize the deviation between their historical mean and the ideal mean
        Over time, we should converge to everyone having the ideal mean
        """
        self.prob = LpProblem("Scheduling_Problem", LpMaximize)
        self.prob += lpSum(
            # maximize the difference between ideal and actual averages
            (
                self.ideal_avg[trim_task_name(date_task)]
                - (
                    self.actual_avg.loc[person, trim_task_name(date_task)]
                    # bias the value (.1 < bias_value < 1)
                    * self.bias_value(person, date_task)
                )
            )
            # 1 if assigned, 0 otherwise
            * self.x[(person, date_task)]
            for person in self.people
            for date_task in self.all_date_tasks
            if self.is_eligible(person, trim_task_name(date_task))
        )

    def bias_value(self, person, date_task):
        bias_value = self.bias[trim_task_name(date_task)][person]

        if bias_value == 0:
            return 1

        if bias_value < 1:
            b = 1 / max(1 - bias_value, 0.01)
        elif bias_value > 1:
            b = 1 - bias_value

        return b

    def constrain_one_person_per_task(self):
        for task in self.all_date_tasks:
            self.prob += lpSum(self.x[(person, task)] for person in self.people) == 1

    def constrain_assign_only_eligible_people(self):
        for person in self.people:
            for task in self.tasks:
                if not self.is_eligible(person, task):
                    for ineligible_task in self.get_date_tasks(task):
                        self.prob += self.x[(person, ineligible_task)] == 0

    def constrain_do_not_assign_excluded_tasks(self):
        for task1, task2 in self.excluded_tasks:
            for person in self.people:
                if self.is_eligible(person, task1) and self.is_eligible(person, task2):
                    for ineligible_pair in self.schedule.week_aligned_date_tasks_pairs(
                        task1, task2
                    ):
                        if (
                            0 not in ineligible_pair
                            and ineligible_pair[0] != ineligible_pair[1]
                        ):
                            self.prob += (
                                self.x[(person, ineligible_pair[0])]
                                + self.x[(person, ineligible_pair[1])]
                                <= 1
                            )

    def constrain_do_not_over_assign_in_month(self):
        for task in self.tasks:
            eligible = self.get_eligible(task)
            num_eligible = len(eligible)
            for person in eligible:
                date_tasks = self.get_date_tasks(task)

                if num_eligible >= len(date_tasks):
                    # we have an abundance everyone should go at most once
                    #
                    # TODO catchup mechanism, if someone is behind in being assigned to a certain task
                    # we can allow them to go twice in one month by checking if their actual_avg is below some threshold
                    # when compared to the ideal_avg
                    self.prob += (
                        lpSum(self.x[(person, date_task)] for date_task in date_tasks)
                        <= 1
                    )
                else:
                    # Some may repeat, but no one should repeat more than one more than the other people
                    self.prob += (
                        lpSum(self.x[(person, date_task)] for date_task in date_tasks)
                        <= (len(date_tasks) + num_eligible - 1) / num_eligible
                    )
                    # And everyone should get assigned at least once
                    self.prob += (
                        lpSum(self.x[(person, date_task)] for date_task in date_tasks)
                        >= 1
                    )
