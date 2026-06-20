from django.test import SimpleTestCase

from contributions.helpers.models_helper import (
    count_blank_lines,
    count_loc,
    detect_impact_loc,
    has_impact_loc_calculation_static_method,
    prepare_diff_text,
)


class ModelsHelperTests(SimpleTestCase):
    def test_should_detect_impact_loc_when_line_has_code(self):
        self.assertTrue(detect_impact_loc("\npublic void execute() {\n}"))

    def test_should_not_detect_impact_loc_when_lines_are_numeric(self):
        self.assertFalse(detect_impact_loc("\n42"))

    def test_should_count_blank_and_numeric_lines(self):
        self.assertEqual(3, count_blank_lines("\n\n  \n 42\nreturn value;"))

    def test_should_count_loc_without_blank_or_numeric_lines(self):
        self.assertEqual(1, count_loc("\n\n  \n 42\nreturn value;"))

    def test_should_prepare_diff_text_with_line_numbers_and_type_symbol(self):
        result = prepare_diff_text([(2, "return value;")], "", "+")

        self.assertEqual("\n2 + return value;", result)

    def test_should_calculate_impact_loc_from_added_or_deleted_diff(self):
        diff = {
            "added": [(10, "public void execute() {")],
            "deleted": [(9, "42")],
        }

        self.assertTrue(has_impact_loc_calculation_static_method(diff))

    def test_should_not_calculate_impact_loc_for_numeric_only_diff(self):
        diff = {
            "added": [(10, "42")],
            "deleted": [(9, "  ")],
        }

        self.assertFalse(has_impact_loc_calculation_static_method(diff))
