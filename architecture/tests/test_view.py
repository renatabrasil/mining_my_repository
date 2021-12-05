import os
import shutil
from unittest.mock import patch, Mock

from django.test import TestCase
from django.test.utils import isolate_apps
from django.urls import reverse

from architecture.forms import FilesCompiledForm
from architecture.models import FileCommits
from contributions.models import Project, Tag, Commit


@isolate_apps('architecture')
class ArchitectureCalculateMetricsViewTests(TestCase):
    directory = "compiled"
    file_name = "commits-1.1.txt"

    def tearDown(self):
        if os.path.isfile(self.file_name):
            os.remove(self.file_name)
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_should_load_index_view_as_get_http_method(self):
        """
        If HTTP METHOD is equal to GET, the form should be exhibited
        """
        # Given
        project = Project.objects.create(project_name="AntB")
        tag = Tag.objects.create(description="rel/1.1", project=project)
        files = [FileCommits.objects.create(name='compiled/commits-rel-1.4.txt', tag=tag,
                                            local_repository='G:/My Drive/MestradoUSP/programacao/projetos/git/ant',
                                            build_path='build',
                                            directory=self.directory)]

        session = self.client.session
        session['tag'] = 1
        session.save()

        # When
        response = self.client.get(reverse('architecture:index'))

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "compiled/commits-rel-1.4.txt")
        self.assertQuerysetEqual(response.context['title'], "Configuração do Projeto")
        self.assertQuerysetEqual(response.context['files'], files)

    @patch.object(FilesCompiledForm, "errors", [])
    @patch("contributions.repositories.commit_repository.CommitRepository.find_all_commits_by_project_order_by_id_asc",
           return_value=[Commit(tag=Tag(description="rel/1.1")), Commit(tag=Tag(description="rel/1.1"))])
    @patch('architecture.models.FileCommits')
    @patch('architecture.models.FileCommits.objects')
    def test_should_send_form_with_configs_as_post_http_method(self, mock_class, mock_file, mock):
        """
        If HTTP METHOD is equal to POST, informations filled in the form should be sent
        """

        mock_file.return_value.save = Mock(return_value=1)
        mock_class.filter.return_value.__getitem__.return_value.__str__.return_value = self.file_name
        mock_class.filter.return_value.count.return_value = 1

        project = Project.objects.create(project_name="AntB")

        session = self.client.session
        session['tag'] = 1
        session['project_id'] = project.id
        session.save()

        # When
        response = self.client.post(reverse('architecture:index'),
                                    data={'directory': self.directory, 'git_local_repository': 'blablabla.git',
                                          'build_path': '/build'})

        # Then
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context['title'], "Configuração do Projeto")
        self.assertQuerysetEqual(response.context['files'], mock_class.filter)
        mock_class.assert_called_once
        mock_file.assert_called_once
        mock.assert_called_once
