import os
import calendar
import pandas as pd
from helpers import trim_task_name

calendar.setfirstweekday(calendar.SUNDAY)


class Roster:
    def __init__(self, assignment_history_file):
        # Read eligibility matrix
        self.eligibility_df = pd.read_csv("men.csv")
        self.eligibility_df.set_index("name", inplace=True)

        # Read exclusions matrix
        self.exclusions_df = pd.read_csv("exclusions.csv", index_col=0)
        self.exclusions_df.fillna(0, inplace=True)

        # Duty codes
        self.duty_codes_df = pd.read_csv("duty-codes.csv")

        # Service days
        self.service_days = set(
            self.duty_codes_df.select_dtypes(include="number").iloc[0, :].to_list()
        )

        # Variables

        # List of people and tasks
        self.people = self.eligibility_df.index

        self.tasks = list(self.eligibility_df.columns)

        # Historical assignment frequency
        self.assignment_history_file = assignment_history_file
        self.initialize_history(assignment_history_file)

        # should try to minimize the deviation from the ideal average
        self.ideal_avg = {
            task: 1 / count
            for task, count in self.eligibility_df.sum(axis=0).to_dict().items()
        }

        # actual assignments per person per task
        self.actual_avg = pd.DataFrame(index=self.people, columns=self.tasks)
        for person in self.people:
            for task in self.tasks:
                self.actual_avg.loc[person, task] = self.assignment_history_df.loc[
                    person, task
                ] / max(self.assignment_history_df.loc[person, "Rounds"], 1)

    def initialize_history(self, assignment_history_file):
        if os.path.exists(assignment_history_file):
            self.assignment_history_df = pd.read_csv(
                assignment_history_file, index_col=0
            )
        else:
            self.assignment_history_df = pd.DataFrame(
                0, index=self.people, columns=self.tasks
            )
            self.assignment_history_df["Rounds"] = 0

        self.assignment_history_df.to_csv(assignment_history_file)

    def record_assignments(self, assignments):
        for task, person in assignments.items():
            self.assignment_history_df.loc[person, trim_task_name(task)] += 1

        self.assignment_history_df["Rounds"] += 1
        self.assignment_history_df.to_csv(self.assignment_history_file)

    def remove_assignments(self, assignments):
        if self.assignment_history_df["Rounds"].all() == 0:
            raise ValueError("Cannot remove_assignments from an empty history")

        for task, person in assignments.items():
            self.assignment_history_df.loc[person, trim_task_name(task)] -= 1

        self.assignment_history_df["Rounds"] -= 1
        self.assignment_history_df.to_csv(self.assignment_history_file)

    def is_eligible(self, person, task) -> bool:
        return self.eligibility_df.loc[person, task] == 1.0

    def get_eligible(self, task):
        return self.eligibility_df[task].dropna().index.to_list()

    def is_excluded(self, task1, task2):
        return (
            self.exclusions_df.loc[task1, task2] == 1
            or self.exclusions_df.loc[task2, task1] == 1
        )
