import unittest
import os
import pandas as pd
from core.roster import Roster

TEST_ROUNDS_CSV = "core/roster/test-rounds.csv"


class RosterTests(unittest.TestCase):

    def test_increment_rounds(self):
        assignments = {
            "lesson-1": "Byers, Austin",
            "lesson-8": "Byers, Austin",
            "opening_prayer-1": "Earp, Wyatt",
        }
        roster = Roster(
            "core/schedule/test/unittest-previous-assignments.csv",
            TEST_ROUNDS_CSV,
        )
        roster.increment_rounds(assignments)
        df = pd.read_csv(TEST_ROUNDS_CSV, index_col=0)

        assert df.at["Byers, Austin", "lesson"] == 2
        assert df["opening_prayer"].sum() == len(roster.get_eligible("opening_prayer"))

    def test_decrement_rounds(self):
        """
        todo
        """
        assignments = {
            "lesson-1": "Byers, Austin",
            "lesson-8": "Byers, Austin",
            "opening_prayer-1": "Earp, Wyatt",
        }
        roster = Roster(
            "core/schedule/test/unittest-previous-assignments.csv",
            TEST_ROUNDS_CSV,
        )
        roster.increment_rounds(assignments)
        df = pd.read_csv(TEST_ROUNDS_CSV, index_col=0)

        assert df.at["Byers, Austin", "lesson"] == 2
        assert df["opening_prayer"].sum() == len(roster.get_eligible("opening_prayer"))

    def setup(self):
        """
        initialize test data file, if we have one already for some reason zero it out
        """
        df = pd.read_csv(TEST_ROUNDS_CSV, index_col=0)
        for col in df.columns:
            df[col].values[:] = 0
        df.to_csv(TEST_ROUNDS_CSV)

    def tearDown(self):
        """
        remove test data
        """
        os.remove(TEST_ROUNDS_CSV)
        pass


if __name__ == "__main__":
    unittest.main()
