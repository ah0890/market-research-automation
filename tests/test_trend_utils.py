import unittest

from models.trend import TrendPoint
from settings import (
    TREND_DIRECTION_DECLINING,
    TREND_DIRECTION_RISING,
    TREND_DIRECTION_STABLE,
    TREND_DIRECTION_UNKNOWN,
)
from utils.trend_utils import calculate_average_trend, calculate_trend_direction


def _points(values: list[int]) -> list[TrendPoint]:
    return [TrendPoint(date=f"2024-{i + 1:02d}-01", interest_value=value) for i, value in enumerate(values)]


class CalculateAverageTrendTests(unittest.TestCase):
    def test_empty_series_returns_none(self) -> None:
        self.assertIsNone(calculate_average_trend([]))

    def test_average_of_values(self) -> None:
        self.assertEqual(calculate_average_trend(_points([10, 20, 30])), 20.0)


class CalculateTrendDirectionTests(unittest.TestCase):
    def test_insufficient_data_is_unknown(self) -> None:
        self.assertEqual(calculate_trend_direction(_points([10, 20, 30])), TREND_DIRECTION_UNKNOWN)

    def test_rising_trend(self) -> None:
        previous_window = [10, 10, 10, 10, 10, 10]
        recent_window = [20, 20, 20, 20, 20, 20]
        self.assertEqual(
            calculate_trend_direction(_points(previous_window + recent_window)),
            TREND_DIRECTION_RISING,
        )

    def test_declining_trend(self) -> None:
        previous_window = [20, 20, 20, 20, 20, 20]
        recent_window = [10, 10, 10, 10, 10, 10]
        self.assertEqual(
            calculate_trend_direction(_points(previous_window + recent_window)),
            TREND_DIRECTION_DECLINING,
        )

    def test_stable_trend(self) -> None:
        previous_window = [20, 20, 20, 20, 20, 20]
        recent_window = [21, 19, 20, 20, 21, 19]
        self.assertEqual(
            calculate_trend_direction(_points(previous_window + recent_window)),
            TREND_DIRECTION_STABLE,
        )


if __name__ == "__main__":
    unittest.main()
