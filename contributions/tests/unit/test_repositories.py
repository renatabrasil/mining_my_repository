from django.test import TransactionTestCase

from contributions.models import Commit, ComponentCommit, Developer, Directory, Modification, Project, Tag
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.directory_repository import DirectoryRepository
from contributions.repositories.modification_repository import ModificationRepository
from contributions.repositories.tag_repository import TagRepository


class RepositoryTests(TransactionTestCase):
    def setUp(self):
        self.project = Project.objects.create(project_name="ANT")
        self.other_project = Project.objects.create(project_name="MAVEN")
        self.tag = Tag.objects.create(description="v1.0", project=self.project)
        self.developer = Developer.objects.create(
            name="Renata Brasil",
            email="renata@example.com",
            login="renata",
        )
        self.commit = Commit.objects.create(
            hash="abc123",
            author=self.developer,
            committer=self.developer,
            tag=self.tag,
        )
        self.directory = Directory.objects.create(
            name="src/main",
            project=self.project,
            visible=True,
        )

    def test_should_find_developer_by_login(self):
        result = DeveloperRepository().find_all_developer_by_login("renata")

        self.assertEqual([self.developer], list(result))

    def test_should_find_developer_by_case_insensitive_name(self):
        result = DeveloperRepository().find_all_developer_by_iexact_name("renata brasil")

        self.assertEqual([self.developer], list(result))

    def test_should_find_visible_directories_ordered_by_id(self):
        hidden_directory = Directory.objects.create(
            name="hidden",
            project=self.project,
            visible=False,
        )
        second_directory = Directory.objects.create(
            name="src/test",
            project=self.project,
            visible=True,
        )

        result = DirectoryRepository().find_all_visible_directories_order_by_id()

        self.assertEqual([self.directory, second_directory], list(result))
        self.assertNotIn(hidden_directory, result)

    def test_should_find_visible_directories_by_project_ordered_by_name(self):
        Directory.objects.create(name="zzz", project=self.other_project, visible=True)
        first_directory = Directory.objects.create(name="aaa", project=self.project, visible=True)

        result = DirectoryRepository().find_all_visible_directories_by_project_id_order_by_name(self.project.id)

        self.assertEqual([first_directory, self.directory], list(result))

    def test_should_find_major_tags_by_project_from_tag_id(self):
        older_tag = Tag.objects.create(description="v0.9", project=self.project, major=True)
        minor_tag = Tag.objects.create(description="v1.1", project=self.project, major=False)
        newer_tag = Tag.objects.create(description="v2.0", project=self.project, major=True)
        Tag.objects.create(description="other", project=self.other_project, major=True)

        result = TagRepository().find_all_major_tags_by_project(self.project.id, self.tag.id)

        self.assertEqual([self.tag, older_tag, newer_tag], list(result))
        self.assertNotIn(minor_tag, result)

    def test_should_find_modifications_by_directory_path(self):
        component_commit = ComponentCommit.objects.create(component=self.directory, commit=self.commit)
        other_directory = Directory.objects.create(name="src/other", project=self.project)
        other_component_commit = ComponentCommit.objects.create(component=other_directory, commit=self.commit)
        modification = Modification(
            path="src/main/App.java",
            directory=self.directory,
            commit=self.commit,
            component_commit=component_commit,
        )
        other_modification = Modification(
            path="src/other/App.java",
            directory=other_directory,
            commit=self.commit,
            component_commit=other_component_commit,
        )
        Modification.objects.bulk_create([modification, other_modification])

        result = ModificationRepository().find_all_modifications_by_path(self.directory.id)

        self.assertEqual(["src/main/App.java"], [item.path for item in result])
