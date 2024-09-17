from logging import info
import os
import calendar
import pandas as pd
from util import trim_task_name
from util.helpers import write_dict_to_file

calendar.setfirstweekday(calendar.SUNDAY)


class Roster:
    def __init__(self, assignment_history_file):
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

        # Duty codes
        self.duty_codes_df = pd.read_csv("data/duty-codes.csv")

        # Rounds
        self.rounds_df = pd.read_csv("data/rounds.csv")
        self.rounds_df.set_index("name", inplace=True)
        self.rounds_df.fillna(0, inplace=True)
        self.rounds_df[self.rounds_df != "name"].astype("int")

        # Service days
        self.service_days = set(
            self.duty_codes_df.select_dtypes(include="number").iloc[0, :].to_list()
        )

        # Historical assignment frequency
        self.assignment_history_file = assignment_history_file
        self.initialize_history(assignment_history_file)

        # Number of scheduling rounds this roster has undergone
        self.rounds = self.assignment_history_df.at[self.people[0], "Rounds"]

        # ideal avg for each task is perfect round robin or 1/(# eligible for task)
        self.ideal_avg = {
            task: 1 / count
            for task, count in self.eligibility_df.sum(axis=0).to_dict().items()
        }

        # if person is chosen for task, compute the difference between ideal and avg
        self.assignment_delta = {person: {} for person in self.people}

        # actual avg per person per task
        # could this be done in a jinja script tag?
        self.actual_avg = pd.DataFrame(index=self.people, columns=self.tasks)
        for person in self.people:
            for task in self.tasks:
                self.actual_avg.at[person, task] = self.assignment_history_df.at[
                    person, task
                ] / (max(self.rounds_df.at[person, task], 1))

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

    def record_assignments(self, assignments, rounds):
        # TODO rounds should be recorded per tasks
        # not every week has both services, need a way of tracking this
        # to compute average correctly
        for task, person in assignments.items():
            self.assignment_history_df.loc[person, trim_task_name(task)] += 1

        self.assignment_history_df.to_csv(self.assignment_history_file)
        self.increment_rounds()

    def remove_assignments(self, assignments):
        if self.assignment_history_df["Rounds"].all() == 0:
            raise ValueError("Cannot remove_assignments from an empty history")

        for task, person in assignments.items():
            if self.assignment_history_df.loc[person, trim_task_name(task)] != 0:
                self.assignment_history_df.loc[person, trim_task_name(task)] -= 1

        self.assignment_history_df.to_csv(self.assignment_history_file)
        self.decrement_rounds()

    def increment_rounds(self):
        for person, task in self.eligible:
            self.rounds_df.at[person, task] += 1
        self.rounds_df.to_csv("data/rounds.csv")

    def decrement_rounds(self):
        for person, task in self.eligible:
            self.rounds_df.at[person, task] -= 1
        self.rounds_df.to_csv("data/rounds.csv")

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
