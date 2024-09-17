import pandas as pd
import calendar
from core.roster import Roster

calendar.setfirstweekday(calendar.SUNDAY)

from util.helpers import trim_task_name, trim_task_date
from collections import OrderedDict
from itertools import zip_longest


class Schedule:
    def __init__(self, year, month, roster: Roster):
        self.year = year
        self.month = month
        self.roster = roster

        self.calendar = calendar.monthcalendar(year, month)
        self.service_times_df = pd.read_csv("data/service-times.csv", index_col=0)

        self.duty_names_df = pd.read_csv("data/duty-names.csv", index_col=0)
        # label?
        self.duty_names = self.duty_names_df.to_dict()["Name"]
        self.schedule_duty_order = self.duty_names_df.index.to_list()

        self.duty_codes_df = pd.read_csv("data/duty-codes.csv")
        self.service_days = set(
            self.duty_codes_df.select_dtypes(include="number").iloc[0, :].to_list()
        )

        self.service_names = self.service_times_df.index.to_list()

        self.get_date_tasks = Schedule.create_get_date_tasks(
            calendar.monthcalendar(year, month), self.duty_codes_df, self.service_days
        )
        self.all_date_tasks = [
            dt for task in self.roster.tasks for dt in self.get_date_tasks(task)
        ]

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

    @classmethod
    def create_get_date_tasks(cls, cal, duty_codes_df, service_days):
        """
        For duties that happen per service or weekly, we need to treat them
        as separate duties that need to be scheduled. We will add
        columns to the data like `song_leader-{day/week}`.

        When using the column name as an index into another frame, we
        must trim the column name back to its original form, e.g. `song_leader`

        duty_codes is referenced to modify how we multiple the duties
        - duties without any codes (not appearing in this df) are assumed
          to be done at each service
        - a code of 'w' represents a weekly duty
        - a code of 'm' represents a monthly duty

        weeks are zero-indexed, days are not, is that confusing?
        """

        def get_date_tasks(task):
            date_tasks = []
            code = duty_codes_df.at[0, task]
            if code == "m":
                date_tasks.append(task)
            elif code == "w":
                num_weeks = len(
                    [
                        i
                        for i, week in enumerate(cal)
                        if any(week[day] for day in service_days)
                    ]
                )
                # account for serviceless beginning weeks!
                for i in range(num_weeks):
                    date_tasks.append(f"{task}-{i}")
            else:
                codes = str(code)
                for week in cal:
                    for i, day in enumerate(week):
                        if str(i) in codes and day != 0:
                            date_tasks.append(f"{task}-{day}")
            return date_tasks

        return get_date_tasks

    def week_aligned_date_tasks_pairs(self, task1, task2):
        # need to pad start to get weekly duties to align correctly
        # otherwise we exclude tasks in different weeks
        # should go in schedule
        task1_dates = self.get_date_tasks(task1)
        task2_dates = self.get_date_tasks(task2)

        task1_codes = self.get_duty_codes(task1)
        task2_codes = self.get_duty_codes(task2)

        if len(task1_dates) != len(task2_dates):
            task1_weekly, task2_weekly = "w" in task1_codes, "w" in task2_codes

            if task1_weekly ^ task2_weekly:
                weekly_task_dates = task1_dates if "w" in task1_codes else task2_dates
                daily_task_dates = task2_dates if "w" in task1_codes else task1_dates

                if (
                    len(weekly_task_dates) > len(daily_task_dates)
                    and int(trim_task_date(daily_task_dates[0])) not in self.calendar[0]
                ):
                    daily_task_dates = [0, *daily_task_dates]

                task1_dates = daily_task_dates
                task2_dates = weekly_task_dates

        return zip_longest(
            task1_dates,
            task2_dates,
            fillvalue=0,
        )
