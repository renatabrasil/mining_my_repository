# standard library

# Django

# third-party
# import unittest

from django.test import TestCase

from contributions.models import (
    Developer, Project, Tag, Directory, Commit)


# local Django


def create_project(name="Projeto"):
    return Project.objects.create(project_name=name)


def create_tag(description='rel/1.1', previous_tag=None, project=create_project(), major=True,
               main_directory="main/code", max_minor_version_description="", prepare_build_command=""):
    return Tag.objects.create(description=description, previous_tag=previous_tag, project=project, major=major,
                              main_directory=main_directory,
                              max_minor_version_description=max_minor_version_description,
                              prepare_build_command=prepare_build_command)


def create_directory(project=create_project(), visible=True, name=""):
    return Directory.objects.create(project=project, visible=visible, name=name)


def create_developer(name="Ana", email="ana@ana.com.br", login="anaana"):
    return Developer.objects.create(name=name, email=email, login=login)


def create_commit(id=1, tag=create_tag(), hash="ASDADADADSADADS", author=create_developer(),
                  committer=create_developer()):
    return Commit.objects.create(id=id, tag=tag, hash=hash, author=author, committer=committer)


# class DeveloperModelTests(TestCase):
#     @classmethod
#     def create_developer(cls, name="Renata B", email="renata@gmail.com"):
#         return Developer(name=name, email=email, login='renatabrasil')
#
#     def test_developer_name(self):
#         dev = self.create_developer()
#         expected_result = "Renata B (login: renatabrasil, email: renata@gmail.com)"
#
#         self.assertEqual(expected_result, dev.__str__())


class ProjectModelTests(TestCase):
    def setUp(self):
        """
        Set up all the tests
        """
        self.project1 = create_project(name="Projeto 1")
        self.project2 = create_project(name="Project 2")

        self.tag = create_tag(description='rel/1.1', previous_tag=None, project=self.project2,
                              main_directory="main/code", major=True)
        self.tag2 = create_tag(description='rel/1.2', previous_tag=self.tag, project=self.project2, major=True)
        self.tag3 = create_tag(description='rel/1.3', previous_tag=self.tag2, project=self.project2, major=True)
        self.tag_minor1 = create_tag(description='rel/1.3.1', previous_tag=self.tag3, project=self.project2,
                                     major=False)

    def tearDown(self):
        self.project1.delete()
        self.project2.delete()
        self.tag.delete()
        self.tag2.delete()
        self.tag3.delete()
        self.tag_minor1.delete()

    # @classmethod
    # def create_project(cls, name="Project 1", path="https://github.com/project_1"):
    #     return Project.objects.create(project_name=name, project_path=path)

    def test_project_name(self):
        proj = create_project()

        self.assertEqual(proj.__str__(), "Projeto")

    # @patch()
    def test_first_tag(self):
        tag = Tag.objects.create(description='rel/1.1', previous_tag=None, project=self.project1)

        self.assertEqual(self.project1.first_tag, tag)


# class TagModelTests(TestCase):
#     def setUp(self):
#         """
#         Set up all the tests
#         """
#         project1 = create_project(name="Project 1")
#         project2 = create_project(name="Project 2")
#
#         tag = create_tag(description='rel/1.1', previous_tag=None, project=project2,
#                          main_directory="main/code", major=True)
#         tag2 = create_tag(description='rel/1.2', previous_tag=tag, project=project2, major=True)
#         tag3 = create_tag(description='rel/1.3', previous_tag=tag2, project=project2, major=True)
#         tag_minor1 = create_tag(description='rel/1.3.1', previous_tag=tag3, project=project2, major=False)
#
#     def test_minors(self):
#         tag_major = create_tag(max_minor_version_description="1.1,1.2,1.2.a,1.3.1")
#
#         result = tag_major.minors
#
#         self.assertListEqual(["1.1", "1.2", "1.2.a", "1.3.1"], result)
#
#     def test_minors_when_minors_are_empty(self):
#         tag_major = create_tag(max_minor_version_description="")
#
#         result = tag_major.minors
#
#         self.assertListEqual([], result)
#
#     def test_line_major_versions(self):
#         self.assertListEqual([1, 2, 3], list(Tag.line_major_versions(1)))
#
#     def test_main_directory_prefix(self):
#         project2 = create_project(name="Project 2")
#         tag = create_tag(description='rel/1.1', id=1, previous_tag=None, project=project2,
#                          main_directory="main/code", major=True)
#
#         self.assertEqual("main/code/", tag.main_directory_prefix)
#
#     def test_pre_build_commands_successfully(self):
#         tag = create_tag(prepare_build_command="ant clean, ant update, ant compile")
#
#         result = tag.pre_build_commands
#
#         self.assertListEqual(["ant clean", "ant update", "ant compile"], result)
#
#     def test__str__(self):
#         project2 = create_project(name="Project 2")
#         tag2 = create_tag(description='rel/1.2', id=2, project=project2, major=True)
#
#         self.assertEqual("Project 2: rel/1.2", tag2.__str__())
#
#
# class DirectoryModelTests(TestCase):
#     def test_directory_name(self):
#         project2 = create_project(name="Project 2")
#         directory = create_directory(project=project2, visible=False, name="core/db/models")
#
#         self.assertEqual(directory.__str__(), "core/db/models - Visible: False")
#
#     def test_belongs_to_component_with_same_path(self):
#         file = "core/db/models/"
#
#         directory = create_directory(visible=True, name="core/db/models/")
#
#         self.assertTrue(directory.belongs_to_component(file))
#
#     def test_file_inside_belongs_to_component(self):
#         file = "core/db/models/create_client.sql"
#
#         directory = create_directory(visible=False, name="core/db/models/")
#
#         self.assertTrue(directory.belongs_to_component(file))
#
#     def test_file_inside_belongs_to_component_and_file_is_a_component(self):
#         file = "core/db/models/"
#
#         directory = create_directory(visible=True, name="core/db/models")
#
#         self.assertFalse(directory.belongs_to_component(file))
#
#
# class CommitModelTests(TestCase):
#     def test__str__(self):
#         author = create_developer(name="Roberto")
#         tag = create_tag(description="1.0")
#         commit = create_commit(hash="ABCD123456", id=15, author=author, tag=tag)
#
#         expectedResult = "15 - hash: ABCD123456 - Author: Roberto - Tag: 1.0"
#         result = commit.__str__()
#
#         self.assertEqual(expectedResult, result)


# def test_calculate_general_experience_successfully(self):
#         with mock.patch('contributions.models.update_commit') as mocked_handler:
#             post_save.connect(mocked_handler, sender=Commit, dispatch_uid='test_cache_mocked_handler')
#
#         au = Mock(Developer)
#         author = mommy.make(Developer)
#         committer = mommy.make(Developer)
#         tag = mommy.make(Tag)
#
#         commit = Commit(author=author, committer=committer, tag=tag)
#
#         commit.save()
#
#         self.assertIsNone(commit)

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

# if __name__ == '__main__':
#     unittest.main()
