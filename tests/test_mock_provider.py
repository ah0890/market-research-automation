import unittest

from api.mock_provider import fetch_google_trends_mock, fetch_search_volume_mock


class FetchSearchVolumeMockTests(unittest.TestCase):
    def test_returns_one_result_per_keyword(self) -> None:
        results = fetch_search_volume_mock(["ceramic mug", "dog harness"], 2840, "en")
        self.assertEqual(set(results.keys()), {"ceramic mug", "dog harness"})

    def test_is_deterministic_for_the_same_keyword(self) -> None:
        first = fetch_search_volume_mock(["ceramic mug"], 2840, "en")["ceramic mug"]
        second = fetch_search_volume_mock(["ceramic mug"], 2840, "en")["ceramic mug"]
        self.assertEqual(first.search_volume, second.search_volume)
        self.assertEqual(first.cpc, second.cpc)

    def test_includes_twelve_months_of_history(self) -> None:
        result = fetch_search_volume_mock(["ceramic mug"], 2840, "en")["ceramic mug"]
        self.assertEqual(len(result.monthly_search_volume_history), 12)

    def test_competition_label_matches_index(self) -> None:
        result = fetch_search_volume_mock(["ceramic mug"], 2840, "en")["ceramic mug"]
        self.assertIn(result.competition, ("LOW", "MEDIUM", "HIGH"))
        self.assertTrue(0 <= result.competition_index <= 100)


class FetchGoogleTrendsMockTests(unittest.TestCase):
    def test_returns_one_result_per_keyword_and_no_errors(self) -> None:
        results, errors = fetch_google_trends_mock(["ceramic mug", "dog harness"], 2840, "en")
        self.assertEqual(set(results.keys()), {"ceramic mug", "dog harness"})
        self.assertEqual(errors, {})

    def test_includes_five_years_of_monthly_data(self) -> None:
        results, _ = fetch_google_trends_mock(["ceramic mug"], 2840, "en")
        self.assertEqual(len(results["ceramic mug"].monthly_values), 60)

    def test_interest_values_stay_within_bounds(self) -> None:
        results, _ = fetch_google_trends_mock(["ceramic mug"], 2840, "en")
        for point in results["ceramic mug"].monthly_values:
            self.assertTrue(0 <= point.interest_value <= 100)

    def test_is_deterministic_for_the_same_keyword(self) -> None:
        first, _ = fetch_google_trends_mock(["ceramic mug"], 2840, "en")
        second, _ = fetch_google_trends_mock(["ceramic mug"], 2840, "en")
        self.assertEqual(first["ceramic mug"].monthly_values, second["ceramic mug"].monthly_values)


if __name__ == "__main__":
    unittest.main()
