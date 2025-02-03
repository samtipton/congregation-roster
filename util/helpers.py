import re
import json


date_task_name_pattern = re.compile(r"-\w+$")
date_task_date_pattern = re.compile(r"^[0-9]+-[0-9]+-(?:[0-9]+-)?")
date_task_day_pattern = re.compile(r"^[0-9]+-[0-9]+-([0-9]+)-\w+$")


# TODO Should move into date task class?
# TODO Names suggest opposite of what they do
def trim_task_name(date_task):
    """Trim/remove task date from date_task"""
    return date_task_date_pattern.sub("", date_task)


def trim_task_date(date_task):
    """Trim/remove name from date_task"""
    return date_task_name_pattern.sub("", date_task)


def trim_date_task_day(date_task):
    """trim the day numeric from the date_task, date_task is expected to contain it"""
    match = date_task_day_pattern.search(date_task)
    if match:
        return match.group(1)
    else:
        raise ValueError(
            f"Expected a date_task containing a day numeric in the form YYYY-mm-dd-<task_key>. Received {date_task}"
        )


def write_dict_to_file(d, path):
    json_str = json.dumps(d, indent=4, sort_keys=True, default=str)
    write_string_to_file(json_str, path)


def write_string_to_file(s, path):
    with open(path, "w") as f:
        f.write(s)


def term_link(uri, label=None):
    if label is None:
        label = uri
    parameters = ""

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"

    return escape_mask.format(parameters, uri, label)
