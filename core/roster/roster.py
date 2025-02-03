import calendar
import pandas as pd
from core.task import Tasks

calendar.setfirstweekday(calendar.SUNDAY)


class Roster:
    def __init__(self):
        # Read eligibility matrix
        self.eligibility_df = pd.read_csv("data/prefs.csv")
        self.eligibility_df.set_index("name", inplace=True)

        # List of people and tasks
        self.people = self.eligibility_df.index
        self.tasks = Tasks()
        self.task_keys = [task.key for task in self.tasks]

        self.excluded_tasks = self.create_excluded_tasks_cache()

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
        """set of exclusion pairs, use is_eligible to ignore ordering"""

        # Read exclusions matrix
        exclusions_df = pd.read_csv("data/exclusions.csv", index_col=0)
        exclusions_df.fillna(0, inplace=True)

        excluded_tasks = set()

        for task1 in self.task_keys:
            for task2 in self.task_keys:
                if (
                    self.exclusions_df.loc[task1, task2] == 1
                    or self.exclusions_df.loc[task2, task1] == 1
                ):
                    excluded_tasks.add((task1, task2))

        return excluded_tasks
