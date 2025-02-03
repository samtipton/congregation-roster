import calendar
import pandas as pd

from util.decorators import singleton

calendar.setfirstweekday(calendar.SUNDAY)


@singleton
class TaskMetadata:
    def __init__(self):
        # duty codes
        # TODO rename task codes
        self.duty_codes = pd.read_csv("data/duty-codes.csv")

        # service_days
        self.service_days = set(
            self.duty_codes.select_dtypes(include="number").iloc[0, :].to_list()
        )

    def get_duty_code(self, task_key):
        return str(self.duty_codes.at[0, task_key])


class Task:
    def __init__(self, key, code):
        self.key = key
        self.code = code


class Tasks:
    """classy wrapper list of Tasks"""

    def __new__(cls):
        metadata = TaskMetadata()
        return [
            Task(key, code)
            for key, code in metadata.duty_codes.loc[0].to_dict().items()
        ]
