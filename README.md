# Congregation Roster

A _work in progress_ python utility for solving the congregational duty scheduling constraint problem

### Current Features

1. Once csvs are updated with your information, you may run this program to create a schedule that optimizes for fairly scheduling people to tasks. Fairness here means that the average assignment frequency difference between men signed up for a particular task is minimized across all people and tasks.

2. Before exiting, the program will start a webapp where the schedule can be edited in place (drag-and-drop names, edit names) for any manual tweaks that need to be made.

3. From the webapp, a reveal-on-hover control menu in the upper left hand corner of the screen provides a 'Download PDF' button and a 'Commit' button.

4. 'Commit' will save the current schedule to persistent csv file-store which will be used for the next non-year-month matching schedule generation.

### Setup

#### Install conda

Conda is used for managing the environment/packages needed to run the library that solves the scheduling constraint problem (PuLP).

1. I installed the anaconda distribution found [here](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)

2. Once installed (`$ conda`) shows output, and you are in the base environment (`$ conda activate base`) we need to create the custom environment we will use to install packages needed to run this application. Do so with:

```sh
$ conda env create -f environment.yml
```

3. If needed, activate this new environment `$ conda activate roster`

#### Install packages with pip

A few packages we need are not available with conda (pdfkit, pyquery)

1. With your conda environment activated, ensure pip is installed in your env `$ which pip` should show a path into your env.

2. Run

```sh
$ pip install -r requirements.txt
```

This should complete the python environment setup.

### How to run as a standalone python script

5. Make `run.py` executable: `chmod u+x run.py`
6. Run `$ ./run.py <month number> <year> <path/to/pdf/file> <path/to/optional/history/csv/file>`

For example

```sh
./run.py 11 2024 /Users/Desktop/congregation-roster/roster-11-2024.pdf previous-assignments-test.csv
```

### Explanations of /data csv files

1. `men.csv`: contains all men available for duty scheduling in the first column, the other columns are the duties to be scheduled for, cell values of a `1` indicate that that man may be assigned a task

2. `exclusions.csv`: this file is an adjacency matrix of duties. If a cell value contains a 1, this indicates this duty should not be assigned to the same man.

3. `duty-codes.csv`: this file contains 'codes' for each duty. These codes will be referenced to determine what days or weeks a duty should be scheduled for. A future code may be for gospel meeting duty scheduling. Codes may be 1 of the following

   - a number between 0 and 6: represents the day of the week the duty is to be performed (0 for Sunday, 3 for Wednesday, etc.)
   - 'w': a weekly duty
   - 'm': a monthly duty

4. `duty-names.csv`: this file is a mapping of the duty "id" to a human-readable name we'll use on the schedule

5. `previous-assignments.csv`: you will not see this file until you run the script the first time without a command-line override. This file contains the historical assignment frequencies for everyone. This is the script's persistent datastore. This file doesn't make since to be checked into this project.

Jupyter has a nice interface for viewing csvs, or you can export into excel or google sheets.

### How to test/develop in Jupyter Notebook

This solver was initially developed using jupyter, it is still possible to do so but any changes made to the logic that need to be persisted in the script will need to be manually copied back into solver.py. It is still a nice way of seeing intermediate output and testing python snippets.

1. [Install Anaconda Navigator](https://docs.anaconda.com/free/navigator/install/)
2. Open a Jupyter Lab instance from Anaconda Navigator
3. Navigate to the congregation-roster project directory in Jupyter Lab
