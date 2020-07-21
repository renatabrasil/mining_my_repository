# standard library
import datetime
import math

# Django
from django.test import TestCase
# third-party
from model_mommy import mommy

# local Django
from contributions.models import (
    Commit, Developer, Directory, DirectoryReport, IndividualContribution,
    Modification, Project, ProjectIndividualContribution, ProjectReport, Tag)


class DeveloperModelTests(TestCase):
    @classmethod
    def create_developer(self, name="Renata B", email="renata@gmail.com"):
        return Developer.objects.create(name=name, email=email)
    def test_developer_name(self):
        dev = self.create_developer()

        self.assertEqual(dev.__str__(), "Renata B (renata@gmail.com)")

class ProjectModelTests(TestCase):
    @classmethod
    def create_project(self, name="Project 1", path="https://github.com/project_1"):
        return Project.objects.create(project_name=name, project_path=path)

    def test_project_name(self):
        proj = self.create_project()

        self.assertEqual(proj.__str__(), "Project 1")
        
    def test_first_tag(self):
        project = mommy.make(Project)
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None, project=project)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=project)
        tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=project)

        self.assertEqual(project.first_tag, tag)

class TagModelTests(TestCase):
    @classmethod
    def create_tag(self,project,previous_tag=None,description="rel/1.1"):
        return Tag.objects.create(project=project, description=description,previous_tag=previous_tag)
    def test_tag_description(self):
        tag = self.create_tag(ProjectModelTests.create_project())

        self.assertEqual(tag.__str__(),"rel/1.1")

class DirectoryModelTests(TestCase):
    @classmethod
    def create_directory(self, project, name="main",visible=True):
        return Directory.objects.create(project=project, name=name,visible=visible)
    def test_directory_name(self):
        directory = self.create_directory(ProjectModelTests.create_project())
        self.assertEqual(directory.__str__(),"main - Visible: True")

class CommitModelTests(TestCase):
    def test_has_files_in_this_directory(self):
        # commit = self.create_commit(TagModelTests.create_tag(ProjectModelTests.create_project()),
        #                             DeveloperModelTests.create_developer(), DeveloperModelTests.create_developer("Marcia"))

        commit = mommy.make(Commit)
        directory = mommy.make(Directory)
        mod = mommy.make(Modification, commit=commit, directory=directory)

        # FIXME:
        # self.assertTrue(commit.has_files_in_this_directory(mod.directory))
        # self.assertTrue(commit2.has_files_in_this_directory(modifications_set[0].directory))
        # self.assertEqual(commit.id, mod.commit.id)
        # self.assertEqual(len(commit.modifications.all()), 1)
        pass

    def test_commit_name(self):
        dev = mommy.make(Developer, name='Romulo')
        commit = mommy.make(Commit, hash='aBaBaB27', author=dev)
        self.assertEqual(commit.__str__(), 'aBaBaB27 - Author: Romulo')

    def test_parents(self):
        commit2 = mommy.make(Commit, hash="Oioioioioi")
        commit2.parents=[]
        commit = mommy.make(Commit, parents_str="Oioioioioi")
        self.assertTrue(isinstance(commit.parents, list))
        self.assertEqual(commit.parents[0].hash,commit2.hash)

    def test_number_of_java_files(self):
        directory = mommy.make(Directory, name='src')
        commit = mommy.make("contributions.Commit", hash="oi")
        modification = mommy.make(Modification,path="main.java", new_path="main.java", directory=directory, commit=commit)
        # FIXME: commit association is not working
        # modification2 = mommy.make(Modification,path="test.java", new_path="test.java", old_path="test.java",
        #                            commit=modification.commit, directory=directory)
        # self.assertEqual(modification.commit.hash, 'oi')
        # self.assertEqual(modification.commit.number_of_java_files,1)

    def test_cloc(self):
        commit = mommy.make(Commit, hash="oi")
        # FIXME
        # modification = mommy.make(Modification, _save_kwargs={'added': 10})
        modification = mommy.make(Modification, cloc=30)
        # self.assertEqual(modification.commit.cloc,30)

    def test_save_children_commit(self):
        project = ProjectModelTests.create_project()
        developer = DeveloperModelTests.create_developer()
        tag = TagModelTests.create_tag(ProjectModelTests.create_project())
        directory = Directory.objects.create(name="src/main/org/apache/ant", project=project)
        commit = Commit.objects.create(hash="oioioi", tag=tag, author=developer, committer=developer,
                                       author_date=datetime.datetime.now().date(),
                                       committer_date=datetime.datetime.now().date())
        commit2 = Commit.objects.create(hash="Assoioioi", tag=tag, author=developer, committer=developer,
                                        author_date=datetime.datetime.now().date(),
                                        committer_date=datetime.datetime.now().date(), parents_str='oioioi')

        mod = mommy.make(Modification)
        mod.commit = commit
        # commit.children_commit = commit2
        commit.save()
        commit2.save()

        # TODO: tests
        # self.assertEqual(commit.children_commit.id, commit2.id)

