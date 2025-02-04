# standard library

# Django
from unittest.mock import patch, Mock

from django.test import TestCase
from django.test.client import RequestFactory
# third-party
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
        input_ = "john doe dash 2 at gmail dot com"
        input2 = "john doe minus 2 at gmail dot com"
        expected_result = "johndoe-2@gmail.com"

        # When
        result = CommitUtils.get_email(input_)

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
        modification = Modification.objects.create(old_path="src\java\org\\apache\lucene\store\RAM2Directory.java",
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
        path = "src\java\org\\apache\lucene\store\RAMDirectory.java"

        modification = Modification.objects.create(old_path=path,
                                                   new_path=path,
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

        modification = Modification.objects.create(old_path="src\java\org\\apache\lucene\store\Database.java",
                                                   new_path=None,
                                                   change_type=ModificationType.DELETE, commit=commit)
        expected_result = "src/java/org/apache/lucene/store/Database.java"
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
    def create_tag(self):
        project = Project.objects.create(project_name="ANT")
        return Tag.objects.create(description="v1.0", project=project)

    @patch("contributions.models.Tag.objects")
    def test_should_load_tag_stored_in_post_request_successfully(self, mock_tag):
        # Given
        mocked_tag = self.create_tag()
        mock_tag.filter.return_value = Mock()
        mock_tag.filter.return_value.first.return_value = mocked_tag

        rf = RequestFactory()
        post_request = rf.post('/submit2/', {'tag': '1'})
        post_request.session = {}

        # When
        result = ViewUtils.load_tag(post_request)

        # Then
        self.assertEqual('1', post_request.session['tag'])
        self.assertEqual(mocked_tag, result)
        mock_tag.assert_called_once

    @patch("contributions.models.Tag.objects")
    def test_should_load_tag_stored_in_session_in_a_request_successfully(self, mock_tag):
        # Given
        mocked_tag = self.create_tag()
        mock_tag.filter.return_value = Mock()
        mock_tag.filter.return_value.first.return_value = mocked_tag

        rf = RequestFactory()
        post_request = rf.post('/submit5/')
        post_request.session = {'tag': '2'}

        # When
        result = ViewUtils.load_tag(post_request)

        # Then
        self.assertEqual('2', post_request.session['tag'])
        self.assertEqual(mocked_tag, result)
        mock_tag.assert_called_once

    @patch("contributions.models.Tag.objects")
    def test_should_return_first_tag_when_calls_load_tag_that_neither_stored_in_session_nor_in_request_successfully(
            self, mock_tag):
        # Given
        mock_tag.filter.return_value = Mock()
        mock_tag.all.return_value.first.return_value = Tag(id=3)

        rf = RequestFactory()
        post_request = rf.post('/submit/')
        post_request.session = {'project': '1'}

        # When
        ViewUtils.load_tag(post_request)

        # Then
        self.assertEqual('3', str(post_request.session['tag']))
        mock_tag.assert_called_once

    @patch("contributions.models.Tag.objects")
    def test_should_return_tag_saved_from_get_request(self, mock_tag):
        # Given
        mock_tag.filter.return_value = Mock()
        mock_tag.filter.return_value.first.return_value.get.return_value = '5'

        rf = RequestFactory()
        get_request = rf.get('/submit/', {'tag': 'rel/1.1'})
        get_request.session = {}

        # When
        ViewUtils.load_tag(get_request)

        # Then
        self.assertEqual('5', str(get_request.session['tag']))
        mock_tag.assert_called_once
