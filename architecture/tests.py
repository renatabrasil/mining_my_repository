from django.test import TestCase

# Create your tests here.
from architecture.models import ArchitectureQualityMetrics, ArchitectureQualityByDeveloper
from contributions.models import Developer, Directory, Tag, Commit, Modification, Project


class ArchitectureQualityMetricsModelTests(TestCase):

    def test_delta_metrics(self):
        # previous_metrics = ArchitectureQualityMetrics()
        previous_metrics = ArchitectureQualityMetrics(ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1)
        metrics = ArchitectureQualityMetrics(previous_architecture_quality_metrics=previous_metrics,
                                             ca=3,ce=2,rma=0.01,rmi=0.012,rmd=0.5)

        self.assertEqual(metrics.delta_rmd,0.4)
        self.assertEqual(metrics.delta_rma, 0.0)
        self.assertEqual(metrics.delta_rmi, 0.01)

class ArchitectureQualityByDeveloperModelTests(TestCase):
    def test_commit_activity_in_this_tag(self):
        project = Project(pk=1,project_name="Ant")
        developer = Developer(pk=1,name="Jack",email="jack@gmail.com")
        # directory = Directory(pk=1,name="src/main/org/apache/ant").save()
        tag = Tag(pk=1,description="rel/1.1",project=project)
        tag2 = Tag(pk=2,description="rel/1.2",project=project)
        commit = Commit(pk=1,hash="oioioi", tag=tag, author=developer, committer=developer)
        commit2 = Commit(pk=2,hash="Assoioioi", tag=tag2, author=developer, committer=developer)
        # mod = Modification(commit=commit, directory=directory)

        metrics_by_developer = ArchitectureQualityByDeveloper(pk=1,developer=developer, tag=tag)


        previous_metrics = ArchitectureQualityMetrics(pk=1,architecture_quality_by_developer_and_directory=metrics_by_developer,
                                                      ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1)

        metrics = ArchitectureQualityMetrics(pk=2,architecture_quality_by_developer_and_directory=metrics_by_developer,
                                             previous_architecture_quality_metrics=previous_metrics,
                                             ca=3, ce=2, rma=0.01, rmi=0.012, rmd=0.5)




        # TOFIX: this text
        # technical debt
        self.assertEqual(metrics_by_developer.commit_activity_in_this_tag,0)
        self.assertEqual(metrics_by_developer.architecturally_impactful_commits,1)
        self.assertEqual(metrics_by_developer.exposition, 1.0)