# FIXME: cloc uncommented lines test
class ModifiModelTests(TestCase):
    def test_modification_name(self):
        commit = mommy.make(Commit, hash='hey')
        directory = mommy.make(Directory, name="src/main/apache")
        modification = mommy.make(Modification, new_path="src/main/apache/main.java", directory=directory, commit=commit)
        modification2 = mommy.make(Modification, new_path="test.java",
                                  commit=commit, directory=directory)
        self.assertEqual(modification.__str__(), 'Commit: ' + modification.commit.hash + ' - Directory: src/main/apache - File name: main.java')
        # self.assertEqual(modification2.__str__(),
        #                  'Commit: ' + modification2.commit.hash + ' - Directory: src/main/apache  - File name: test.java')

    def test_diff_text(self):
        commit = mommy.make(Commit, hash='hey')
        directory = mommy.make(Directory, name="src/main/apache")
        modification = mommy.make(Modification, new_path="src/main/apache/main.java", directory=directory,
                                  commit=commit, diff="\n+ public void {\n\n- * @author")
        self.assertEqual(modification.diff_added,'\n0 lines added: \n\n2 +  public void {')
        self.assertEqual(modification.diff_removed, '\n0 lines removed:  \n\n3 -  * @author')

class ProjectIndividualContributionModelTests(TestCase):
    def test_project_report_name(self):
        dev = mommy.make(Developer, name='James')
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        project_r = mommy.make(ProjectReport, tag=tag, total_commits=10, total_files=10, total_cloc=10)
        project_report = mommy.make(ProjectIndividualContribution, commits=1, files=1, cloc=1,
                                    author=dev, project_report=project_r, _save_kwargs={})
        project_report.save()

        self.assertEqual(project_report.__str__(), 'Author: James - Experience: ' + str(project_r.experience)+' - Tag: rel/1.1')
    def test_calculate_boosting_factor(self):
        dev = mommy.make(Developer, name='James')
        dev2 = mommy.make(Developer, name='Ricardo')
        tag1 = mommy.make(Tag, description='rel/1.1', previous_tag=None, id=1)
        project_r = mommy.make(ProjectReport, tag=tag1, total_commits=10, total_files=100, total_cloc=1000)
        project_report = mommy.make(ProjectIndividualContribution, author=dev, commits=1, files=10, cloc=100,
                                    project_report=project_r)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag1, id=2, project=tag1.project)
        project_r2 = mommy.make(ProjectReport, tag=tag2, total_commits=120, total_files=120, total_cloc=1600)
        project_report2 = mommy.make(ProjectIndividualContribution, author=dev, commits=10, files=12, cloc=250,
                                     project_report=project_r2)
        tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=tag1.project, id=3)
        project_r3 = mommy.make(ProjectReport, tag=tag3, total_commits=140, total_files=160, total_cloc=1950)
        project_report3 = mommy.make(ProjectIndividualContribution, author=dev, commits=14, files=22, cloc=320,
                                     project_report=project_r3)
        project_report2_1 = mommy.make(ProjectIndividualContribution, author=dev2, commits=2,
                                       files=6, cloc=500, project_report=project_r2)

        tag_ = mommy.make(Tag, description='1rel/1.1', previous_tag=None)
        tag_2 = mommy.make(Tag, description='1rel/1.2', previous_tag=tag_)
        tag_3 = mommy.make(Tag, description='1rel/1.3', previous_tag=tag_2)
        # project_r_ = mommy.make(ProjectReport, tag=tag_3, total_commits=10, total_files=10, total_cloc=10)
        # project_report_ = mommy.make(ProjectIndividualContribution, author=dev,
        #                              commits=2, files=2,
        #                              cloc=2, project_report=project_r_)

        # Test first project contribution by Ricardo

        self.assertAlmostEqual(project_report.experience, 0.1,5)
        self.assertAlmostEqual(project_report.experience_bf, 0.1,5)

        # self.assertAlmostEqual(project_report2.ownership_commits, 10/120, 6)
        # self.assertListEqual(project_report3.__all_previous_contributions__(),[])
        # self.assertListEqual(project_report3.__all_previous_contributions__(),[])
        self.assertListEqual(project_report.commit_activity, [0.1])
        self.assertListEqual(project_report2.commit_activity,[0.1,9/110])
        self.assertListEqual(project_report3.commit_activity, [0.1, 9/110,0.2])
        self.assertAlmostEqual(project_report2.commit_exp, 0.136363636, 5)
        self.assertAlmostEqual(project_report2.file_exp, 0.1, 5)
        self.assertAlmostEqual(project_report2.cloc_exp, 0.2625, 5)

        self.assertAlmostEqual(project_report3.commit_exp, 0.176223776, 5)
        self.assertAlmostEqual(project_report3.file_exp, 0.2, 5)
        self.assertAlmostEqual(project_report3.cloc_exp, 0.285185185, 5)


        # FIXME: create tests where first tag is not id=1 and there some gaps between tags
        self.assertAlmostEqual(project_report2.experience, 0.128181818, 5)
        self.assertAlmostEqual(project_report2.experience_bf, 0.172272727, 5)
        self.assertAlmostEqual(project_report3.experience, 0.158787879, 5)
        self.assertAlmostEqual(project_report3.experience_bf, 0.229318829, 5)

        # Test when a developer starts to contribute later
        # self.assertListEqual(project_report3.commit_activity, [])
        self.assertAlmostEqual(project_report2_1.ownership_commits_in_this_tag, 0.018181818,5)
        self.assertAlmostEqual(project_report2_1.bf_commit, 0.5, 5)
        self.assertAlmostEqual(project_report2_1.commit_exp, 0.013636364, 5)
        self.assertAlmostEqual(project_report2_1.experience, 0.228484848, 5)
        self.assertAlmostEqual(project_report2_1.experience_bf, 0.342727273, 5)

