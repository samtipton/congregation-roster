from collections import OrderedDict
from pulp import *

from core.history import AssignmentHistory
from core.roster import Roster
from core.schedule import Schedule
from core.stats import AssignmentStats, AssignmentBiases
from util import *
from itertools import chain


class SchedulingProblem:
    def __init__(self, schedule: Schedule, roster: Roster, history: AssignmentHistory):
        self.schedule = schedule
        self.roster = roster

        self.people = self.roster.people

        self.tasks = self.roster.tasks
        self.task_keys = [task.key for task in self.tasks]

        stats = AssignmentStats(roster, history)
        self.excluded_tasks = self.roster.excluded_tasks
        self.is_excluded = self.roster.is_excluded
        self.get_eligible = self.roster.get_eligible

        self.is_eligible = self.roster.is_eligible
        self.ideal_avg = stats.ideal_avg
        self.actual_avg = stats.actual_avg
        self.bias = AssignmentBiases().bias

        self.get_date_tasks = self.schedule.get_date_tasks

        # date tasks for month
        self.all_date_tasks = [
            dt for task_key in self.task_keys for dt in self.get_date_tasks(task_key)
        ]

        self.historical_assignments_vars = list(history.assignment_history.items())

        # all possible assignment pair (person, task) combinations for month
        assignment_vars = chain(
            (
                (date_task, person)
                for person in self.people
                for date_task in self.all_date_tasks
                # if self.is_eligible(person, trim_task_name(date_task))
            ),
            self.historical_assignments_vars,
        )

        self.x = LpVariable.dicts(
            "assignment",
            assignment_vars,
            cat="Binary",
        )

        self.set_objective_function()
        self.constrain_past_assignments()
        self.constrain_one_person_per_task()
        self.constrain_assign_only_eligible_people()
        self.constrain_do_not_assign_excluded_tasks()
        self.constrain_do_not_over_assign_in_month()
        self.constrain_do_not_over_assign_new_people()
        self.constrain_month_boundary_assignments()

    def solve(self, verbose=False):
        result = self.prob.solve(PULP_CBC_CMD(msg=verbose))

        # TODO I think there is some unnecessary code in here
        assignment = {}
        for person in self.people:
            assigned_tasks = [
                task
                for task in self.all_date_tasks
                if self.x[(task, person)].varValue == 1
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
                    * self.bias_value(person, date_task)
                )
            )
            # 1 if assigned, 0 otherwise
            * self.x[(date_task, person)]
            for person in self.people
            for date_task in self.all_date_tasks
            # if self.is_eligible(person, trim_task_name(date_task))
        )

    def constrain_past_assignments(self):
        """Constrain all past assignments variables to 1"""
        for task, person in self.historical_assignments_vars:
            self.prob += self.x[(task, person)] == 1

    def constrain_one_person_per_task(self):
        for task in self.all_date_tasks:
            self.prob += (
                lpSum(
                    self.x[(task, person)]
                    for person in self.people
                    # if self.is_eligible(person, trim_task_name(task))
                )
                == 1
            )

    # TODO try only introducing vars with eligible people
    def constrain_assign_only_eligible_people(self):
        for person in self.people:
            for task in self.task_keys:
                if not self.is_eligible(person, task):
                    for ineligible_task in self.get_date_tasks(task):
                        self.prob += self.x[(ineligible_task, person)] == 0

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
                                self.x[(ineligible_pair[0], person)]
                                + self.x[(ineligible_pair[1], person)]
                                <= 1
                            )

    def constrain_do_not_over_assign_in_month(self):
        for task in self.task_keys:
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
                        lpSum(self.x[(date_task, person)] for date_task in date_tasks)
                        <= 1
                    )
                else:
                    # Some may repeat, but no one should repeat more than one more than the other people
                    self.prob += (
                        lpSum(self.x[(date_task, person)] for date_task in date_tasks)
                        <= (len(date_tasks) + num_eligible - 1) / num_eligible
                    )
                    # And everyone should get assigned at least once
                    self.prob += (
                        lpSum(self.x[(date_task, person)] for date_task in date_tasks)
                        >= 1
                    )

    def constrain_do_not_over_assign_new_people(self):
        """TODO need to do more here"""
        zero_average_people = self.actual_avg.index[
            (self.actual_avg == 0).all(axis=1)
        ].tolist()

        for person in zero_average_people:
            self.prob += (
                lpSum(self.x[(date_task, person)] for date_task in self.all_date_tasks)
                <= 2
            )

    def constrain_month_boundary_assignments(self):
        """
        TODO do not double assign person in next week if there are multiple choices
        month boundary doesn't matter rename method
        """
        pass

    def bias_value(self, person, date_task):
        bias_for_task = self.bias[trim_task_name(date_task)]

        if person not in bias_for_task:
            return 1

        bias_value = bias_for_task[person]

        if bias_value == 1:
            return 1
        elif bias_value < 1:
            return 1 / max(1 - bias_value, 0.01)
        elif bias_value > 1:
            return 1 - bias_value
