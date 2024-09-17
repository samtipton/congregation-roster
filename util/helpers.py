import re
import json


def trim_task_name(name):
    return re.sub(r"-\d+$", "", name)


def trim_task_date(name):
    return re.sub(r"^[a-zA-Z_]+-", "", name)


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
