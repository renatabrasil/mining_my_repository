import datetime

from django.test import TestCase

# Create your tests here.
from architecture.models import ArchitectureQualityMetrics, ArchitectureQualityByDeveloper
from contributions.models import Developer, Directory, Tag, Commit, Modification, Project


class ArchitectureQualityMetricsModelTests(TestCase):

    def test_delta_metrics(self):
        # previous_metrics = ArchitectureQualityMetrics()
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
        metrics_by_developer = ArchitectureQualityByDeveloper.objects.create(developer=developer, tag=tag,
                                                                             directory=directory)
        previous_metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
                                                                     ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1,
                                                                     commit=commit)
        metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
                                                            previous_architecture_quality_metrics=previous_metrics,
                                             ca=3,ce=2,rma=0.01,rmi=0.012,rmd=0.5, commit=commit2)

        # FIXME:
        # self.assertEqual(metrics.delta_rmd,0.4)
        # self.assertEqual(metrics.delta_rma, 0.0)
        # self.assertEqual(metrics.delta_rmi, 0.01)

        self.assertEqual(metrics.commit.parents[0], previous_metrics.commit)

class ArchitectureQualityByDeveloperModelTests(TestCase):
    def test_commit_activity_in_this_tag(self):
        project = Project.objects.create(project_name="Ant")
        developer = Developer.objects.create(name="Jack",email="jack@gmail.com")
        developer2 = Developer.objects.create(name="Rose", email="rose@gmail.com")
        directory = Directory.objects.create(name="src/main/org/apache/ant", project=project)
        tag = Tag.objects.create(description="rel/1.1",project=project)
        tag2 = Tag.objects.create(description="rel/1.2",project=project)
        commit = Commit.objects.create(hash="oioioi", tag=tag, author=developer, committer=developer2,
                        author_date=datetime.datetime.now().date(), committer_date=datetime.datetime.now().date())
        commit2 = Commit.objects.create(hash="Assoioioi", tag=tag, author=developer, committer=developer,
                                        author_date=datetime.datetime.now().date(),
                                        committer_date=datetime.datetime.now().date())
        commit3 = Commit.objects.create(hash="commit3", tag=tag2, author=developer, committer=developer,
                         author_date=datetime.datetime.now().date(), committer_date=datetime.datetime.now().date())
        commit4 = Commit.objects.create(hash="commit4", tag=tag, author=developer, committer=developer,
                                        author_date=datetime.datetime.now().date(),
                                        committer_date=datetime.datetime.now().date())
        commit5 = Commit.objects.create(hash="commit5", tag=tag, author=developer, committer=developer2,
                                        author_date=datetime.datetime.now().date(),
                                        committer_date=datetime.datetime.now().date())
        # modification
        metrics_by_developer = ArchitectureQualityByDeveloper.objects.create(developer=developer, tag=tag, directory=directory)

        previous_metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
                                                      ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1, commit=commit2)
        metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
                                             previous_architecture_quality_metrics=previous_metrics,
                                             ca=3, ce=2, rma=0.01, rmi=0.012, rmd=0.5, commit=commit)
        metrics3 = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
            ca=2, ce=1, rma=0.001, rmi=0.0152, rmd=0.3, commit=commit4)
        metrics4 = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
                                                             previous_architecture_quality_metrics=metrics3,
                                                            ca=2, ce=1, rma=0.001, rmi=0.0152, rmd=0.6, commit=commit5)

        # methods
        self.assertEqual(metrics_by_developer.commit_activity_in_this_tag,4)
        self.assertEqual(metrics_by_developer.architecturally_impactful_commits,2)
        self.assertEqual(metrics_by_developer.exposition, (metrics_by_developer.architecturally_impactful_commits/metrics_by_developer.commit_activity_in_this_tag))
        self.assertEqual(metrics_by_developer.delta_rmd, 0.7)
        self.assertEqual(metrics_by_developer.architectural_impactful_loc, 0.0)
        self.assertIs(metrics_by_developer.directory.visible, True)