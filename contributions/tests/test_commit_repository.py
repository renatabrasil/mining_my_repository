from django.test import TransactionTestCase

from contributions.models import Commit, Tag, Project, Developer
from contributions.repositories.commit_repository import CommitRepository


class DeveloperModelTests(TransactionTestCase):
    commit_repositoy = CommitRepository()

    def test_should_update_a_commit_successfully(self):
        # Given
        commit = Commit.objects.create(hash="NAOATUALIZOU", mean_rmd_components=0.0, author=Developer.objects.create(),
                                       committer=Developer.objects.create(),
                                       tag=Tag.objects.create(description="oi", project=Project.objects.create()))

        # When
        result = self.commit_repositoy.update(commit=commit, fields={'mean_rmd_components': 12.0, 'hash': 'WTF'})

        # Then
        self.assertEqual(12.0, commit.mean_rmd_components)
        self.assertEqual('WTF', commit.hash)
        self.assertEqual('oi', commit.tag.description)
