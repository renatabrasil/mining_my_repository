from unittest.mock import patch, Mock

from django import test

from contributions.models import Developer
from contributions.repositories.developer_repository import DeveloperRepository


class TestDeveloperRepository(test.TestCase):
    def setUp(self):
        self.__developer_repository = DeveloperRepository()

    @patch('contributions.models.Developer.objects', return_value=Mock())
    def test_find_all_developer_by_login(self, mock_developer):
        # Given
        expected_result = Developer(name="Jeff", login="jeff", email="jeff@gmail.com")
        mock_developer.filter.return_value = [expected_result]

        # When
        result = self.__developer_repository.find_all_developer_by_login("jeff")

        # Then
        self.assertEquals([expected_result], result)
        mock_developer.filter.assert_called_with(login="login")
