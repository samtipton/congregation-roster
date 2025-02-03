import json
import re
import pandas as pd
from datetime import datetime
from core.task import TaskMetadata
from util.helpers import trim_task_date, trim_task_name, write_dict_to_file

DATE_FORMAT = "%Y-%m-%d"


class AssignmentHistory:
    def __init__(self, assignment_history_file):
        self.assignment_history_file = assignment_history_file

        with open(assignment_history_file, "r") as file:
            self.assignment_history = json.load(file)

        # TODO don't need
        write_dict_to_file(
            self.assignment_history, "/Users/stipton/Desktop/history.json"
        )

        self.pref_update_history = pd.read_csv(
            "data/prefs_update_history.csv", index_col=0
        )
        self.pref_update_history.fillna("", inplace=True)
        self.pref_update_history = self.pref_update_history.to_dict(orient="index")

    def record_assignments(self, assignments):
        self.assignment_history.update(assignments)

        write_dict_to_file(self.assignment_history, self.assignment_history_file)
        # with open(self.assignment_history_file, "w") as f:
        #     json.dump(self.assignment_history, f, indent=4, sort_keys=True, default=str)

    def remove_assignments(self, assignments):
        for key in assignments:
            self.assignment_history.pop(key, None)

        write_dict_to_file(self.assignment_history, self.assignment_history_file)
        # with open(self.assignment_history_file, "w") as f:
        #     json.dump(self.assignment_history, f, indent=4, sort_keys=True, default=str)

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
        TODO this does not take into account eligibility changes will need new dataset
        """
        # TODO memoize
        if not self.pref_update_history[person][task_key]:
            return 0

        task_metadata = TaskMetadata()

        start_date = datetime.strptime(
            self.pref_update_history[person][task_key], DATE_FORMAT
        ).date()

        rounds = len(
            [
                k
                for k in self.assignment_history.keys()
                if trim_task_name(k) == task_key
                and datetime.strptime(
                    trim_task_date(self.shift_week_task_date(k, task_metadata)),
                    DATE_FORMAT,
                ).date()
                >= start_date
            ]
        )

        return rounds

    def shift_week_task_date(self, date_task, task_metadata: TaskMetadata):
        """
        corrects 'week' and 'month'dates (e.g. 2025-1-0, 2025-1) to reflect beginning of corresponding week
        TODO could we rely only on code and use properly formatted dates everywhere,
        defaulting to 1st day of week or month?
        """
        code = task_metadata.get_duty_code(trim_task_name(date_task))

        if code == "w":
            match = re.search(r"(\d{4}-\d{1,2})-[0-4]-(\w+)", date_task)
            if match:
                return f"{match.group(1)}-1-{match.group(2)}"
            else:
                raise ValueError(f"unexpected week date_task format: {date_task}")
        elif code == "m":
            match = re.search(r"(\d{4}-\d{1,2})-(\w+)", date_task)
            if match:
                return f"{match.group(1)}-1-{match.group(2)}"
            else:
                raise ValueError(f"unexpected month date_task format: {date_task}")
        else:
            return date_task