class ProjectReportModelTests(TestCase):
    def test_project_report_name(self):
        tag = mommy.make(Tag, description='rel/1.2')
        report = mommy.make(ProjectReport,tag=tag)

        self.assertEqual(report.__str__(), 'Project tag: rel/1.2')

    # mean
    # standard deviation
    # median
    def test_statistics(self):
        dev = mommy.make(Developer, name='Ricardo')
        tag1 = mommy.make(Tag, description='rel/1.1', previous_tag=None, id=1)
        dev2 = mommy.make(Developer, name='Romulo')
        dev3 = mommy.make(Developer, name='Renata')
        project_r = mommy.make(ProjectReport, tag=tag1, total_commits=5, total_files=10, total_cloc=100)
        project_report = mommy.make(ProjectIndividualContribution, author=dev,
                                    commits=50, files=100, cloc=1000, project_report=project_r,
                                    experience_bf=0.1)
        project_report2 = mommy.make(ProjectIndividualContribution, author=dev, project_report=project_r)
        project_report2_1 = mommy.make(ProjectIndividualContribution, author=dev2, project_report=project_r)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag1, id=2, project=tag1.project)
        project_r2 = mommy.make(ProjectReport, tag=tag2)
        project_report2_2 = mommy.make(ProjectIndividualContribution, author=dev3, project_report=project_r2)
        project_r.calculate_statistical_metrics()
        project_r2.calculate_statistical_metrics()
        # FIXME
        # self.assertAlmostEqual(project_r.mean,0.151524001,5)
        # self.assertAlmostEqual(project_r.median, 0.2, 5)
        # self.assertTrue(math.isnan(project_r.standard_deviation))
        #

        # self.assertAlmostEqual(project_r2.mean, 0.383333333, 5)
        # self.assertAlmostEqual(project_r2.median, 0.2, 5)
        # self.assertAlmostEqual(project_r2.standard_deviation, 0.361708907, 5)

    # FIXME: create data for tests
    def test_lists(self):
        dev = mommy.make(Developer, name='Ricardo', email='ricardo@gmail.com')
        dev2 = mommy.make(Developer, name='Romulo', email='romulo@gmail.com')
        dev3 = mommy.make(Developer, name='Renata', email='renata@gmail.com')
        tag1 = mommy.make(Tag, description='rel/1.1', previous_tag=None, id=1)
        project_r = mommy.make(ProjectReport, tag=tag1, total_commits=5, total_files=10, total_cloc=100)
        project_report = mommy.make(ProjectIndividualContribution, author=dev, commits=1, files=2, cloc=20,
                                    project_report=project_r)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag1, id=2, project=tag1.project)
        project_r2 = mommy.make(ProjectReport, tag=tag2, total_commits=10, total_files=10, total_cloc=10)
        project_report2 = mommy.make(ProjectIndividualContribution, author=dev, commits=6, files=7,
                                     cloc=5, project_report=project_r2)
        project_report2_1 = mommy.make(ProjectIndividualContribution, author=dev2, commits=2,
                                       files=2, cloc=2, project_report=project_r2)
        project_report2_2 = mommy.make(ProjectIndividualContribution, author=dev3, commits=8,
                                     files=8, cloc=8, project_report=project_r2)
        project_r.calculate_statistical_metrics()
        project_r2.calculate_statistical_metrics()
        # For one developer
        # FIXME
        # self.assertListEqual(project_r.core_developers_experience,[dev])
        # self.assertListEqual(project_r.peripheral_developers_experience, [])
        # self.assertAlmostEqual(project_r.experience,0.2,5)
        # self.assertAlmostEqual(project_r.ownership, 0.2, 5)
        # self.assertEqual(project_r.major, 1)
        # self.assertEqual(project_r.minor, 0)

        # For more than one developer
        # FIXME
        # self.assertListEqual(project_r2.core_developers_experience, [dev3])
        # self.assertListEqual(project_r2.peripheral_developers_experience, [dev,dev2])
        # self.assertAlmostEqual(project_r2.experience, 0.8, 5)
        self.assertAlmostEqual(project_r2.ownership, 0.8, 5)
        self.assertEqual(project_r2.major, 3)
        self.assertEqual(project_r2.minor, 0)

