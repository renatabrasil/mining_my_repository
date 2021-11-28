from django.test import TestCase

from architecture.models import (FileCommits)
from contributions.models import (Project, Tag)


# Create your tests here.


class FileCommitsModelTests(TestCase):
    def test_name_file(self):
        project = Project.objects.create(project_name="Ant")
        tag = Tag.objects.create(description="rel/1.1", project=project)
        file = FileCommits.objects.create(name="File 1", directory="desktop", tag=tag, build_path='',
                                          local_repository='')

        self.assertEqual(file.__str__(), 'desktop/File 1')

# class ArchitectureQualityMetricsModelTests(TestCase):
# def setUp(self):
#     self.commit = Recipe(Commit,
#                          hash='Commit1'
#                          )
#     self.modification_ucloc = Recipe(Modification,
#                                      path='test.java',
#                                      added=2,
#                                      removed=1,
#                                      commit=foreign_key(self.commit)
#                                      )

# TODO: delete
# def test_delta_metrics(self):
#     # previous_metrics = ArchitectureQualityMetrics()
#     project = mommy.make(Project)
#     developer = mommy.make(Developer,name="Jack", email="jack@gmail.com")
#     tag = mommy.make(Tag,description="rel/1.1", project=project)
#     directory = mommy.make(Directory, name="src/main/org/apache/ant", project=project)
#
#     # commit = Commit.objects.create(hash="oioioi", tag=tag, author=developer, committer=developer)
#     # commit2 = Commit.objects.create(hash="Assoioioi", tag=tag, author=developer, committer=developer,
#     #                                 parents_str='oioioi')
#
#     # one line added
#     kid = mommy.make('contributions.Commit', tag=tag)
#     modification = mommy.make(Modification, directory=directory)
#     modification2 = mommy.make('contributions.Modification', commit=[kid], make_m2m=True,
#                                directory=directory,diff="\n+ public void {\n\n- * @author", added=2, removed=1)
#
#     project_individual_contribution = mommy.make(ProjectIndividualContribution,author=developer)
#     metrics_by_developer = mommy.make(ArchitectureQualityByDeveloper,
#                                       project_individual_contribution=project_individual_contribution,
#                                       directory=directory, tag=tag)
#
#     previous_metrics = mommy.make(ArchitectureQualityMetrics,commit=modification.commit,
#                                   architecture_quality_by_developer_and_directory=metrics_by_developer,
#                                   ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1)
#     metrics = mommy.make(ArchitectureQualityMetrics,architecture_quality_by_developer_and_directory=metrics_by_developer,
#                          previous_architecture_quality_metrics=previous_metrics, commit=modification2.commit,
#                          ca=3,ce=2,rma=0.01,rmi=0.012,rmd=0.5)
#
#     # metrics_by_developer = ArchitectureQualityByDeveloper.objects.create(developer=developer, tag=tag,
#     #                                                                      directory=directory)
#     # previous_metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
#     #                                                              ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1,
#     #                                                              commit=commit)
#     # metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
#     #                                                     previous_architecture_quality_metrics=previous_metrics,
#     #                                      ca=3,ce=2,rma=0.01,rmi=0.012,rmd=0.5, commit=commit2)
#     commit = modification2.commit
#     # FIXME:
#     modification3 = mommy.make('contributions.Modification', commit=[kid], make_m2m=True,
#                                directory=directory, diff="\n+ public void {\n\n- * @author", added=2, removed=1,
#                                _quantity=3)
#     modification4 = self.modification_ucloc.make()
#     commit = self.commit.make()
#
#     mm = mommy.make(ArchitectureQualityByDeveloper)
#     met = mommy.make(ArchitectureQualityMetrics, commit=kid, architecture_quality_by_developer_and_directory=mm, _quantity=3)
#
#     # met.save()
#     #
#     # self.assertEqual(mm.metrics.all()[2], '')
#     # self.assertEqual(kid.architectural_metrics.all(), '')
#     # self.assertEqual(commit.modifications.all(), '')
#     # self.assertEqual(len(modification.commit.modifications.all()), 1)
#     # self.assertEqual(len(modification2.commit.modifications.all()),1)
#     # self.assertEqual(commit.cloc_uncommented(directory),0)
#     # self.assertEqual(metrics.delta_rmd,0.4)
#     # self.assertEqual(metrics.delta_rma, 0.0)
#     # self.assertEqual(metrics.delta_rmi, 0.01)
#
#     # self.assertEqual(metrics.commit.parents[0], previous_metrics.commit)

# class ArchitectureQualityByDeveloperModelTests(TestCase):
#     def test_commit_activity_in_this_tag(self):
# project = Project.objects.create(project_name="Ant")
# developer = Developer.objects.create(name="Jack",email="jack@gmail.com")
# developer2 = Developer.objects.create(name="Rose", email="rose@gmail.com")
# directory = Directory.objects.create(name="src/main/org/apache/ant", project=project)
# tag = Tag.objects.create(description="rel/1.1",project=project)
# tag2 = Tag.objects.create(description="rel/1.2",project=project)
# commit = Commit.objects.create(hash="oioioi", tag=tag, author=developer, committer=developer2,
#                 author_date=datetime.datetime.now().date(), committer_date=datetime.datetime.now().date())
# commit2 = Commit.objects.create(hash="Assoioioi", tag=tag, author=developer, committer=developer,
#                                 author_date=datetime.datetime.now().date(),
#                                 committer_date=datetime.datetime.now().date())
# commit3 = Commit.objects.create(hash="commit3", tag=tag2, author=developer, committer=developer,
#                  author_date=datetime.datetime.now().date(), committer_date=datetime.datetime.now().date())
# commit4 = Commit.objects.create(hash="commit4", tag=tag, author=developer, committer=developer,
#                                 author_date=datetime.datetime.now().date(),
#                                 committer_date=datetime.datetime.now().date())
# commit5 = Commit.objects.create(hash="commit5", tag=tag, author=developer, committer=developer2,
#                                 author_date=datetime.datetime.now().date(),
#                                 committer_date=datetime.datetime.now().date())
# modification
# metrics_by_developer = ArchitectureQualityByDeveloper.objects.create(developer=developer, tag=tag, directory=directory)
#
# previous_metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
#                                               ca=3, ce=2, rma=0.01, rmi=0.002, rmd=0.1, commit=commit2)
# metrics = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
#                                      previous_architecture_quality_metrics=previous_metrics,
#                                      ca=3, ce=2, rma=0.01, rmi=0.012, rmd=0.5, commit=commit)
# metrics3 = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
#     ca=2, ce=1, rma=0.001, rmi=0.0152, rmd=0.3, commit=commit4)
# metrics4 = ArchitectureQualityMetrics.objects.create(architecture_quality_by_developer_and_directory=metrics_by_developer,
#                                                      previous_architecture_quality_metrics=metrics3,
#                                                     ca=2, ce=1, rma=0.001, rmi=0.0152, rmd=0.6, commit=commit5)
#
# # methods
# self.assertEqual(metrics_by_developer.commit_activity_in_this_tag,4)
# self.assertEqual(metrics_by_developer.architecturally_impactful_commits,2)
# self.assertEqual(metrics_by_developer.exposition, (metrics_by_developer.architecturally_impactful_commits/metrics_by_developer.commit_activity_in_this_tag))
# self.assertEqual(metrics_by_developer.delta_rmd, 0.7)
# self.assertEqual(metrics_by_developer.architectural_impactful_loc, 0.0)
# self.assertIs(metrics_by_developer.directory.visible, True)
