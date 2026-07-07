from django import template
from django.template.base import Token, TokenType
from django.test import SimpleTestCase

from contributions.templatetags.contributions_extra import (
    SetVarNode,
    div,
    get,
    get_field,
    get_list,
    percentage,
    set_var,
)


class DummyObject:
    name = "component"


class TemplateTagsTests(SimpleTestCase):
    def test_should_get_value_from_mapping(self):
        self.assertEqual("value", get({"key": "value"}, "key"))

    def test_should_return_none_when_mapping_key_does_not_exist(self):
        self.assertIsNone(get({"key": "value"}, "missing"))

    def test_should_get_value_from_list(self):
        self.assertEqual("second", get_list(["first", "second"], 1))

    def test_should_return_none_when_list_value_is_empty(self):
        self.assertIsNone(get_list([], 0))

    def test_should_divide_values(self):
        self.assertEqual(2, div(10, 5))

    def test_should_return_zero_when_dividing_by_zero(self):
        self.assertEqual(0, div(10, 0))

    def test_should_format_percentage(self):
        self.assertEqual("25.00%", percentage(0.25))

    def test_should_get_object_field(self):
        self.assertEqual("component", get_field(DummyObject(), "name"))

    def test_set_var_node_should_store_resolved_value_in_context(self):
        context = template.Context({"source": "resolved"})
        node = SetVarNode("target", "source")

        result = node.render(context)

        self.assertEqual("", result)
        self.assertEqual("resolved", context["target"])

    def test_set_var_node_should_store_empty_string_when_value_does_not_exist(self):
        context = template.Context({})
        node = SetVarNode("target", "missing")

        node.render(context)

        self.assertEqual("", context["target"])

    def test_set_var_should_require_expected_syntax(self):
        token = Token(token_type=TokenType.BLOCK, contents="set value")

        with self.assertRaises(template.TemplateSyntaxError):
            set_var(None, token)
