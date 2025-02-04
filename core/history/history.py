import calendar
import json
import pandas as pd
from datetime import datetime
from util.helpers import (
    trim_task_date,
    trim_task_name,
    write_dict_to_file,
)

calendar.setfirstweekday(calendar.SUNDAY)
DATE_FORMAT = "%Y-%m-%d"


class AssignmentHistory:
    def __init__(self, assignment_history_file):
        self.assignment_history_file = assignment_history_file

        with open(assignment_history_file, "r") as file:
            self.assignment_history = json.load(file)

        self.pref_update_history = pd.read_csv(
            "data/prefs_update_history.csv", index_col=0
        )
        self.pref_update_history.fillna("", inplace=True)
        self.pref_update_history = self.pref_update_history.to_dict(orient="index")

    def record_assignments(self, assignments):
        self.assignment_history.update(assignments)
        write_dict_to_file(self.assignment_history, self.assignment_history_file)

    def remove_assignments(self, assignments):
        for key in assignments:
            self.assignment_history.pop(key, None)
        write_dict_to_file(self.assignment_history, self.assignment_history_file)

    def count_eligible_months(self, person, task_key, end_year, end_month):
        """
        How many months have passed from being eligible for task until end_year/end_month
        """
        if not self.pref_update_history[person][task_key]:
            return 0

        start_date = datetime.strptime(
            self.pref_update_history[person][task_key], DATE_FORMAT
        ).date()

        start_year = int(start_date.year)
        start_month = int(start_date.month)

        if start_year < end_year or (
            start_year == end_year and end_month < start_month
        ):
            return 0

        return (end_year - start_year) * 12 + (end_month - start_month)

    def rounds(self, person, task_key):
        """
        count how many rounds person has been eligible for task_key since they last updated prefs
        """
        # TODO memoize
        if not self.pref_update_history[person][task_key]:
            return 0

        start_date = datetime.strptime(
            self.pref_update_history[person][task_key], DATE_FORMAT
        ).date()

        rounds = len(
            [
                k
                for k in self.assignment_history.keys()
                if trim_task_name(k) == task_key
                and datetime.strptime(
                    trim_task_date(k),
                    DATE_FORMAT,
                ).date()
                >= start_date
            ]
        )

        return rounds
