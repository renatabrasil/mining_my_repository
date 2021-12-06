# standard library

# Django

# third-party

from django.http import request
from django.test import TestCase
from pydriller.domain.commit import ModificationType

from common.utils import CommitUtils, ViewUtils
# local Django
from contributions.models import Modification, Project, Tag, Commit, Developer


class CommitUtilsTests(TestCase):
    def setUp(self):
        """
        Set up all the tests
        """

    def test_get_email_successfully(self):
        #  Given
        input = "john doe dash 2 at gmail dot com"
        input2 = "john doe minus 2 at gmail dot com"
        expected_result = "johndoe-2@gmail.com"

        # When
        result = CommitUtils.get_email(input)

        # Then
        self.assertEquals(expected_result, result)

        result = CommitUtils.get_email(input2)
        self.assertEquals(expected_result, result)

    def test_true_path_when_is_modification_when_path_are_different(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit(hash="TEST", author=Developer(name="Franco"), committer=Developer(name="Roberto"),
                        tag=tag)
        modification = Modification.objects.create(old_path="src\java\org\\apache\lucene\store\RAMDirectory.java",
                                                   new_path="src\java\org\\apache\lucene\store\\NovoRAMDirectory.java",
                                                   change_type=ModificationType.MODIFY, commit=commit)
        expected_result = "src/java/org/apache/lucene/store/NovoRAMDirectory.java"

        # When
        result = CommitUtils.true_path(modification)

        # Then
        self.assertEquals(expected_result, result)

    def test_true_path_when_is_modification_when_path_are_the_same(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit(hash="TEST", author=Developer(name="Franco"), committer=Developer(name="Roberto"),
                        tag=tag)

        modification = Modification.objects.create(old_path="src\java\org\\apache\lucene\store\RAMDirectory.java",
                                                   new_path="src\java\org\\apache\lucene\store\\RAMDirectory.java",
                                                   change_type=ModificationType.MODIFY, commit=commit)
        expected_result = "src/java/org/apache/lucene/store/RAMDirectory.java"

        # When
        result = CommitUtils.true_path(modification)

        # Then
        self.assertEquals(expected_result, result)

    def test_true_path_modification_when_change_type_is_deleted(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit(hash="TEST", author=Developer(name="Franco"), committer=Developer(name="Roberto"),
                        tag=tag)

        modification = Modification.objects.create(old_path="src\java\org\\apache\lucene\store\RAMDirectory.java",
                                                   new_path=None,
                                                   change_type=ModificationType.DELETE, commit=commit)
        expected_result = "src/java/org/apache/lucene/store/RAMDirectory.java"
        # When
        result = CommitUtils.true_path(modification)

        # Then
        self.assertEquals(expected_result, result)

    def test_true_path_modification_when_change_type_is_added(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit(hash="TEST", author=Developer(name="Franco"), committer=Developer(name="Roberto"),
                        tag=tag)

        modification = Modification.objects.create(old_path=None,
                                                   new_path="src\java\org\\apache\lucene\store\RAMDirectory.java",
                                                   change_type=ModificationType.ADD, commit=commit)
        expected_result = "src/java/org/apache/lucene/store/RAMDirectory.java"

        # When
        result = CommitUtils.true_path(modification)

        # Then
        self.assertEquals(expected_result, result)

    def test_true_path_modification_and_return_empty_string_when_no_path_is_given(self):
        # Given
        project = Project.objects.create(project_name="ANT")
        tag = Tag.objects.create(description="v1.0", project=project)

        commit = Commit(hash="TEST", author=Developer(name="Franco"), committer=Developer(name="Roberto"),
                        tag=tag)

        modification = Modification.objects.create(old_path=None,
                                                   new_path=None,
                                                   change_type=ModificationType.ADD, commit=commit)

        # When
        result = CommitUtils.true_path(modification)

        # Then
        self.assertTrue(len(result) == 0)

    def test_strip_accents(self):
        # Given
        input_text = "Eugênia~~´´´´ Márcia Müller"
        expected_result = "Eugenia~~ Marcia Muller"

        # When
        result = CommitUtils.strip_accents(input_text)

        # Then
        self.assertEquals(expected_result, result)

    def test_directory_to_str_of_a_file_in_directory_with_subdirectories(self):
        # Given
        file_path = "/main/spring/processors/payments.java"
        expected_result = "/main/spring/processors"
        # When
        result = CommitUtils.extract_directory_name_from_full_file_name(file_path)
        # Then
        self.assertEquals(expected_result, result)

    def test_directory_to_str_of_a_file_in_root_directory(self):
        # Given
        file_path = "payments.java"
        expected_result = "/"
        # When
        result = CommitUtils.extract_directory_name_from_full_file_name(file_path)
        # Then
        self.assertEquals(expected_result, result)

    def test_is_java_file_true(self):
        # Given
        file_path = "/main/options/main.java"
        # When
        result = CommitUtils.is_java_file(file_path)
        # Then
        self.assertTrue(result)

    def test_is_java_file_false(self):
        # Given
        file_path = "/main/options/main.txt"
        # When
        result = CommitUtils.is_java_file(file_path)
        # Then
        self.assertFalse(result)

    def test_is_java_file_false_when_given_path_is_none(self):
        # Given
        file_path = None
        # When
        result = CommitUtils.is_java_file(file_path)
        # Then
        self.assertFalse(result)


###### ViewUtils tests

class ViewUtilsTests(TestCase):
    # @mock.patch('Project.objects.all().first()', return_value=None)
    def test_current_project_successfully(self):
        project1 = Project.objects.create(project_name="teste")

        result = ViewUtils.get_current_project(request)

        self.assertIsNotNone(result)
        self.assertEquals(project1, result)

    # def test_current_project_and_throws_exception_if_there_is_no_project(self):
    #     Project.objects.all().delete()
    #     # self.assertRaises(Exception,ViewUtils.get_current_project(request) )
    #     self.assertRaises(Exception, ViewUtils.get_current_project, 'request')
    #     # with self.assertRaises(Exception):
    #     #     thing = ViewUtils.get_current_project(request)

    # FIXME
    # class RequestMock(RequestFactory):
    #     def request(self, **request):
    #         "Construct a generic request object."
    #         request = RequestFactory.request(self, **request)
    #         handler = BaseHandler()
    #         handler.load_middleware()
    #         for middleware_method in handler._request_middleware:
    #             if middleware_method(request):
    #                 raise Exception("Couldn't create request mock object - "
    #                                 "request middleware returned a response")
    #         return request
    #
    # def mocked_requests_get(self):
    #     return None
    # # @patch.object(Session, 'get')
    # # @mock.patch("request.POST.get('tag')", return_value=None)
    # @mock.patch('requests.get', return_value=None)
    # # @mock.patch("request.session['tag']", side_effect=Exception("test error"))
    # def test_load_tag_throws_exception(self):
    #     # mock.assert_called_with(1)