class IndividualContributionModelTests(TestCase):
    def test_individual_contribution(self):
        dev = mommy.make(Developer, name='Ricardo')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report,
                                  ownership_commits=0.625,ownership_files=0.25,ownership_cloc=0.85)

        self.assertEqual(contribution.__str__(),'Author: Ricardo - Directory: src/main/apache - Experience: 0.52 - Tag: rel/1.1')

    def test_ownership_in_this_tag(self):
        dev = mommy.make(Developer, name='Ricardo')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag, total_commits=16, total_files=8,
                            total_cloc=100)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report,
                                  commits=10,files=2,cloc=85,
                                  ownership_commits=0.625, ownership_files=0.25, ownership_cloc=0.85)
        report2 = mommy.make(DirectoryReport, directory=directory, tag=tag2, total_commits=26, total_files=18,
                             total_cloc=150)
        contribution2_1 = mommy.make(IndividualContribution, author=dev, directory_report=report2,
                                     commits=18, files=6, cloc=95)

        self.assertEqual(contribution.ownership_commits_in_this_tag, 0.625)
        self.assertEqual(contribution.ownership_files_in_this_tag, 0.25)
        self.assertEqual(contribution.ownership_cloc_in_this_tag, 0.85)

        self.assertEqual(contribution2_1.ownership_commits_in_this_tag,0.8)
        self.assertEqual(contribution2_1.ownership_files_in_this_tag, 0.4)
        self.assertEqual(contribution2_1.ownership_cloc_in_this_tag, 0.2)

    def test_calculate_boosting_factor(self):
        dev = mommy.make(Developer, name='Ricardo')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=tag.project)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag, total_commits=16,total_files=8,total_cloc=100)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report, commits=10, files=2,
                                  cloc=85,
                                  ownership_commits=0.625, ownership_files=0.25, ownership_cloc=0.85)
        report2 = mommy.make(DirectoryReport, directory=directory, tag=tag2, total_commits=26, total_files=18,
                            total_cloc=150)
        contribution2_1 = mommy.make(IndividualContribution, author=dev, directory_report=report2,
                                     commits=18, files=6, cloc=95,
                                     ownership_commits=18/26, ownership_files=6/18, ownership_cloc=95/150)

        # For one developer
        self.assertAlmostEqual(contribution.experience, 0.52, 5)
        self.assertAlmostEqual(contribution.experience_bf, 0.52, 5)

        # self.assertAlmostEqual(contribution2_1.ownership_commits_in_this_tag, 0.8, 5)
        self.assertListEqual(contribution2_1.commit_activity,[0.625,0.8])
        self.assertListEqual(contribution2_1.file_activity, [0.25, 4/10])
        self.assertListEqual(contribution2_1.cloc_activity, [0.85, 10/50])

        # For more than one tag
        # self.assertAlmostEqual(contribution2_1.experience, 349/1300, 5)
        # self.assertAlmostEqual(contribution2_1.experience_bf,17983/31200, 5)

        # FIXME: create tests where first tag is not id=1 and there some gaps between tags

    def test_calculate_boosting_factor_with_skips(self):
        dev = mommy.make(Developer, name='Ricardo')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=tag.project)
        tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=tag.project)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag, total_commits=10,total_files=10,total_cloc=10)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report, commits=1, files=1,
                                  cloc=1,
                                  ownership_commits=0.1, ownership_files=0.1, ownership_cloc=0.1)
        report3 = mommy.make(DirectoryReport, directory=directory, tag=tag3, total_commits=90, total_files=90,
                            total_cloc=90)
        contribution3_1 = mommy.make(IndividualContribution, author=dev, directory_report=report3,
                                     commits=2, files=2, cloc=2,
                                     ownership_commits=2/90, ownership_files=2/90, ownership_cloc=2/90)

        # For one developer
        self.assertAlmostEqual(contribution.experience, 0.1, 5)
        self.assertAlmostEqual(contribution.experience_bf, 0.1, 5)

        self.assertListEqual(contribution.commit_activity, [0.1])
        self.assertEqual(len(contribution3_1.__all_previous_contributions__()),1)
        self.assertListEqual(contribution3_1.commit_activity, [0.1, 0.0, 0.0125])
        self.assertListEqual(contribution3_1.file_activity, [0.1,0.0,0.0125])
        self.assertListEqual(contribution3_1.cloc_activity, [0.1,0.0,0.0125])

        # For more than one tag
        self.assertAlmostEqual(contribution3_1.bf_commit, 0.375, 5)
        self.assertAlmostEqual(contribution3_1.bf_file, 0.375, 5)
        self.assertAlmostEqual(contribution3_1.bf_cloc, 0.375, 5)

        self.assertAlmostEqual(contribution3_1.commit_exp, 0.0515625, 5)
        # self.assertEqual(len(contribution3_1.commit_activity), 3)
        self.assertAlmostEqual(contribution3_1.experience, 0.0375, 5)
        self.assertAlmostEqual(contribution3_1.experience_bf, 0.051563, 5)

