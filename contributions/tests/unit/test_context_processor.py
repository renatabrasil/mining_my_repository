from django.test import TestCase
from django.test.client import RequestFactory

from contributions.context_processor import tags_processor
from contributions.models import Developer, Project, Tag


class ContextProcessorTests(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.project = Project.objects.create(project_name="ANT")
        self.other_project = Project.objects.create(project_name="Maven")
        self.major_tag = Tag.objects.create(description="v1.0", project=self.project, major=True)
        Tag.objects.create(description="v1.1-minor", project=self.project, major=False)
        Tag.objects.create(description="v2.0", project=self.other_project, major=True)
        self.developer = Developer.objects.create(name="Ana", email="ana@example.com", login="ana")

    def test_tags_processor_uses_project_from_session(self):
        request = self.request_factory.get("/")
        request.session = {"project": self.project.id}

        context = tags_processor(request)

        self.assertEqual(self.project, context["project"])
        self.assertListEqual([self.major_tag], list(context["tags"]))
        self.assertListEqual([self.developer], list(context["developers"]))
        self.assertCountEqual([self.project, self.other_project], list(context["projects"]))

    def test_tags_processor_falls_back_to_first_project_when_session_project_is_empty(self):
        request = self.request_factory.get("/")
        request.session = {"project": None}

        context = tags_processor(request)

        self.assertEqual(self.project, context["project"])
        self.assertListEqual([self.major_tag], list(context["tags"]))
