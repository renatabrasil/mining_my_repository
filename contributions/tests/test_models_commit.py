from enum import Enum

from django.test import TestCase

# Django
from contributions.models import Commit, Project, Developer, Tag, Modification, Directory


# third-party


class change_type(Enum):
    ADDED = 'ADD'
    DELETED = 'DEL'
    MODIFIED = 'MOD'
    RENAMED = 'REN'


class ModificationModelTests(TestCase):

    def setUp(self):
        """
        Set up all the tests
        """
        self.project2 = Project.objects.create(project_name="Project 2")

        self.developer1 = Developer.objects.create(name="Daniel Palacios", email="danpalacios@msn.com",
                                                   login="danpalacios")
        self.developer2 = Developer.objects.create(name="Roberto", email="roberto@brasil.com.br", login="beto2021")

        self.main_directory = Directory.objects.create(project=self.project2, visible=True, name="src/java")

        self.tag = Tag.objects.create(description='rel/1.1', previous_tag=None, project=self.project2,
                                      main_directory="main/code", major=True)

        self.first_commit = Commit.objects.create(hash="FIRSTCOMMIT", author=self.developer2, committer=self.developer2,
                                                  tag=self.tag)

    def tearDown(self):
        self.first_commit.delete()
        self.tag.delete()
        self.main_directory.delete()
        self.developer2.delete()
        self.developer1.delete()
        self.project2.delete()

    def test_should_return_file_name_in_root_path(self):
        modification = Modification.objects.create(new_path="main.java", directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)

        self.assertEqual("main.java", modification.file)

    def test_should_return_file_name_in_complete_path(self):
        modification = Modification.objects.create(new_path="src/main/apache/main.java", directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)

        self.assertEqual("main.java", modification.file)

    def test_verify_whether_a_modification_has_impact_loc_or_not(self):
        diff = "\n+ public void {\n\n- * @author"

        modification = Modification.objects.create(new_path="src/main/apache/main.java", directory=self.main_directory,
                                                   change_type=change_type.MODIFIED,
                                                   commit=self.first_commit, diff=diff)

    def test_should_return_if_a_file_is_a_java_file(self):
        modification = Modification.objects.create(new_path="src/main/apache/main.java", directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)
        modification2 = Modification.objects.create(new_path="docs/README.md", directory=self.main_directory,
                                                    commit=self.first_commit, change_type=change_type.ADDED)

        self.assertTrue(modification.is_java_file)
        self.assertFalse(modification2.is_java_file)

    def test_should_return_modification_name(self):
        modification = Modification.objects.create(new_path="src/main/apache/main.java", directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)
        modification2 = Modification.objects.create(new_path="test.java", directory=self.main_directory,
                                                    commit=self.first_commit, change_type=change_type.ADDED)

        expected_responses = {
            'response_modification_1': f'Commit: {modification.commit.hash} - Directory: src/main/apache - File name: main.java',
            'response_modification_2': f'Commit: {modification2.commit.hash} - Directory: / - File name: test.java'
        }

        self.assertEqual(expected_responses['response_modification_1'], modification.__str__())
        self.assertEqual(expected_responses['response_modification_2'], modification2.__str__())

    def test_should_return_diff_text(self):
        diff = "\n+ public void {\n\n- * @author"

        modification = Modification.objects.create(new_path="src/main/apache/main.java", directory=self.main_directory,
                                                   change_type=change_type.MODIFIED,
                                                   commit=self.first_commit, diff=diff)
        expected_response = {
            'lines_added': '\n0 lines added: \n\n2 +  public void {',
            'lines_removed': '\n0 lines removed:  \n\n3 -  * @author'
        }

        self.assertEqual(expected_response['lines_added'], modification.diff_added)
        self.assertEqual(expected_response['lines_removed'], modification.diff_removed)


class CommitModelTests(TestCase):

    @classmethod
    def create_commit(cls, tag=None, hash="ASDADADADSADADS", author=None,
                      committer=None):
        return Commit.objects.create(id=id, tag=tag, hash=hash, author=author, committer=committer)

    def setUp(self):
        """
        Set up all the tests
        """
        self.project1 = Project.objects.create(project_name="Project 1")
        self.project2 = Project.objects.create(project_name="Project 2")

        self.developer1 = Developer.objects.create(name="Daniel Palacios", email="danpalacios@msn.com",
                                                   login="danpalacios")
        self.developer2 = Developer.objects.create(name="Roberto", email="roberto@brasil.com.br", login="beto2021")

        self.tag = Tag.objects.create(description='rel/1.1', previous_tag=None, project=self.project2,
                                      main_directory="main/code", major=True)

        self.first_commit = Commit.objects.create(hash="FIRSTCOMMIT", author=self.developer2, committer=self.developer2,
                                                  tag=self.tag)
        self.commit_with_author_experience = Commit.objects.create(hash="COMMITWITHXP", author=self.developer2,
                                                                   committer=self.developer2,
                                                                   previous_impactful_commit=self.first_commit,
                                                                   tag=self.tag)

        self.first_files_in_the_project_1 = Modification.objects.create(new_path="/src", commit=self.first_commit,
                                                                        change_type=change_type.ADDED, added=1000,
                                                                        removed=0)
        self.first_files_in_the_project_2 = Modification.objects.create(new_path="/src/main/database",
                                                                        commit=self.first_commit,
                                                                        change_type=change_type.ADDED, added=10,
                                                                        removed=0)
        self.refactor_file = Modification.objects.create(new_path="/src/main", change_type=change_type.MODIFIED,
                                                         commit=self.commit_with_author_experience, added=50,
                                                         removed=12)

    def test_should_return_commit_description__str__(self):
        commit = Commit.objects.create(hash="ABCD123456", id=15, author=self.developer1, tag=self.tag,
                                       committer=self.developer2)

        expected_result = "15 - hash: ABCD123456 - Author: Daniel Palacios - Tag: rel/1.1"
        result = commit.__str__()

        self.assertEqual(expected_result, result)

    def test_should_calculate_general_experience_successfully(self):
        commit = Commit(author=self.developer1, committer=self.developer2, tag=self.tag, hash="AAASSDDD")
        refactor_file = Modification.objects.create(new_path="/src/main/addoc", change_type=change_type.MODIFIED,
                                                    commit=commit, added=540,
                                                    removed=20)

        # commit.save()

        self.assertIsNotNone(commit)
