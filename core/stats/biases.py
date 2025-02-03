import os

import pandas as pd

from util.decorators import singleton


@singleton
class AssignmentBiases:
    def __init__(self):
        # Read biases matrix
        if os.path.isfile("data/biases.csv"):
            bias_df = pd.read_csv("data/biases.csv", index_col=0)
            bias_df.fillna(1, inplace=True)
        else:
            eligibility_df = pd.read_csv("data/prefs.csv")
            eligibility_df.set_index("name", inplace=True)
            bias_df = eligibility_df.copy()
            bias_df[:] = 1

        self.bias = bias_df.to_dict()