class DirectoryReportModelTests(TestCase):
    def test_report_name(self):
        tag = mommy.make(Tag, description='rel/1.1')
        directory = mommy.make(Directory, name='src/main/apache')
        report = mommy.make(DirectoryReport, directory=directory, tag=tag)

        self.assertEqual(report.__str__(), 'Tag: rel/1.1 - Directory: src/main/apache')

    # FIXME: first_directory_report
    def test_directory_report(self):
        dev = mommy.make(Developer, name='Ricardo')
        dev2 = mommy.make(Developer, name='James')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=tag.project)
        tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=tag.project)
        tag4 = mommy.make(Tag, description='rel/1.4', previous_tag=tag3, project=tag.project)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag, total_commits=10, total_files=10,
                            total_cloc=10)
        report2 = mommy.make(DirectoryReport, directory=directory, tag=tag2)
        report3 = mommy.make(DirectoryReport, directory=directory, tag=tag3)
        contribution_ = mommy.make(IndividualContribution, author=dev2, directory_report=report2)
        contribution_2 = mommy.make(IndividualContribution, author=dev, directory_report=report3)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report3)
        contribution3_1 = mommy.make(IndividualContribution, author=dev, directory_report=report3)
        #
        # tag =DirectoryReport.first_directory_report
        # self.assertEqual(tag, 2)


    # mean
    # standard deviation
    # median
    def test_statistics(self):
        dev = mommy.make(Developer, name='Ricardo')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=tag.project)
        tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=tag.project)
        tag4 = mommy.make(Tag, description='rel/1.4', previous_tag=tag3, project=tag.project)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag, total_commits=10, total_files=10,
                            total_cloc=10)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report, commits=1, files=1,
                                  cloc=1,
                                  ownership_commits=0.1, ownership_files=0.1, ownership_cloc=0.1)
        contribution_ = mommy.make(IndividualContribution, author=dev, directory_report=report, commits=1, files=1,
                                  cloc=1,
                                  ownership_commits=0.4, ownership_files=0.4, ownership_cloc=0.4)
        contribution_2 = mommy.make(IndividualContribution, author=dev, directory_report=report, commits=1, files=1,
                                   cloc=1,
                                   ownership_commits=0.3, ownership_files=0.3, ownership_cloc=0.3)

        report3 = mommy.make(DirectoryReport, directory=directory, tag=tag3, total_commits=90, total_files=90,
                             total_cloc=90)
        contribution3_1 = mommy.make(IndividualContribution, author=dev, directory_report=report3,
                                     commits=2, files=2, cloc=2,
                                     ownership_commits=2 / 90, ownership_files=2 / 90, ownership_cloc=2 / 90)

        report4 = mommy.make(DirectoryReport, directory=directory, tag=tag4, total_commits=120, total_files=120,
                             total_cloc=120)
        contribution4_1 = mommy.make(IndividualContribution, author=dev, directory_report=report4,
                                     commits=3, files=3, cloc=3,
                                     ownership_commits=3/120, ownership_files=3/120, ownership_cloc=3/120)

        report.calculate_statistical_metrics()
        report3.calculate_statistical_metrics()
        report4.calculate_statistical_metrics()
        self.assertAlmostEqual(report3.mean, 0.0515625, 5)
        self.assertAlmostEqual(report3.median, 0.0515625, 5)
        self.assertTrue(math.isnan(report3.standard_deviation))
        self.assertAlmostEqual(report.mean, 0.266666667, 5)
        self.assertAlmostEqual(report.median, 0.3, 5)
        self.assertAlmostEqual(report.standard_deviation, 0.152752523, 5)

        self.assertAlmostEqual(contribution.experience_bf, 0.1, 5)
        self.assertAlmostEqual(contribution_.experience_bf, 0.4, 5)
        self.assertAlmostEqual(contribution_2.experience_bf, 0.3, 5)
        self.assertAlmostEqual(contribution3_1.experience_bf,0.0515625,5)

        # self.assertAlmostEqual(contribution3_1.experience_bf, 0.049750434, 5)
        self.assertAlmostEqual(contribution4_1.experience_bf, 0.049750434, 5)

    def test_lists(self):
        dev = mommy.make(Developer, name='Ricardo')
        dev2 = mommy.make(Developer, name='Romulo')
        dev3 = mommy.make(Developer, name='Renata')
        dev4 = mommy.make(Developer, name='Daniela')
        directory = mommy.make(Directory, name="src/main/apache")
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=tag.project)
        tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=tag.project)
        tag4 = mommy.make(Tag, description='rel/1.4', previous_tag=tag3, project=tag.project)
        report = mommy.make(DirectoryReport, directory=directory, tag=tag, total_commits=10, total_files=10,
                            total_cloc=10)
        contribution = mommy.make(IndividualContribution, author=dev, directory_report=report, commits=1, files=1,
                                  cloc=1,
                                  ownership_commits=0.8, ownership_files=0.8, ownership_cloc=0.8)
        contribution_ = mommy.make(IndividualContribution, author=dev2, directory_report=report, commits=1, files=1,
                                   cloc=1,
                                   ownership_commits=0.5, ownership_files=0.6, ownership_cloc=0.4)
        contribution_2 = mommy.make(IndividualContribution, author=dev3, directory_report=report, commits=1, files=1,
                                    cloc=1,
                                    ownership_commits=0.003, ownership_files=0.003, ownership_cloc=0.003)
        contribution_3 = mommy.make(IndividualContribution, author=dev4, directory_report=report, commits=1, files=1,
                                    cloc=1,
                                    ownership_commits=0.3, ownership_files=0.3, ownership_cloc=0.8)

        # self.assertEqual(contribution_2.experience, 0)
        # FIXME:
        self.assertEqual(len(report.core_developers_experience),4)
        # self.assertListEqual(report.core_developers_experience,[])
        self.assertListEqual(report.peripheral_developers_experience,[])
        self.assertAlmostEqual(report.experience, 0.8)
        self.assertEqual(report.ownership, 0.8)
        self.assertEqual(report.major, 3)
        self.assertEqual(report.minor, 1)
