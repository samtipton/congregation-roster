#!/opt/anaconda3/envs/roster/bin/python3
import json
import os
import re
import sys


JSON_OUTPUT_FILE_PATTERN = re.compile(r"[^\d]*(\d+)-(\d{4})\.json")
DATE_TASK_PATTERN = re.compile(r"(\w*)-(\d{1,2})")


def get_files_in_directory_by_pattern(
    directory_path: str, filename_pattern: re.Pattern[str]
):
    # Get a list of files in the directory
    files = [
        f
        for f in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, f))
        and filename_pattern.search(f)
    ]

    return files


def run():
    if len(sys.argv) != 2:
        raise RuntimeError("Expected path to JSON_OUTPUT_PATH")

    dir_path = sys.argv[1]

    if not os.path.isdir(dir_path):
        raise RuntimeError(f"Invalid path: {dir_path}")

    filenames = get_files_in_directory_by_pattern(sys.argv[1], JSON_OUTPUT_FILE_PATTERN)

    new_data = {}
    for filename in filenames:
        data = None
        with open(f"{dir_path}/{filename}", "r") as f:
            data = json.load(f)
            # print(data)

        # extract year and month out
        match = JSON_OUTPUT_FILE_PATTERN.search(filename)
        if match:
            month = match.group(1)
            year = match.group(2)
        else:
            raise RuntimeWarning(f"Unexpected filename: {filename}")

        # print(f"{year}-{month}")

        # make date_task names of the form {year}-{month}-{day}-{task}
        for task, person in data.items():
            day_task_match = DATE_TASK_PATTERN.search(task)

            if day_task_match:
                task = day_task_match.group(1)
                day = day_task_match.group(2)
                expanded_date_task = f"{year}-{month}-{day}-{task}"
                new_data[expanded_date_task] = person

                # print(f"{expanded_date_task}: {person}")
            else:
                raise RuntimeWarning(f"Unexpected date_task: {task}")

    # write each file back with new name
    new_path = f"{dir_path}/expanded-date-task-keys-assignment-history.json"

    if os.path.exists(new_path):
        os.remove(new_path)
    with open(new_path, "w") as f:
        json.dump(new_data, f, indent=4, sort_keys=True, default=str)


if __name__ == "__main__":
    run()
