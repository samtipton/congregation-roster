import unittest

from ..schedule import Schedule


class ScheduleTests(unittest.TestCase):

    def test_service_weeks(self):
        sch = Schedule(2024, 9)

        assert len(sch.get_service_weeks()) == 5

    def test_week_aligned_date_tasks_pairs(self):
        sch = Schedule(2024, 9)

        aligned_tasks1 = sch.week_aligned_date_tasks_pairs(
            "sound_board_operator", "first_lesson"
        )

        aligned_tasks2 = sch.week_aligned_date_tasks_pairs(
            "first_lesson", "sound_board_operator"
        )

        assert ("first_lesson-13", "sound_board_operator-1") not in aligned_tasks1
        assert ("first_lesson-13", "sound_board_operator-1") not in aligned_tasks2
        assert ("sound_board_operator-1", "first_lesson-13") not in aligned_tasks1
        assert ("sound_board_operator-1", "first_lesson-13") not in aligned_tasks2


if __name__ == "__main__":
    unittest.main()
