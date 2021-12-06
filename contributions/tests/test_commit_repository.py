from django.test import TransactionTestCase

from contributions.models import Commit, Tag, Project, Developer
from contributions.repositories.commit_repository import CommitRepository


class DeveloperModelTests(TransactionTestCase):
    repository = CommitRepository()

    def test_should_update_a_commit_successfully(self):
        # Given
        commit = Commit.objects.create(hash="NAOATUALIZOU", mean_rmd_components=0.0, author=Developer.objects.create(),
                                       committer=Developer.objects.create(),
                                       tag=Tag.objects.create(description="oi", project=Project.objects.create()))

        # When
        self.repository.update(commit=commit, fields={'mean_rmd_components': 12.0, 'hash': 'WTF'})

        # Then
        self.assertEqual(12.0, commit.mean_rmd_components)
        self.assertEqual('WTF', commit.hash)
        self.assertEqual('oi', commit.tag.description)

    def test_should_save_commit_succesfully(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit(hash="TEST", author=Developer(name="Franco"), committer=Developer(name="Roberto"),
                        tag=tag)

        # When
        self.repository.insert(commit)

        # Then
        self.assertTrue(commit.pk > 0)

    def test_should_get_commit_by_primary_key(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit.objects.create(hash="TEST", author=Developer(name="Franco"),
                                       committer=Developer(name="Roberto"),
                                       tag=tag)
        commit2 = Commit.objects.create(id=4, hash="TEST2", author=Developer(name="Franco Fanti"),
                                        committer=Developer(name="Roberto"),
                                        tag=tag)
        commit3 = Commit.objects.create(hash="TEST3", author=Developer(name="Franco Fanti"),
                                        committer=Developer(name="Roberto"),
                                        tag=tag)

        # When
        result = self.repository.find_by_primary_key(4)

        # Then
        self.assertEqual(4, commit2.id)
