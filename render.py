import calendar

calendar.setfirstweekday(calendar.SUNDAY)

from schedule import Schedule
from helpers import *

EMPTY_HEADER_CELL = "<th class='empty'></th>"
EMPTY_DATA_CELL = "<td class='empty'></td>"


def count_day_of_week_in_month(calendar, day_of_week):
    count = 0
    for week in calendar:
        if week[day_of_week] != 0:
            count += 1
    return count


def render_service_header_row(
    service_name, day_of_week, schedule: Schedule, max_num_services
):
    # if no services this week, leave out of schedule
    dates = [
        (
            ""
            if not any(week[day] for day in schedule.service_days)
            else (
                f'<th class="day">{week[day_of_week]}</th>'
                if week[day_of_week]
                else "<th></th>"
            )
        )
        for i, week in enumerate(schedule.calendar)
    ]

    num_dates = len(dates)

    if num_dates < max_num_services:
        dates.append(EMPTY_HEADER_CELL)

    dates_html = EMPTY_DATA_CELL.join([date for date in dates if date])

    return f"""
        <tr>
            <th class="service-name">{service_name}</th>
            {EMPTY_HEADER_CELL}
            {dates_html}
        </tr>
    """


def render_duty_assignment_cells(
    service, trimmed_duty, num_services, schedule: Schedule, day_of_week
):

    assignments = [
        (
            ""
            if not any(week[day] for day in schedule.service_days)
            else (
                f"""
                <td class="duty-cell" draggable="true" data-duty="{f'{trimmed_duty}-{week[day_of_week]}'}">
                    <input type="text" value="{schedule.service_assignments[service][f'{trimmed_duty}-{week[day_of_week]}']}">
                </td>
                """
                if f"{trimmed_duty}-{week[day_of_week]}"
                in schedule.service_assignments[service]
                and week[day_of_week] != 0
                else """<td class="empty-duty-cell"></td>"""
            )
        )
        for i, week in enumerate(schedule.calendar)
    ]
    assignments = [assignment for assignment in assignments if assignment]
    return EMPTY_DATA_CELL.join(assignments)


def render_duty_row(service, trimmed_duty, schedule, day_of_week, num_services):
    padding = ""

    return f"""
        <tr>
            <td>{schedule.duty_names[trimmed_duty]}</td>
            {EMPTY_DATA_CELL}
            {render_duty_assignment_cells(service, trimmed_duty, num_services, schedule, day_of_week)}
            {padding}
        </tr>
    """


def render_duty_assignment_rows(service, day_of_week, schedule, num_services):
    trimmed_duty_names = dict.fromkeys(
        [trim_task_name(duty) for duty in schedule.service_assignments[service].keys()]
    )

    return "".join(
        [
            render_duty_row(service, trimmed_duty, schedule, day_of_week, num_services)
            for trimmed_duty in trimmed_duty_names.keys()
        ]
    )


def render_service(service_name, day_of_week, schedule, max_num_services, header=True):
    header_html = ""

    if header:
        header_html = f"<thead>{render_service_header_row(service_name, day_of_week, schedule, max_num_services)}</thead>"

    return f"""
        <table>
            {header_html}
            <tbody>{render_duty_assignment_rows(service_name, day_of_week, schedule, max_num_services)}</tbody>
        </table>
    """


def render_weekly_duty_cell(schedule, trimmed_duty):
    service_assignments = schedule.service_assignments["weekly"]

    assignments = [
        (
            f"""
            <td class="duty-cell" draggable="true" data-duty="{f'{trimmed_duty}-{i}'}">
                <input type="text" value="{service_assignments[f'{trimmed_duty}-{i}']}">
            </td>
            """
            if f"{trimmed_duty}-{i}" in service_assignments
            else ""
        )
        for i, week in enumerate(schedule.calendar)
    ]

    return EMPTY_DATA_CELL.join([a for a in assignments if a])


def render_weekly_duty_row(schedule, trimmed_duty):
    padding = ""

    return f"""
        <tr>
            <td>{schedule.duty_names[trimmed_duty]}</td>
            {EMPTY_DATA_CELL}
            {render_weekly_duty_cell(schedule, trimmed_duty)}
            {padding}
        </tr>
    """


def render_weely_duty_assignment_rows(schedule: Schedule):
    trimmed_duty_names = dict.fromkeys(
        [trim_task_name(duty) for duty in schedule.service_assignments["weekly"].keys()]
    )

    return "".join(
        [
            render_weekly_duty_row(schedule, trimmed_duty)
            for trimmed_duty in trimmed_duty_names.keys()
        ]
    )


def render_weeky_duties(schedule: Schedule):
    if schedule.service_assignments["weekly"]:
        return f"""<table><tbody>{render_weely_duty_assignment_rows(schedule)}</tbody></table>"""
    else:
        return ""


def render_monthly_assignments(schedule: Schedule):
    # may have empty first week, every month has at least 2 weeks
    if schedule.service_assignments["monthly"]:
        return "".join(
            [
                f"""
                    <tr>
                        <td class="monthly">{schedule.duty_names[duty]}</td>
                        <td class="assignment">{assignee}</td>
                    </tr>"""
                for duty, assignee in schedule.service_assignments["monthly"].items()
            ]
        )
    else:
        return ""


def render_monthly_duties(schedule: Schedule):
    return f"""
        <table>
            <tbody>
                {render_monthly_assignments(schedule)}
            </tbody>
        </table>
    """


def read_schedule_javascript():
    with open("schedule.js") as f:
        return f.read()


def render_schedule_to_html(schedule: Schedule):
    cal = calendar.monthcalendar(schedule.year, schedule.month)

    # assumes sunday, wednesday only
    num_services = max(
        count_day_of_week_in_month(cal, 0), count_day_of_week_in_month(cal, 3)
    )

    service_names = schedule.service_names

    with open("style.css", "r") as f:
        style = f.read()

    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta name="pdfkit-page-size" content="Legal"/>
            <meta name="pdfkit-orientation" content="Landscape"/>
            <meta http-equiv="Cache-control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="Pragma" content="no-cache">
            <style>{style}</style>
        </head>
        <body>
            <div class="header">
                <h1>{calendar.month_name[schedule.month]}</h1>
            </div>
            {render_service(service_names[0], 0, schedule, num_services)}
            <div class="banner dark-background">
                2nd Service 10:30
            </div>
            {render_service(service_names[1], 0, schedule, num_services, header=False)}
            {render_service(service_names[2], 3, schedule, num_services)}
            {render_weeky_duties(schedule)}
            <script>{read_schedule_javascript()}</script>
        </body>
    </html>
    """
