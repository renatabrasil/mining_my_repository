#     time = timezone.now() + datetime.timedelta(days=days)
#     return Question.objects.create(question_text=question_text, pub_date=time)

# def create_question(question_text, days):
#     """
#     Create a question with the given `question_text` and published the
#     given number of `days` offset to now (negative for questions published
#     in the past, positive for questions that have yet to be published).
#     """

from django.test import TestCase
from django.urls import reverse

from architecture.models import FileCommits
from contributions.models import Project, Tag


class ArchitectureCalculateMetricsViewTests(TestCase):

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
                                            directory='compiled')]

        session = self.client.session
        session['tag'] = 1
        session.save()

        # When
        response = self.client.get(reverse('architecture:index'))

        # When
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "compiled/commits-rel-1.4.txt")
        self.assertQuerysetEqual(response.context['files'], files)

    # @patch.object(FilesCompiledForm, "errors", [])
    # @patch("contributions.repositories.commit_repository.CommitRepository.find_all_commits_by_project_order_by_id_asc",
    #        return_value=[Commit(tag=Tag.objects.create(description="rel/1.1", project_id=1)), Mock(spec=Commit)])
    # def test_should_send_form_with_configs_as_post_http_method(self, mock):
    #     """
    #     If HTTP METHOD is equal to POST, informations filled in the form should be sent
    #     """
    #     # Given
    #     project = Project.objects.create(project_name="AntB")
    #     tag = Tag.objects.create(description="rel/1.1", project=project)
    #
    #     with patch('contributions.models.Commit.tag', new_callable=PropertyMock) as mock_foo:
    #         mock_foo = Mock(name="mock.tag.description")
    #         commit = Commit()
    #         commit.tag = Tag(description='rel/1.1')
    #         mock_foo.return_value = Tag(description='rel/1.1')
    #
    #     session = self.client.session
    #     session['tag'] = 1
    #     session.save()
    #
    #     # When
    #     response = self.client.post(reverse('architecture:index'),
    #                                 data={'directory': '/compiled', 'git_local_repository': 'blablabla.git',
    #                                       'build_path': '/build'})
    #
    #     # When
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "compiled/commits-rel-1.4.txt")
    #     mock.assert_called_once_with
    #     # self.assertQuerysetEqual(response.context['files'], files)
