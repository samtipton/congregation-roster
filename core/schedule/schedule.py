from itertools import zip_longest
import pandas as pd
import calendar


calendar.setfirstweekday(calendar.SUNDAY)

from core.task import TaskMetadata
from util.helpers import trim_date_task_day, trim_task_name
from collections import OrderedDict


class Schedule:
    def __init__(self, year, month):
        self.year = year
        self.month = month

        self.calendar = calendar.monthcalendar(year, month)
        self.service_times_df = pd.read_csv("data/service-times.csv", index_col=0)

        self.duty_names_df = pd.read_csv("data/duty-names.csv", index_col=0)
        self.duty_names = self.duty_names_df.to_dict()["Name"]  # label?
        self.schedule_duty_order = self.duty_names_df.index.to_list()

        self.duty_codes_df = pd.read_csv("data/duty-codes.csv")
        self.service_days = set(
            self.duty_codes_df.select_dtypes(include="number").iloc[0, :].to_list()
        )

        self.service_names = self.service_times_df.index.to_list()

        self.assignments = None

    def set_assignments(self, assignments):
        # sort keys based on names csv
        sorted_assignments = dict(
            sorted(
                assignments.items(),
                key=lambda x: self.schedule_duty_order.index(trim_task_name(x[0])),
            )
        )

        self.assignments = sorted_assignments
        self.service_assignments = Schedule.get_service_assignments(
            self.service_times_df, self.assignments
        )
        self.service_assignments["weekly"] = Schedule.get_coded_duty_assignments(
            self.duty_codes_df, "w", self.assignments
        )
        self.service_assignments["monthly"] = Schedule.get_coded_duty_assignments(
            self.duty_codes_df, "m", self.assignments
        )

    def get_service_weeks(self):
        return [
            [week[day] for day in self.service_days if week[day]]
            for week in self.calendar
        ]

    def get_duty_codes(self, task):
        trimmed_task = trim_task_name(task)
        return str(self.duty_codes_df.at[0, trimmed_task])

    @staticmethod
    def get_service_assignments(service_times_df, assignments):
        service_assignments = OrderedDict()

        for i, service_time in enumerate(service_times_df.index.to_list()):
            service_duties = set(service_times_df.iloc[i].dropna().index.to_list())
            service_assignments[service_time] = {
                task: assigned
                for task, assigned in assignments.items()
                if trim_task_name(task) in service_duties
            }

        return service_assignments

    @staticmethod
    def get_coded_duty_assignments(duty_codes_df, code, assignments):
        coded_duty = duty_codes_df.loc[0, (duty_codes_df == code).any()].index.to_list()

        return {
            task: assigned
            for task, assigned in assignments.items()
            if trim_task_name(task) in coded_duty
        }

    """
    For tasks that happen per service or weekly, we need to treat them
    as separate tasks that need to be scheduled. We will add
    columns to the data like `{year}-{month}-{day/week}-{task_key}`.

    When using the date_task as an index into another frame, we
    must trim the date_task back to its original form, e.g. `song_leader`
    (task_key)

    duty_codes (TODO rename task_codes) is referenced to modify how we multiple the duties
    - tasks without any codes (not appearing in this df) are assumed
      to be done at each service
    - a code of 'w' represents a weekly duty
    - a code of 'm' represents a monthly duty

    weeks are zero-indexed, days are not, is that confusing?
    TODO - evaluate week task day should be first day of week in month, check entire week
    """

    def get_date_tasks(self, task):
        date_tasks = []
        metadata = TaskMetadata()
        code = metadata.get_duty_code(task)
        if code == "m":
            date_tasks.append(f"{self.year}-{self.month}-{task}")
        elif code == "w":
            num_weeks = len(
                [
                    i
                    for i, week in enumerate(self.calendar)
                    if any(week[day] for day in metadata.service_days)
                ]
            )
            # account for service-less beginning weeks!
            for i in range(num_weeks):
                date_tasks.append(f"{self.year}-{self.month}-{i}-{task}")
        else:
            codes = str(code)
            for week in self.calendar:
                for i, day in enumerate(week):
                    if str(i) in codes and day != 0:
                        date_tasks.append(f"{self.year}-{self.month}-{day}-{task}")
        return date_tasks

    def week_aligned_date_tasks_pairs(self, task1, task2):
        """
        need to pad start to get weekly duties to align correctly
        otherwise we exclude tasks in different weeks
        """
        date_tasks1 = self.get_date_tasks(task1)
        date_tasks2 = self.get_date_tasks(task2)

        task1_codes = TaskMetadata().get_duty_code(task1)
        task2_codes = TaskMetadata().get_duty_code(task2)

        if len(date_tasks1) != len(date_tasks2):
            task1_weekly, task2_weekly = "w" in task1_codes, "w" in task2_codes

            if task1_weekly ^ task2_weekly:
                weekly_date_tasks = date_tasks1 if "w" in task1_codes else date_tasks2
                daily_date_tasks = date_tasks2 if "w" in task1_codes else date_tasks1

                if (
                    len(weekly_date_tasks) > len(daily_date_tasks)
                    and int(trim_date_task_day(daily_date_tasks[0]))
                    not in self.calendar[0]
                ):
                    daily_date_tasks = [0, *daily_date_tasks]

                date_tasks1 = daily_date_tasks
                date_tasks2 = weekly_date_tasks

        return zip_longest(
            date_tasks1,
            date_tasks2,
            fillvalue=0,
        )
