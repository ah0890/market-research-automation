import unittest

from utils.validation import validate_row


class ValidateRowTests(unittest.TestCase):
    def test_valid_row_has_no_errors(self) -> None:
        values = {"Category": "Kitchen", "Product": "Mug", "Main Keyword": "ceramic mug"}
        self.assertEqual(validate_row(2, values), [])

    def test_missing_required_fields_are_reported(self) -> None:
        values = {"Category": "", "Product": None, "Main Keyword": "mug"}
        errors = validate_row(5, values)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("Category" in e for e in errors))
        self.assertTrue(any("Product" in e for e in errors))

    def test_whitespace_only_value_is_missing(self) -> None:
        values = {"Category": "  ", "Product": "Mug", "Main Keyword": "mug"}
        errors = validate_row(3, values)
        self.assertEqual(len(errors), 1)
        self.assertIn("Category", errors[0])


if __name__ == "__main__":
    unittest.main()
