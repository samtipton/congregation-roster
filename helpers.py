import re

def trim_task_name(name):
    return re.sub("-\d+$", "", name)

def date_from_date_task(name):
    return re.sub("-\d+$", "", name)
