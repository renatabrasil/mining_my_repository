import os
import shutil

from django import test

from architecture.helpers import build_path_name, has_jar_file


class HelperTest(test.TestCase):
    def __setup_directory(self, name, csv_creation: bool = False, jar_file: bool = True, any_ext: bool = False):
        os.makedirs(f'test/{name}', exist_ok=True)

        if csv_creation:
            open(f'test/{name}/file.csv', mode='a').close()
        if jar_file:
            open(f'test/{name}/file.jar', mode='a').close()
        if any_ext:
            open(f'test/{name}/file.txt', mode='a').close()

    def tearDown(self):
        shutil.rmtree('test', ignore_errors=True)

    def test_verify_build_path_name(self):
        # Given
        paths = ["src", "java", "controllers"]
        paths_with_one_directory = ["test"]

        # When
        result = build_path_name(path=paths)
        result_with_one_directory = build_path_name(path=paths_with_one_directory)

        # Then
        self.assertEqual("src/java/controllers", result)
        self.assertEqual("test", result_with_one_directory)

    def test_verify_has_jar_file_only_jar_file_is_present(self):
        self.__setup_directory('bulba')

        result = has_jar_file('test/bulba')

        self.assertTrue(result)

    def test_verify_has_jar_file_only_csv_file_is_present(self):
        self.__setup_directory('bulba', csv_creation=True, jar_file=False, any_ext=False)

        result = has_jar_file('test/bulba')

        self.assertTrue(result)

    def test_verify_has_jar_file_directory_with_any_type_extension(self):
        self.__setup_directory('bulba', any_ext=True)

        result = has_jar_file('test/bulba')

        self.assertTrue(result)

    def test_verify_has_jar_file_when_there_is_no_jar_file(self):
        self.__setup_directory('bulba', jar_file=False, any_ext=False, csv_creation=False)

        result = has_jar_file('test/bulba')

        self.assertFalse(result)

    def test_verify_has_jar_file_when_there_is_no_directory(self):
        result = has_jar_file('test/bulba')

        self.assertFalse(result)
