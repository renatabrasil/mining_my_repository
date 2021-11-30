# standard library
# Django

# third-party
from django.test import TestCase

# local Django
from contributions.models import Project, Tag, Developer, Directory


class DeveloperModelTests(TestCase):
    @classmethod
    def create_developer(cls, name="Renata B", email="renata@gmail.com"):
        return Developer.objects.create(name=name, email=email, login='renatabrasil')

    def test_should_return_developer_name(self):
        dev = self.create_developer()
        expected_result = "Renata B (login: renatabrasil, email: renata@gmail.com)"

        self.assertEqual(expected_result, dev.__str__())


class ProjectModelTests(TestCase):

    @classmethod
    def create_project(cls, name="Projeto"):
        return Project.objects.create(project_name=name)

    def setUp(self):
        # """
        # Set up all the tests
        # """

        self.project1 = Project.objects.create(project_name="Projeto 1")
        self.project2 = self.create_project(name="Project 2")

    def test_should_return_project_name(self):
        # pass
        proj = self.create_project()

        self.assertEqual(proj.__str__(), "Projeto")

    def test_should_return_first_tag(self):
        tag = Tag.objects.create(description='rel/1.1', previous_tag=None, project=self.project1)

        self.assertEqual(self.project1.first_tag, tag)


class TagModelTests(TestCase):

    @classmethod
    def create_tag(cls, description='rel/1.1', previous_tag=None, project=None,
                   major=True,
                   main_directory="main/code", max_minor_version_description="", prepare_build_command=""):
        return Tag.objects.create(description=description, previous_tag=previous_tag, project=project, major=major,
                                  main_directory=main_directory,
                                  max_minor_version_description=max_minor_version_description,
                                  prepare_build_command=prepare_build_command)

    def setUp(self):
        """
        Set up all the tests
        """
        self.project1 = ProjectModelTests.create_project(name="Project 1")
        self.project2 = ProjectModelTests.create_project(name="Project 2")

        tag = self.create_tag(description='rel/1.1', previous_tag=None, project=self.project2,
                              main_directory="main/code", major=True)
        tag2 = self.create_tag(description='rel/1.2', previous_tag=tag, project=self.project2, major=True)
        tag3 = self.create_tag(description='rel/1.3', previous_tag=tag2, project=self.project2, major=True)
        self.tag_minor1 = self.create_tag(description='rel/1.3.1', previous_tag=tag3, project=self.project2,
                                          major=False)

    def test_should_return_minors(self):
        tag_major = self.create_tag(max_minor_version_description="1.1,1.2,1.2.a,1.3.1", project=self.project1)

        result = tag_major.minors

        self.assertListEqual(["1.1", "1.2", "1.2.a", "1.3.1"], result)

    def test_should_return_empty_array_when_minors_are_empty(self):
        tag_major = self.create_tag(max_minor_version_description="", project=self.project1)

        result = tag_major.minors

        self.assertListEqual([], result)

    def test_should_return_major_versions_of_a_project(self):
        self.assertListEqual([1, 2, 3], list(Tag.line_major_versions(self.project2.id)))

    def test_should_return_main_directory_prefix(self):
        tag = self.create_tag(description='rel/1.1', previous_tag=None, project=self.project2,
                              main_directory="main/code", major=True)

        self.assertEqual("main/code/", tag.main_directory_prefix)

    def test_should_return_pre_build_commands_successfully(self):
        tag = self.create_tag(prepare_build_command="ant clean, ant update, ant compile", project=self.project1)

        result = tag.pre_build_commands

        self.assertListEqual(["ant clean", "ant update", "ant compile"], result)

    def test__str__(self):
        tag2 = self.create_tag(description='rel/1.2', project=self.project2, major=True)

        self.assertEqual("Project 2: rel/1.2", tag2.__str__())


class DirectoryModelTests(TestCase):

    @classmethod
    def create_directory(cls, project=None, visible=True, name=""):
        return Directory.objects.create(project=project, visible=visible, name=name)

    def setUp(self):
        """
        Set up all the tests
        """
        self.project1 = ProjectModelTests.create_project(name="Project 1")
        self.project2 = ProjectModelTests.create_project(name="Project 2")

    def test_should_return_directory_name(self):
        directory = self.create_directory(project=self.project2, visible=False, name="core/db/models")

        self.assertEqual(directory.__str__(), "core/db/models - Visible: False")

    def test_should_check_if_directory_belongs_to_component_with_same_path(self):
        file = "core/db/models/"

        directory = self.create_directory(project=self.project1, visible=True, name="core/db/models/")

        self.assertTrue(directory.belongs_to_component(file))

    def test_should_check_if_a_file_inside_this_directory_belongs_to_component(self):
        file = "core/db/models/create_client.sql"

        directory = self.create_directory(project=self.project1, visible=False, name="core/db/models/")

        self.assertTrue(directory.belongs_to_component(file))

    def test_should_check_if_a_file_inside_this_directory_belongs_to_component_and_this_file_is_a_component(self):
        file = "core/db/models/"

        directory = self.create_directory(project=self.project1, visible=True, name="core/db/models")

        self.assertFalse(directory.belongs_to_component(file))
