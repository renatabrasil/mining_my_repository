from django.test import TransactionTestCase

from contributions.models import Project
from contributions.repositories.project_repository import ProjectRepository


class ProjectRepositoryTests(TransactionTestCase):
    repository = ProjectRepository()

    def test_should_return_project_when_calls_find_project_by_name(self):
        # Given
        Project.objects.create(project_name="OBS")
        expected_result = Project.objects.create(project_name="ANT")
        Project.objects.create(project_name="XXX")

        # When
        result = self.repository.find_project_by_name("ANT")

        # Then
        self.assertEqual(expected_result, result)
