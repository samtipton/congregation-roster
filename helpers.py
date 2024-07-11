import re


def trim_task_name(name):
    return re.sub("-\d+$", "", name)


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
