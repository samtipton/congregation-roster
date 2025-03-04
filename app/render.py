import calendar

from core.roster import Roster
from core.stats import AssignmentStats

calendar.setfirstweekday(calendar.SUNDAY)

from core.schedule import Schedule
from util import *

EMPTY_HEADER_CELL = "<th class='empty'></th>"
EMPTY_DATA_CELL = "<td class='empty'></td>"


def count_day_of_week_in_month(calendar, day_of_week):
    count = 0
    for week in calendar:
        if week[day_of_week] != 0:
            count += 1
    return count


class ScheduleRenderer:
    def __init__(self, schedule: Schedule, roster: Roster, stats: AssignmentStats):
        self.schedule = schedule
        self.calendar = schedule.calendar
        self.roster = roster
        self.stats = stats

    def render_schedule_to_html(
        self,
        interactive=True,
    ):
        """
        TODO show ideal avg delta in cells, e.g. (+.33), if 33% closer to ideal avg after assign

            Will require dynamic re-calculating if the two elements being moved can use a template object with a table
            to hold ideal averages and each man's average

            Could color-code
        """

        # assumes sunday, wednesday only
        self.num_services = max(
            count_day_of_week_in_month(self.calendar, 0),
            count_day_of_week_in_month(self.calendar, 3),
        )

        service_names = self.schedule.service_names

        with open("app/static/style.css", "r") as f:
            style = f.read()

        # TODO jinja template for this?
        # Clean-up non-interactive logic, something about link and script tags,
        # and datalists
        # was making pdf 3000 pages long and throwing off layout
        return f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta name="pdfkit-page-size" content="Legal"/>
                <meta name="pdfkit-orientation" content="Landscape"/>
                <meta http-equiv="Cache-control" content="no-cache, no-store, must-revalidate">
                <meta http-equiv="Pragma" content="no-cache">
                <script src="https://code.jquery.com/jquery-3.7.1.min.js"
                        integrity="sha256-/JqT3SQfawRcv/BIHPThkBvs0OEvtFFmqPF/lYI/Cxo="
                        crossorigin="anonymous">
                </script>
                {'<link rel="shortcut icon" href="/static/favicon.ico">' if interactive else ''}
                {'<script src="/static/schedule.js"></script>' if interactive else ''}
                <style>{style}</style>
            </head>
            <body>
                <div class="overlay mouse-reveal">
                    <button id="download-pdf">Download PDF</button>
                    <button id="toggle-assignment-count">Toggle Assignment Counts</button>
                    <button id="commit-schedule">Commit</button>
                </div>
                <div class="header">
                    <h1>{calendar.month_name[self.schedule.month]}</h1>
                </div>
                {'''
                 ''' 
                 if interactive else ''}
                {self.render_service(service_names[0], 0)}
                <div class="banner dark-background">
                    2nd Service 10:30
                </div>
                {self.render_service(service_names[1], 0, header=False)}
                {self.render_service(service_names[2], 3 )}
                {self.render_weekly_duties()}
                {'<div class="toast" id="toast"></div>' if interactive else ''}
                {'<div class="assignment-map hidden"></div>' if interactive else ''}
                {self.render_data_lists() if interactive else ''}
            </body>
        </html>
        """

    def render_service_header_row(self, service_name, day_of_week):
        # if no services this week, leave out of schedule
        dates = [
            (
                ""
                if not any(week[day] for day in self.schedule.service_days)
                else (
                    f'<th class="day">{week[day_of_week]}</th>'
                    if week[day_of_week]
                    else "<th></th>"
                )
            )
            for i, week in enumerate(self.schedule.calendar)
        ]

        num_dates = len(dates)

        if num_dates < self.num_services:
            dates.append(EMPTY_HEADER_CELL)

        dates_html = EMPTY_DATA_CELL.join([date for date in dates if date])

        return f"""
            <tr>
                <th class="service-name">{service_name}</th>
                {EMPTY_HEADER_CELL}
                {dates_html}
            </tr>
        """

    def render_duty_assignment_cells(self, service, trimmed_duty, day_of_week):

        assignments = [
            (
                ""
                if not any(week[day] for day in self.schedule.service_days)
                else (
                    self.render_assignment_input(
                        trimmed_duty,
                        self.schedule.service_assignments[service][
                            f"{self.schedule.year}-{self.schedule.month}-{week[day_of_week]}-{trimmed_duty}"
                        ],
                        week[day_of_week],
                    )
                    if f"{self.schedule.year}-{self.schedule.month}-{week[day_of_week]}-{trimmed_duty}"
                    in self.schedule.service_assignments[service]
                    and week[day_of_week] != 0
                    else """<td class="empty-duty-cell"></td>"""
                )
            )
            for i, week in enumerate(self.schedule.calendar)
        ]
        assignments = [assignment for assignment in assignments if assignment]
        return EMPTY_DATA_CELL.join(assignments)

    def render_duty_row(self, service, trimmed_duty, day_of_week):
        padding = ""

        return f"""
            <tr>
                <td>{self.schedule.duty_names[trimmed_duty]}</td>
                {EMPTY_DATA_CELL}
                {self.render_duty_assignment_cells(service, trimmed_duty, day_of_week)}
                {padding}
            </tr>
        """

    def render_duty_assignment_rows(self, service, day_of_week):
        trimmed_duty_names = dict.fromkeys(
            [
                trim_task_name(duty)
                for duty in self.schedule.service_assignments[service].keys()
            ]
        )

        return "".join(
            [
                self.render_duty_row(service, trimmed_duty, day_of_week)
                for trimmed_duty in trimmed_duty_names.keys()
            ]
        )

    def render_service(self, service_name, day_of_week, header=True):
        header_html = ""

        if header:
            header_html = f"<thead>{self.render_service_header_row(service_name, day_of_week)}</thead>"

        return f"""
            <table>
                {header_html}
                <tbody>{self.render_duty_assignment_rows(service_name, day_of_week)}</tbody>
            </table>
        """

    def render_assignment_input(self, trimmed_duty, assigned_person, data_suffix):
        delta = self.stats.assignment_delta[trimmed_duty][assigned_person]

        if abs(delta) >= 100:
            num_triangles = 3
        elif abs(delta) >= 50:
            num_triangles = 2
        else:
            num_triangles = 1

        if delta == -100 or delta < 0.000001:
            num_triangles = 0

        triangle_class = "green-triangle" if delta < 0 else "red-triangle"
        triangle = f'<div class="{triangle_class}"></div>'
        # place this back in html
        # {triangle * num_triangles}
        return f"""
                <td class="duty-cell" draggable="true" data-duty="{self.schedule.year}-{self.schedule.month}-{data_suffix}-{trimmed_duty}">
                    <div style="position: relative;">
                        <input class="assignment-input keep-datalist" type="text" list="{trimmed_duty}" value="{assigned_person}">
                        <div style="position: absolute; display: flex; right: 5px; bottom: 1px;">
                        </div>
                    </div>
                </td>
                """

    def render_weekly_duty_cell(self, trimmed_duty):
        service_assignments = self.schedule.service_assignments["weekly"]

        assignments = [
            (
                f"""
                {self.render_assignment_input(trimmed_duty, service_assignments[f'{self.schedule.year}-{self.schedule.month}-{i}-{trimmed_duty}'], i)}
                """
                if f"{self.schedule.year}-{self.schedule.month}-{i}-{trimmed_duty}"
                in service_assignments
                else ""
            )
            for i in self.schedule.first_calendar_days_for_each_week
        ]

        return EMPTY_DATA_CELL.join([a for a in assignments if a])

    def render_weekly_duty_row(self, trimmed_duty):
        padding = ""

        return f"""
            <tr>
                <td>{self.schedule.duty_names[trimmed_duty]}</td>
                {EMPTY_DATA_CELL}
                {self.render_weekly_duty_cell(trimmed_duty)}
                {padding}
            </tr>
        """

    def render_weekly_duty_assignment_rows(self):
        trimmed_duty_names = dict.fromkeys(
            [
                trim_task_name(duty)
                for duty in self.schedule.service_assignments["weekly"].keys()
            ]
        )

        return "".join(
            [
                self.render_weekly_duty_row(trimmed_duty)
                for trimmed_duty in trimmed_duty_names.keys()
            ]
        )

    def render_weekly_duties(self):
        if self.schedule.service_assignments["weekly"]:
            return f"""<table><tbody>{self.render_weekly_duty_assignment_rows()}</tbody></table>"""
        else:
            return ""

    def render_monthly_assignments(self):
        # may have empty first week, every month has at least 2 weeks
        if self.schedule.service_assignments["monthly"]:
            return "".join(
                [
                    f"""
                        <tr>
                            <td class="monthly">{self.schedule.duty_names[duty]}</td>
                            <td class="assignment">{assignee}</td>
                        </tr>"""
                    for duty, assignee in self.schedule.service_assignments[
                        "monthly"
                    ].items()
                ]
            )
        else:
            return ""

    def render_monthly_duties(self):
        return f"""
            <table>
                <tbody>
                    {self.render_monthly_assignments()}
                </tbody>
            </table>
        """

    def render_data_lists(self):
        # ordered by DECREASING assignment_delta
        lists = []
        for task in self.roster.task_keys:
            eligible = set(self.roster.get_eligible(task))
            delta_sort = sorted(
                [
                    item
                    for item in self.stats.assignment_delta[task].items()
                    if item[0] in eligible
                ],
                key=lambda item: item[1],
            )
            lists.append(
                f'\n<datalist id="{task}">\n{"\n".join([f'<option value="{k}"></option>' for k,v in delta_sort])}\n</datalist>'
            )

        return "\n".join(lists)
