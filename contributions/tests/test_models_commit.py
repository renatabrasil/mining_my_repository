from enum import Enum

# third-party
from django.test import TestCase

from contributions.models import Commit, Project, Developer, Tag, Modification


# Django


class change_type(Enum):
    ADDED = 'ADD'
    DELETED = 'DEL'
    MODIFIED = 'MOD'
    RENAMED = 'REN'


class CommitModelTests(TestCase):

    @classmethod
    def create_commit(tag=None, hash="ASDADADADSADADS", author=None,
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

        expectedResult = "15 - hash: ABCD123456 - Author: Daniel Palacios - Tag: rel/1.1"
        result = commit.__str__()

        self.assertEqual(expectedResult, result)

    def test_should_calculate_general_experience_successfully(self):
        # with mock.patch('contributions.models.update_commit') as mocked_handler:
        #     post_save.connect(mocked_handler, sender=Commit, dispatch_uid='test_cache_mocked_handler')

        commit = Commit(author=self.developer1, committer=self.developer2, tag=self.tag, hash="AAASSDDD")
        refactor_file = Modification.objects.create(new_path="/src/main/addoc", change_type=change_type.MODIFIED,
                                                    commit=commit, added=540,
                                                    removed=20)

        # commit.save()

        self.assertIsNotNone(commit)

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
