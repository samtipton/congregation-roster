# Congregation Roster

A *work in progress* python utility for solving the congregational duty scheduling constraint problem


### How to test/develop in Jupyter Notebook

1. [Intall Anaconda Navigator](https://docs.anaconda.com/free/navigator/install/)
2. Open a Jupyter Lab instance from Anaconda Navigator
3. Navigate to the congreation-roster project directory in Juppyter Lab
4. If you want to run as a python script 

### How to run as a standalone python script

1. Make sure you have anaconda (`conda`) installed on your path
2. From `pulp-roster.ipynb` jupyter lab click File > Saven and Export Notebook As... > Executable Script
3. Navigate to the congreation-roster project directory in a terminal
4. Run `$ conda activate` to activate the conda virtual environment (may be different in windows?)
5. Run `$python3 pulp-roster.py`


### Explanations of csv files

1. `men.csv`: contains all men available for duty scheduling in the first column, the other columns are the duties to be scheduled for, cell values of a `1` indicate that that man may be assigned a task

2. `exclusions.csv`: this file is an adjacency matrix of duties. If a cell value contains a 1, this indicates this duty should not be assigned to the same man.

3. `previous-assignments.csv`: you will not see this file until you run the script the first time. This file contains the historical assignment frequencies for everyone. This is the sripts "persistent memory". Until we hit an alpha phase, this file is likely to change and shouldn't be in git.

The source of truth for these csvs will be kept in this [google sheet](https://docs.google.com/spreadsheets/d/1ZvrvidGAKMgeG7aW0cY0kQ-0DDIzW-x2EG4FS-oczqI/edit?usp=sharing) (please request access) and exported to csvs to use here.