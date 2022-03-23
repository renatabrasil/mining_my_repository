from django.test import TestCase

from architecture.models import (FileCommits)
from contributions.models import (Project, Tag)


class FileCommitsModelTests(TestCase):
    def test_should_print_name_file(self):
        project = Project.objects.create(project_name="Ant")
        tag = Tag.objects.create(description="rel/1.1", project=project)
        file = FileCommits.objects.create(name="File 1", directory="desktop", tag=tag, build_path='',
                                          local_repository='')

        self.assertEqual(file.__str__(), 'desktop/File 1')
