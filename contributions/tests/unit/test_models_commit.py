from enum import Enum

from django.test import TransactionTestCase

# Django
from contributions.models import Commit, Project, Developer, Tag, Modification, Directory


# third-party


class change_type(Enum):
    ADDED = 'ADD'
    DELETED = 'DEL'
    MODIFIED = 'MOD'
    RENAMED = 'REN'


class ModificationModelTests(TransactionTestCase):

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

    def test_should_print_modification_details(self):
        modification = Modification.objects.create(new_path="src/main/apache/domain/Transporte.java",
                                                   directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)

        self.assertEqual("Commit: FIRSTCOMMIT, Path: src/main/apache/domain/Transporte.java",
                         modification.__str__())

    def test_should_return_file_name_in_root_path(self):
        modification = Modification.objects.create(new_path="main2.java", directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)

        self.assertEqual("main2.java", modification.file)

    def test_should_return_file_name_in_complete_path(self):
        modification = Modification.objects.create(new_path="src/main/apache/driver.java",
                                                   directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)

        self.assertEqual("driver.java", modification.file)

    def test_verify_whether_a_modification_has_impact_loc_or_not(self):
        diff = "\n+ public void {\n\n- * @author"
        diff_without_impact__log = "\n+*  public void {\n\n- // @author"

        modification = Modification.objects.create(new_path="src/main/domain/Project.java",
                                                   directory=self.main_directory,
                                                   change_type=change_type.MODIFIED,
                                                   commit=self.first_commit, diff=diff)

        modification_no_impactful_loc = Modification.objects.create(new_path="src/main/domain/Client.java",
                                                                    directory=self.main_directory,
                                                                    change_type=change_type.MODIFIED,
                                                                    commit=self.first_commit,
                                                                    diff=diff_without_impact__log)

        self.assertTrue(modification.has_impact_loc_calculation())
        self.assertFalse(modification_no_impactful_loc.has_impact_loc_calculation())

    def test_should_return_if_a_file_is_a_java_file(self):
        modification = Modification.objects.create(new_path="src/main/apache/controllers/ClientController.java",
                                                   directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)
        modification2 = Modification.objects.create(new_path="docs/README.md", directory=self.main_directory,
                                                    commit=self.first_commit, change_type=change_type.ADDED)

        self.assertTrue(modification.is_java_file)
        self.assertFalse(modification2.is_java_file)

    def test_should_save_modification_and_commit_at_the_same_time(self):
        modification = Modification.objects.create(new_path="src/main/apache/db/ManageDriver.java",
                                                   directory=self.main_directory,
                                                   commit=Commit(hash="NEWCOMMIT", tag=self.tag, author=self.developer2,
                                                                 committer=self.developer2),
                                                   change_type=change_type.ADDED)
        self.assertEqual("Commit: NEWCOMMIT, Path: src/main/apache/db/ManageDriver.java", modification.__str__())

    def test_should_return_modification_name(self):
        modification = Modification.objects.create(new_path="src/main/apache/main.java", directory=self.main_directory,
                                                   commit=self.first_commit, change_type=change_type.ADDED)
        modification2 = Modification.objects.create(new_path="test.java", directory=self.main_directory,
                                                    commit=self.first_commit, change_type=change_type.ADDED)

        expected_responses = {
            'response_modification_1': f'Commit: {modification.commit.hash}, Path: src/main/apache/main.java',
            'response_modification_2': f'Commit: {modification2.commit.hash}, Path: test.java'
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


class CommitModelTests(TransactionTestCase):

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
        self.first_files_in_the_project_1 = Modification.objects.create(new_path="/src/Database.java",
                                                                        diff="\n+ public void {\n\n- private String author",
                                                                        commit=self.commit_with_author_experience,
                                                                        change_type=change_type.ADDED, added=1000,
                                                                        removed=0)
        self.first_files_in_the_project_2 = Modification.objects.create(new_path="/src/main/database/main.java",
                                                                        commit=self.commit_with_author_experience,
                                                                        diff="\n+ public void {\n\n- * @author",
                                                                        change_type=change_type.ADDED, added=10,
                                                                        removed=0)
        self.refactor_file = Modification.objects.create(new_path="/src/main", change_type=change_type.MODIFIED,
                                                         commit=self.commit_with_author_experience, added=50,
                                                         removed=12)

    # @skip
    def test_should_return_commit_description__str__(self):
        commit = Commit.objects.create(hash="ABCD123456", id=99, author=self.developer1, tag=self.tag,
                                       committer=self.developer2)

        expected_result = "99 - hash: ABCD123456 - Author: Daniel Palacios - Tag: rel/1.1"
        result = commit.__str__()

        self.assertEqual(expected_result, result)

    def test_should_calculate_general_experience_successfully(self):
        # Given
        # Author 1:
        # cloc_activity previous commit = 120
        commit = Commit(author=self.developer2, committer=self.developer2, tag=self.tag, hash="AAASSDDD")
        Modification.objects.create(new_path="/src/main/addoc", change_type=change_type.MODIFIED,
                                    commit=commit, added=540,
                                    removed=20)
        # When
        commit.save()

        # Then
        self.assertAlmostEqual(2.8, commit.author_experience, 1)
        self.assertEqual(3, commit.total_commits)

    def test_should_clean_commit_metrics(self):
        commit = Commit.objects.create(hash="METRICS", author=self.developer2, committer=self.developer2,
                                       tag=self.tag, compilable=True, mean_rmd_components=10.0,
                                       std_rmd_components=2.0, delta_rmd_components=3.0,
                                       normalized_delta=0.5)

        commit.clean_metrics()

        self.assertFalse(commit.compilable)
        self.assertEqual(0.0, commit.mean_rmd_components)
        self.assertEqual(0.0, commit.std_rmd_components)
        self.assertEqual(0.0, commit.delta_rmd_components)
        self.assertEqual(0.0, commit.normalized_delta)

    def test_should_update_compilable_status(self):
        commit = Commit.objects.create(hash="COMPILABLE", author=self.developer2, committer=self.developer2,
                                       tag=self.tag, compilable=False)

        commit.set_compilable(True)

        self.assertTrue(commit.compilable)

    def test_should_identify_newcomer_author_by_seniority(self):
        newcomer_commit = Commit(author=self.developer2, committer=self.developer2, tag=self.tag,
                                  author_seniority=365)
        experienced_commit = Commit(author=self.developer2, committer=self.developer2, tag=self.tag,
                                    author_seniority=366)

        self.assertTrue(newcomer_commit.is_author_newcomer)
        self.assertFalse(experienced_commit.is_author_newcomer)

    def test_should_identify_newcomer_author_when_commit_has_submitted_by(self):
        commit = Commit(author=self.developer2, committer=self.developer2, tag=self.tag,
                        author_seniority=1000, has_submitted_by=True)

        self.assertTrue(commit.is_author_newcomer)

    def test_should_return_existing_parent_commits_from_parent_hashes(self):
        parent = Commit.objects.create(hash="PARENT", author=self.developer2, committer=self.developer2,
                                       tag=self.tag)
        child = Commit.objects.create(hash="CHILD", parents_str="PARENT,UNKNOWN", author=self.developer2,
                                      committer=self.developer2, tag=self.tag)

        self.assertListEqual([parent], child.parents)

    def test_should_link_parent_to_child_after_child_commit_is_saved(self):
        parent = Commit.objects.create(hash="SIGNAL_PARENT", author=self.developer2, committer=self.developer2,
                                       tag=self.tag)
        child = Commit.objects.create(hash="SIGNAL_CHILD", parents_str="SIGNAL_PARENT", author=self.developer2,
                                      committer=self.developer2, tag=self.tag)

        parent.refresh_from_db()

        self.assertEqual(child, parent.children_commit)
