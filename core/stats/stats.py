import re
import pandas as pd
from core.history import AssignmentHistory
from core.roster import Roster
from util.helpers import write_dict_to_file

gamma = 0.2  # decay parameter for new people


class AssignmentStats:
    def __init__(self, roster: Roster, history: AssignmentHistory):
        self.ideal_avg = {
            task: 1 / count
            for task, count in roster.eligibility_df.sum(axis=0).to_dict().items()
        }

        # Historical assignments Create DataFrame from dictionary
        assignment_history_df = pd.DataFrame(
            {
                "Key": history.assignment_history.keys(),
                "Value": history.assignment_history.values(),
            }
        )

        # Pivot to make values the index and keys the columns
        assignment_history_df = assignment_history_df.pivot_table(
            index="Value", columns="Key", aggfunc=lambda x: 1, fill_value=0
        )
        # add new persons to rounds/history
        # set their assignment history to 1 so they do not get biased in first schedule
        for person in roster.people:
            if person not in assignment_history_df.index:
                assignment_history_df.loc[person] = 0

        # if person is chosen for task, compute the difference between ideal and avg
        # TODO: remove? Or implement diff indicators on frontend
        # Render depends on this still
        self.assignment_delta = {task: {} for task in roster.task_keys}

        # actual avg per person per task
        # could this be done in a jinja script tag?
        self.actual_avg = pd.DataFrame(index=roster.people, columns=roster.task_keys)
        for person in roster.people:
            for task in roster.task_keys:
                if person in assignment_history_df.index:
                    date_task_pattern = re.compile(f"[0-9]+-[0-9]+-(?:[0-9]+-)?{task}")
                    assignment_frequency = assignment_history_df.loc[
                        person,
                        assignment_history_df.columns.str.contains(
                            date_task_pattern, regex=True
                        ),
                    ].sum()

                    # count how many times the person has been eligible for a task since joining
                    rounds = max(history.rounds(person, task), 1)

                    self.actual_avg.at[person, task] = assignment_frequency / (rounds)

                    # boost new people
                    if rounds <= 5:
                        actual_avg = self.actual_avg.at[person, task]
                        self.actual_avg.at[person, task] = (
                            1 if actual_avg == 0 else actual_avg
                        ) * (1 + (1 - gamma * rounds))

                    self.assignment_delta[task][person] = round(
                        (
                            (self.actual_avg.at[person, task] - self.ideal_avg[task])
                            / self.ideal_avg[task]
                        )
                        * 100,
                        2,
                    )

                else:
                    self.actual_avg.at[person, task] = 0

        # TODO write to stats dir
        write_dict_to_file(self.ideal_avg, "/Users/stipton/Desktop/avgideal.json")
        write_dict_to_file(
            self.actual_avg.to_dict(), "/Users/stipton/Desktop/avgactual.json"
        )
        write_dict_to_file(self.assignment_delta, "/Users/stipton/Desktop/delta.json")
