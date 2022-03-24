import os
import shutil
from subprocess import Popen
from unittest.mock import patch, Mock

from django import test

from architecture.constants import ConstantsUtils
from architecture.helpers import build_path_name, has_jar_file, sort_files_by_commit_order_asc, \
    get_compiled_directory_name, create_jar_file, generate_csv, delete_not_compiled_version_and_return_filename
from architecture.models import FileCommits


class HelperTest(test.TestCase):
    def __create_jar(self, file_jar: str, local_repository: str, file_folder: str):
        os.makedirs(f'{file_folder}', exist_ok=True)

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

    def test_verify_sort_files_by_commit_order_asc(self):
        # Given
        files = ["version-110-aaa", "version-22-dfdfd", "version-1-bce"]

        # When
        result = sort_files_by_commit_order_asc(files=files)

        # Then
        self.assertEqual(["version-1-bce", "version-22-dfdfd", "version-110-aaa"], result)

    def test_verify_sort_files_by_commit_order_asc_returns_empty_file(self):
        # Given
        files = []

        # When
        result = sort_files_by_commit_order_asc(files=files)

        # Then
        self.assertEqual([], result)

    def test_verify_get_compiled_directory_name(self):
        # Given
        file = FileCommits(name="commit-1.txt", directory='compiled/ant')

        # When
        result = get_compiled_directory_name(file=file)

        # Then
        self.assertEqual('compiled/ant/commit-1/jars', result)

    @patch('subprocess.Popen', return_value=Mock(spec=Popen))
    def test_should_create_jar_file(self, mock_subprocess):
        # Given
        build_path = 'test/build'
        jar_file = 'commit-1.jar'
        jar_folder = 'test/jars'
        local_repository = 'test/project'

        mock_subprocess.wait.side_effect = None

        # When
        create_jar_file(jar_file=jar_file, build_path=build_path, jar_folder=jar_folder,
                        local_repository=local_repository)

        # Then
        mock_subprocess.assert_called_with(f'jar -cf {jar_file} {build_path}', cwd=local_repository, shell=False)
        mock_subprocess.wait.assert_called

    def test_should_do_not_generate_csv_when_folder_doesnt_exist(self):
        self.assertTrue(generate_csv(folder='test'))

    def test_should_do_not_generate_csv_when_csv_already_exists(self):
        self.__setup_directory('bulba')
        self.assertTrue(generate_csv(folder='test'))

    @patch('subprocess.Popen', return_value=Mock(spec=Popen))
    def test_should_generate_csv(self, mock_popen):
        # Given
        mock_popen.wait.side_effect = None
        self.__setup_directory(name='bulba', csv_creation=False, jar_file=True)

        # When and Then
        self.assertTrue(generate_csv(folder='test/bulba'))
        mock_popen.assert_called_with(
            ConstantsUtils.ARCAN_CMD_EXECUTE_PREFIX + ' -p "test/bulba" -out "test/bulba" -pm -folderOfJars',
            shell=False,
            cwd=os.getcwd())
        mock_popen.wait.assert_called

    @patch('subprocess.Popen', return_value=Mock(spec=Popen))
    def test_should_not_generate_csv_when_occurs_an_exception(self, mock_popen):
        # Given
        mock_popen.side_effect = Exception("Qualquer uma")
        self.__setup_directory(name='bulba', csv_creation=False, jar_file=True)

        # When and Then
        self.assertFalse(generate_csv(folder='test/bulba'))
        mock_popen.assert_called_with(
            ConstantsUtils.ARCAN_CMD_EXECUTE_PREFIX + ' -p "test/bulba" -out "test/bulba" -pm -folderOfJars',
            shell=False,
            cwd=os.getcwd())
        mock_popen.wait.assert_called

    # TODO: TO REVIEW
    @patch('shutil.rmtree', side_effect=None)
    def test_delete_not_compiled_version_and_return_filename(self, mock_popen):
        # Given
        self.__setup_directory(name='compiled/ant/build',
                               csv_creation=False, jar_file=True)
        expected_result = "bce31805e9b4b1360d50be8e001886d58e087e38"

        # When
        result = delete_not_compiled_version_and_return_filename(
            commit="bce31805e9b4b1360d50be8e001886d58e087e38",
            directory="test/compiled/ant/build",
            jar_filename="version-bce31805e9b4b1360d50be8e001886d58e087e38.jar")

        self.assertEqual(expected_result, result)
        mock_popen.assert_called_with("version-bce31805e9b4b1360d50be8e001886d58e087e38", ignore_errors=True)
