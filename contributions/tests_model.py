# standard library
import datetime
import math

# Django
from unittest.mock import patch, Mock

from django.test import TestCase
# third-party
from model_mommy import mommy

# local Django
from contributions.models import (
    Commit, Developer, Directory,
    Modification, Project, Tag)


# class DeveloperModelTests(TestCase):
#     @classmethod
#     def create_developer(self, name="Renata B", email="renata@gmail.com"):
#         return Developer.objects.create(name=name, email=email)
#
#     def test_developer_name(self):
#         dev = self.create_developer()
#
#         self.assertEqual(dev.__str__(), "Renata B (renata@gmail.com)")


# class ProjectModelTests(TestCase):
#     @classmethod
#     def create_project(self, name="Project 1", path="https://github.com/project_1"):
#         return Project.objects.create(project_name=name, project_path=path)
#
#     def test_project_name(self):
#         proj = self.create_project()
#
#         self.assertEqual(proj.__str__(), "Project 1")
#
#     def test_first_tag(self):
#         project = mommy.make(Project)
#         tag = mommy.make(Tag, description='rel/1.1', previous_tag=None, project=project)
#         tag2 = mommy.make(Tag, description='rel/1.2', previous_tag=tag, project=project)
#         tag3 = mommy.make(Tag, description='rel/1.3', previous_tag=tag2, project=project)
#
#         self.assertEqual(project.first_tag, tag)


# class TagModelTests(TestCase):
#     @classmethod
#     def create_tag(self, project, previous_tag=None, description="rel/1.1"):
#         return Tag.objects.create(project=project, description=description, previous_tag=previous_tag)
#
#     def test_tag_description(self):
#         tag = self.create_tag(ProjectModelTests.create_project())
#
#         self.assertEqual(tag.__str__(), "rel/1.1")


# class DirectoryModelTests(TestCase):
#     @classmethod
#     def create_directory(self, project, name="main", visible=True):
#         return Directory.objects.create(project=project, name=name, visible=visible)
#
#     def test_directory_name(self):
#         directory = self.create_directory(ProjectModelTests.create_project())
#         self.assertEqual(directory.__str__(), "main - Visible: True")


class CommitModelTests(TestCase):
    @patch('main.models.update_commit')
    def test_calculate_general_experience_successfully(self):
        au = Mock(Developer)
        author = mommy.make(Developer)
        committer = mommy.make(Developer)
        tag = mommy.make(Tag)

        Commit.objects.filter(hash=any())

        Mock


        commit = Commit(author=author, committer=committer, tag=tag)

        commit.save()

        self.assertIsNone(commit)


# # FIXME: cloc uncommented lines test
# class ModifiModelTests(TestCase):
#     def test_modification_name(self):
#         commit = mommy.make(Commit, hash='hey')
#         directory = mommy.make(Directory, name="src/main/apache")
#         modification = mommy.make(Modification, new_path="src/main/apache/main.java", directory=directory,
#                                   commit=commit)
#         modification2 = mommy.make(Modification, new_path="test.java",
#                                    commit=commit, directory=directory)
#         self.assertEqual(modification.__str__(),
#                          'Commit: ' + modification.commit.hash + ' - Directory: src/main/apache - File name: main.java')
#         # self.assertEqual(modification2.__str__(),
#         #                  'Commit: ' + modification2.commit.hash + ' - Directory: src/main/apache  - File name: test.java')
#
#     def test_diff_text(self):
#         commit = mommy.make(Commit, hash='hey')
#         directory = mommy.make(Directory, name="src/main/apache")
#         modification = mommy.make(Modification, new_path="src/main/apache/main.java", directory=directory,
#                                   commit=commit, diff="\n+ public void {\n\n- * @author")
#         self.assertEqual(modification.diff_added, '\n0 lines added: \n\n2 +  public void {')
#         self.assertEqual(modification.diff_removed, '\n0 lines removed:  \n\n3 -  * @author')
#
