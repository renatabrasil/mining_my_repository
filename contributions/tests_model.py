# standard library
import datetime
import math

# Django
from django.test import TestCase
# third-party
from model_mommy import mommy

# local Django
from contributions.models import (
    Commit, Developer, Directory,
    Modification, Project, Tag)


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
    def create_tag(self, project, previous_tag=None, description="rel/1.1"):
        return Tag.objects.create(project=project, description=description, previous_tag=previous_tag)

    def test_tag_description(self):
        tag = self.create_tag(ProjectModelTests.create_project())

        self.assertEqual(tag.__str__(), "rel/1.1")


class DirectoryModelTests(TestCase):
    @classmethod
    def create_directory(self, project, name="main", visible=True):
        return Directory.objects.create(project=project, name=name, visible=visible)

    def test_directory_name(self):
        directory = self.create_directory(ProjectModelTests.create_project())
        self.assertEqual(directory.__str__(), "main - Visible: True")


class CommitModelTests(TestCase):
    def test_calculate_general_experience_successfully(self):
        author = mommy.make()
        committer = mommy.make()

        commit = Commit(author=author, committer=committer)

        commit.save()

        self.assertIsNone(commit)

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
        commit2.parents = []
        commit = mommy.make(Commit, parents_str="Oioioioioi")
        self.assertTrue(isinstance(commit.parents, list))
        self.assertEqual(commit.parents[0].hash, commit2.hash)

    def test_number_of_java_files(self):
        directory = mommy.make(Directory, name='src')
        commit = mommy.make("contributions.Commit", hash="oi")
        modification = mommy.make(Modification, path="main.java", new_path="main.java", directory=directory,
                                  commit=commit)
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
        modification = mommy.make(Modification, new_path="src/main/apache/main.java", directory=directory,
                                  commit=commit)
        modification2 = mommy.make(Modification, new_path="test.java",
                                   commit=commit, directory=directory)
        self.assertEqual(modification.__str__(),
                         'Commit: ' + modification.commit.hash + ' - Directory: src/main/apache - File name: main.java')
        # self.assertEqual(modification2.__str__(),
        #                  'Commit: ' + modification2.commit.hash + ' - Directory: src/main/apache  - File name: test.java')

    def test_diff_text(self):
        commit = mommy.make(Commit, hash='hey')
        directory = mommy.make(Directory, name="src/main/apache")
        modification = mommy.make(Modification, new_path="src/main/apache/main.java", directory=directory,
                                  commit=commit, diff="\n+ public void {\n\n- * @author")
        self.assertEqual(modification.diff_added, '\n0 lines added: \n\n2 +  public void {')
        self.assertEqual(modification.diff_removed, '\n0 lines removed:  \n\n3 -  * @author')

