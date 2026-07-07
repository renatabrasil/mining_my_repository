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

        Commit.objects.create(hash="TEST", author=Developer(name="Franco"),
                              committer=Developer(name="Roberto"),
                              tag=tag)
        Commit.objects.create(id=4, hash="TEST2", author=Developer(name="Fausto Fanti"),
                              committer=Developer(name="Roberto"),
                              tag=tag)
        Commit.objects.create(hash="TEST3", author=Developer(name="Franco Fanti"),
                              committer=Developer(name="Roberto"),
                              tag=tag)

        # When
        result = self.repository.find_by_primary_key(4)

        # Then
        self.assertEqual(4, result.id)

    def test_should_return_all_commits(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit.objects.create(hash="TEST", author=Developer(name="Franco"),
                                       committer=Developer(name="Roberto"),
                                       tag=tag)
        commit2 = Commit.objects.create(hash="TEST2", author=Developer(name="Fred Fanti"),
                                        committer=Developer(name="Roberto"),
                                        tag=tag)
        commit3 = Commit.objects.create(hash="TEST3", author=Developer(name="Franco Fanti"),
                                        committer=Developer(name="Roberto"),
                                        tag=tag)

        expected_result = [commit, commit2, commit3]

        # When
        result = self.repository.find_all()

        # Then
        self.assertEqual(expected_result, list(result))

    def test_should_find_all_distinct_commits_by_tag_description(self):
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)
        other_tag = Tag.objects.create(description="v2.0", project=project)
        expected_commit = Commit.objects.create(hash="MATCH", author=Developer(name="Franco"),
                                                committer=Developer(name="Roberto"), tag=tag)
        Commit.objects.create(hash="OTHER", author=Developer(name="Fred"),
                              committer=Developer(name="Roberto"), tag=other_tag)

        result = self.repository.find_all_distinct_commits_by_tag_description("v1.0")

        self.assertListEqual([expected_commit], list(result))

    def test_should_find_all_commits_by_author_id(self):
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)
        author = Developer.objects.create(name="Franco")
        other_author = Developer.objects.create(name="Fred")
        expected_commit = Commit.objects.create(hash="AUTHOR", author=author,
                                                committer=Developer(name="Roberto"), tag=tag)
        Commit.objects.create(hash="OTHER_AUTHOR", author=other_author,
                              committer=Developer(name="Roberto"), tag=tag)

        result = self.repository.find_all_commits_by_author_id(author.id)

        self.assertListEqual([expected_commit], list(result))

    def test_should_find_commits_by_project_ordered_by_id(self):
        project = Project.objects.create(project_name="ANT")
        other_project = Project.objects.create(project_name="Maven")
        tag = Tag.objects.create(description="v1.0", project=project)
        other_tag = Tag.objects.create(description="v1.0", project=other_project)
        second_commit = Commit.objects.create(id=20, hash="SECOND", author=Developer(name="Franco"),
                                              committer=Developer(name="Roberto"), tag=tag)
        first_commit = Commit.objects.create(id=10, hash="FIRST", author=Developer(name="Fred"),
                                             committer=Developer(name="Roberto"), tag=tag)
        Commit.objects.create(id=30, hash="OTHER_PROJECT", author=Developer(name="Ana"),
                              committer=Developer(name="Roberto"), tag=other_tag)

        result = self.repository.find_all_commits_by_project_order_by_id_asc(project)

        self.assertListEqual([first_commit, second_commit], list(result))

    def test_should_find_only_compilable_commits_by_hash(self):
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)
        expected_commit = Commit.objects.create(hash="SAME_HASH", compilable=True, author=Developer(name="Franco"),
                                                committer=Developer(name="Roberto"), tag=tag)
        Commit.objects.create(hash="SAME_HASH", compilable=False, author=Developer(name="Fred"),
                              committer=Developer(name="Roberto"), tag=tag)

        result = self.repository.find_all_compilable_commits_by_hash("SAME_HASH")

        self.assertListEqual([expected_commit], list(result))
