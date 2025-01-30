import pandas as pd
import calendar

calendar.setfirstweekday(calendar.SUNDAY)


class Tasks:
    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.cal = calendar.monthcalendar(year, month)

        # Read eligibility matrix
        self.eligibility_df = pd.read_csv("data/men.csv")
        self.eligibility_df.set_index("name", inplace=True)

        # List of tasks
        self.tasks = list(self.eligibility_df.columns)

        # duty codes
        self.duty_codes = pd.read_csv("data/duty-codes.csv")

        # service_days
        self.service_days = set(
            self.duty_codes.select_dtypes(include="number").iloc[0, :].to_list()
        )

    def get_duty_code(self, task):
        return self.duty_codes.at[0, task]

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

    def get_date_tasks(self, task):
        date_tasks = []
        code = self.duty_codes.at[0, task]
        if code == "m":
            date_tasks.append(f"{self.year}-{self.month}-{task}")
        elif code == "w":
            num_weeks = len(
                [
                    i
                    for i, week in enumerate(self.cal)
                    if any(week[day] for day in self.service_days)
                ]
            )
            # account for service-less beginning weeks!
            for i in range(num_weeks):
                date_tasks.append(f"{self.year}-{self.month}-{i}-{task}")
        else:
            codes = str(code)
            for week in self.cal:
                for i, day in enumerate(week):
                    if str(i) in codes and day != 0:
                        date_tasks.append(f"{self.year}-{self.month}-{day}-{task}")
        return date_tasks
