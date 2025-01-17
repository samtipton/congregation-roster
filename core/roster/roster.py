from logging import info
import os
import calendar
import pandas as pd
from util import trim_task_name
from util.helpers import write_dict_to_file

calendar.setfirstweekday(calendar.SUNDAY)


class Roster:
    def __init__(self, assignment_history_file, rounds_history_file="data/rounds.csv"):
        # Read eligibility matrix
        self.eligibility_df = pd.read_csv("data/men.csv")
        self.eligibility_df.set_index("name", inplace=True)

        # List of people and tasks
        self.people = self.eligibility_df.index
        self.tasks = list(self.eligibility_df.columns)

        # Read exclusions matrix
        self.exclusions_df = pd.read_csv("data/exclusions.csv", index_col=0)
        self.exclusions_df.fillna(0, inplace=True)

        # set of exclusion pairs, use is_eligible to ignore ordering
        self.excluded_tasks = self.create_excluded_tasks_cache()

        # Read biases matrix
        if os.path.isfile("data/biases.csv"):
            self.bias_df = pd.read_csv("data/biases.csv", index_col=0)
            self.bias_df.fillna(0, inplace=True)
            self.bias = self.bias_df.to_dict()
        else:
            self.bias_df = self.eligibility_df.copy()
            self.bias_df[:] = 0
            self.bias = self.bias_df.to_dict()

        # Duty codes
        self.duty_codes_df = pd.read_csv("data/duty-codes.csv")

        # Rounds
        self.rounds_history_file = rounds_history_file
        self.initialize_rounds(rounds_history_file)
        self.rounds_df = pd.read_csv(rounds_history_file)
        self.rounds_df.set_index("name", inplace=True)
        self.rounds_df.fillna(0, inplace=True)

        # Service days
        self.service_days = set(
            self.duty_codes_df.select_dtypes(include="number").iloc[0, :].to_list()
        )

        # Historical assignment frequency
        self.assignment_history_file = assignment_history_file
        self.initialize_history(assignment_history_file)

        # ideal avg for each task is perfect round robin or 1/(# eligible for task)
        self.ideal_avg = {
            task: 1 / count
            for task, count in self.eligibility_df.sum(axis=0).to_dict().items()
        }

        # add new persons to rounds/history
        # set their assignment history to 1 so they do not get biased in first schedule
        for person in self.people:
            if person not in self.assignment_history_df.index:
                self.assignment_history_df.loc[person] = 0
                self.assignment_history_df.loc[person] = self.assignment_history_df.loc[
                    person
                ] = [
                    1 if self.is_eligible(person, task) else 0
                    for task in self.assignment_history_df.columns
                ]

            if person not in self.rounds_df.index:
                self.rounds_df.loc[person] = 1

        # if person is chosen for task, compute the difference between ideal and avg
        # for DEBUG
        # TODO: remove
        self.assignment_delta = {person: {} for person in self.people}

        # actual avg per person per task
        # could this be done in a jinja script tag?
        self.actual_avg = pd.DataFrame(index=self.people, columns=self.tasks)
        for person in self.people:
            for task in self.tasks:
                self.actual_avg.at[person, task] = self.assignment_history_df.at[
                    person, task
                ] / (max(self.rounds_df.at[person, task], 1))

                # TODO: here we could reference a separate dataframe to deboost
                # certain people from certain tasks by either:
                # 1. increasing actual_avg by some percentage of the delta
                # 2. decreasing number of rounds, will boost average
                # 3. increasing their assignment history count some percentage of itself

                # Does it matter if the changed value is not scaled in a coherent fashion?
                # Yes - it might take them awhile to be assigned again

                self.assignment_delta[person][task] = round(
                    (
                        (self.actual_avg.at[person, task] - self.ideal_avg[task])
                        / self.ideal_avg[task]
                    )
                    * 100,
                    2,
                )

        # cache set of eligible (person, task) tuples
        self.eligible = {
            (person, task)
            for person in self.people
            for task in self.tasks
            if self.is_eligible(person, task)
        }

        write_dict_to_file(self.ideal_avg, "/Users/stipton/Desktop/avgideal.json")
        write_dict_to_file(
            self.actual_avg.to_dict(), "/Users/stipton/Desktop/avgactual.json"
        )
        write_dict_to_file(self.assignment_delta, "/Users/stipton/Desktop/delta.json")

    def initialize_history(self, assignment_history_file):
        if os.path.exists(assignment_history_file):
            self.assignment_history_df = pd.read_csv(
                assignment_history_file, index_col=0
            )
        else:
            self.assignment_history_df = pd.DataFrame(
                0, index=self.people, columns=self.tasks
            )

            self.assignment_history_df.to_csv(assignment_history_file)

    def initialize_rounds(self, rounds_history_file):
        if os.path.exists(rounds_history_file):
            self.rounds_df = pd.read_csv(rounds_history_file, index_col=0)
        else:
            self.rounds_df = pd.DataFrame(0, index=self.people, columns=self.tasks)

            self.rounds_df.to_csv(rounds_history_file)

    def record_assignments(self, assignments):
        for task, person in assignments.items():
            self.assignment_history_df.loc[person, trim_task_name(task)] += 1

        self.assignment_history_df.to_csv(self.assignment_history_file)
        self.increment_rounds(assignments)

    def remove_assignments(self, assignments):
        if self.assignment_history_df["Rounds"].all() == 0:
            raise ValueError("Cannot remove_assignments from an empty history")

        for task, person in assignments.items():
            if self.assignment_history_df.loc[person, trim_task_name(task)] != 0:
                self.assignment_history_df.loc[person, trim_task_name(task)] -= 1

        self.assignment_history_df.to_csv(self.assignment_history_file)
        self.decrement_rounds(assignments)

    def increment_rounds(self, assignments):
        for date_task in assignments.keys():
            trimmed_task = trim_task_name(date_task)
            for person in self.get_eligible(trimmed_task):
                self.rounds_df.at[person, trimmed_task] += 1

        self.rounds_df.to_csv(self.rounds_history_file)

    def decrement_rounds(self, assignments):
        for date_task in assignments.keys():
            trimmed_task = trim_task_name(date_task)
            for person in self.get_eligible(trimmed_task):
                self.rounds_df.at[person, trimmed_task] -= 1

        self.rounds_df.to_csv(self.rounds_history_file)

    def is_eligible(self, person, task) -> bool:
        return self.eligibility_df.loc[person, task] == 1.0

    def get_eligible(self, task):
        return self.eligibility_df[task].dropna().index.to_list()

    def is_excluded(self, task1, task2):
        return (task1, task2) in self.excluded_tasks or (
            task2,
            task1,
        ) in self.excluded_tasks

    def create_excluded_tasks_cache(self):
        excluded_tasks = set()
        for task1 in self.tasks:
            for task2 in self.tasks:
                if (
                    self.exclusions_df.loc[task1, task2] == 1
                    or self.exclusions_df.loc[task2, task1] == 1
                ):
                    excluded_tasks.add((task1, task2))

        return excluded_tasks
