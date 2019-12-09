from django.test import TestCase, Client
from django.urls import reverse
from django.views import generic

from architecture.models import FileCommits


# def create_question(question_text, days):
#     """
#     Create a question with the given `question_text` and published the
#     given number of `days` offset to now (negative for questions published
#     in the past, positive for questions that have yet to be published).
#     """
#     time = timezone.now() + datetime.timedelta(days=days)
#     return Question.objects.create(question_text=question_text, pub_date=time)
from common.utils import ViewUtils
from contributions.models import Project, Tag


# class ArchitectureCalculateMetricsViewTests(TestCase):
    # def test_save_architecture_metrics_quality(self):
    #     """
    #     If directory is visible, calculate metric
    #     """
    #
    #     project = Project.objects.create(project_name="AntB")
    #     # tag = Tag.objects.create(description="rel/1.1", project=project)
    #     # files = []
    #     # files.append(FileCommits.objects.create(name='compiled/commits-rel-1.4.txt', project=project,
    #     #                                         local_repository='G:/My Drive/MestradoUSP/programacao/projetos/git/ant',
    #     #                                         build_path='build',
    #     #                                         directory='compiled'))
    #
    #     session = self.client.session
    #     session['tag'] = 1
    #     session.save()
    #
    #     response = self.client.get(reverse('architecture:index'))
    #     self.assertEqual(response.status_code, 200)
        # tag = ViewUtils.load_tag(response)
        # self.assertContains(response, "compiled/commits-rel-1.4.txt")
        # self.assertQuerysetEqual(response.context['latest_question_list'], [])
