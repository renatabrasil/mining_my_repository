import datetime

from django.test import TestCase

# Create your tests here.
from contributions.models import Project, Developer, Tag, Directory, Commit

class CommitModelTests(TestCase):
    def test_save_children_commit(self):
        project = Project.objects.create(project_name="Ant")
        developer = Developer.objects.create(name="Jack", email="jack@gmail.com")
        tag = Tag.objects.create(description="rel/1.1", project=project)
        directory = Directory.objects.create(name="src/main/org/apache/ant", project=project)
        commit = Commit.objects.create(hash="oioioi", tag=tag, author=developer, committer=developer,
                                       author_date=datetime.datetime.now().date(),
                                       committer_date=datetime.datetime.now().date())
        commit2 = Commit.objects.create(hash="Assoioioi", tag=tag, author=developer, committer=developer,
                                        author_date=datetime.datetime.now().date(),
                                        committer_date=datetime.datetime.now().date(), parents_str='oioioi')
        # commit.children_commit = commit2
        commit.save()
        commit2.save()

        # TODO: tests
        # self.assertEqual(commit.children_commit.id, commit2.id)