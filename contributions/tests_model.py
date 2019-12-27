import datetime

from django.test import TestCase

# Create your tests here.
from model_mommy import mommy

from contributions.models import Project, Developer, Tag, Directory, Commit, Modification, \
    ProjectIndividualContribution, ProjectReport


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
        directory = mommy.make(Directory)
        commit = mommy.make("contributions.Commit", hash="oi")
        modification = mommy.make(Modification,path="main.java", new_path="main.java", directory=directory, commit=commit)
        # FIXME: commit association is not working
        # modification2 = mommy.make(Modification,path="test.java", new_path="test.java", old_path="test.java",
        #                            commit=modification.commit, directory=directory)
        self.assertEqual(modification.commit.number_of_java_files,1)

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
        dev = mommy.make(Developer, name='Ricardo')
        tag = mommy.make(Tag, description='rel/1.1', previous_tag=None)
        project_r = mommy.make(ProjectReport, tag=tag)
        project_report = mommy.make(ProjectIndividualContribution, ownership_commits=0.2, ownership_files=0.2, ownership_cloc=0.1,
                                    author=dev, project_report=project_r, _save_kwargs={})
        project_report.save()

        self.assertEqual(project_report.__str__(), 'Author: Ricardo - Experience: ' + str(project_r.experience)+' - Tag: rel/1.1')
    def test_calculate_boosting_factor(self):
        dev = mommy.make(Developer, name='Ricardo')
        dev2 = mommy.make(Developer, name='Romulo')
        tag_ = mommy.make(Tag, description='1rel/1.1', previous_tag=None)
        tag_2 = mommy.make(Tag, description='1rel/1.2', previous_tag=tag_)
        tag_3 = mommy.make(Tag, description='1rel/1.3', previous_tag=tag_2)
        project_r_ = mommy.make(ProjectReport, tag=tag_3)
        project_report_ = mommy.make(ProjectIndividualContribution, author=dev,
                                    ownership_commits=0.2, ownership_files=0.2,
                                    ownership_cloc=0.2, project_report=project_r_)

        tag1 = mommy.make(Tag, description='rel/1.1', previous_tag=None, id=1)
        project_r = mommy.make(ProjectReport, tag=tag1, total_commits=5, total_files=10, total_cloc=100)
        project_report = mommy.make(ProjectIndividualContribution, author=dev,
                                    ownership_commits=0.2, ownership_files=0.2,
                                    ownership_cloc=0.2, project_report=project_r)
        tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag1, id=2, project=tag1.project)
        project_r2 = mommy.make(ProjectReport, tag=tag2)
        project_report2 = mommy.make(ProjectIndividualContribution, author=dev, ownership_commits=0.6, ownership_files=0.7,
                                    ownership_cloc=0.5, project_report=project_r2)
        project_report2_1 = mommy.make(ProjectIndividualContribution, author=dev2, ownership_commits=0.2,
                                     ownership_files=0.2,
                                     ownership_cloc=0.2, project_report=project_r2)

        # Test first project contribution by Ricardo
        self.assertAlmostEqual(project_report.experience, 0.2,5)
        self.assertAlmostEqual(project_report.experience_bf, 0.2,5)

        # Test second project contribution (with boosting factor) by Ricardo
        self.assertAlmostEqual(project_report2.experience, 0.31,5)
        self.assertAlmostEqual(project_report2.experience_bf, 0.465,5)

        # Test first project contribution (with boosting factor) by Romulo
        self.assertAlmostEqual(project_report2_1.experience, 0.1, 5)
        self.assertAlmostEqual(project_report2_1.experience_bf, 0.15, 5)

        # Test first project contribution (with boosting factor) by Ricardo after 3 tags with none contributions
        self.assertAlmostEqual(project_report_.experience, 0.2,5)
        self.assertAlmostEqual(project_report_.experience_bf, 0.2, 5)

class ProjectReportModelTests(TestCase):
    def test_project_report_name(self):
        tag = mommy.make(Tag, description='rel/1.2')
        report = mommy.make(ProjectReport,tag=tag)

        self.assertEqual(report.__str__(), 'Project tag: rel/1.2')