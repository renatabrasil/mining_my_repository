import os
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from architecture import helpers


class ArchitectureHelpersTests(SimpleTestCase):
    def test_should_build_path_name_from_parts(self):
        self.assertEqual("src/main/jars", helpers.build_path_name(["src", "main", "jars"]))

    def test_should_get_compiled_directory_name(self):
        file_commit = SimpleNamespace(directory="src/main", name="Component.txt")

        result = helpers.get_compiled_directory_name(file_commit)

        self.assertEqual("src/main/Component/jars", result)

    def test_should_return_false_when_directory_does_not_exist(self):
        self.assertFalse(helpers.has_jar_file("missing-folder"))

    def test_should_return_true_when_directory_has_jar_or_csv_file(self):
        with tempfile.TemporaryDirectory() as folder:
            open(os.path.join(folder, "component.jar"), "w").close()

            self.assertTrue(helpers.has_jar_file(folder))

    def test_should_return_true_when_generating_csv_for_missing_folder(self):
        self.assertTrue(helpers.generate_csv("missing-folder"))

    def test_should_run_arcan_when_folder_has_jar_without_pm_csv(self):
        process = Mock()
        with tempfile.TemporaryDirectory() as folder:
            open(os.path.join(folder, "component.jar"), "w").close()

            with patch("architecture.helpers.subprocess.Popen", return_value=process) as popen:
                with patch("architecture.helpers.CommonsConstantsUtils.ARCAN_CMD_EXECUTE_PREFIX", "arcan", create=True):
                    result = helpers.generate_csv(folder)

        self.assertTrue(result)
        popen.assert_called_once()
        process.wait.assert_called_once()

    def test_should_not_run_arcan_when_pm_csv_already_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            open(os.path.join(folder, "component.jar"), "w").close()
            open(os.path.join(folder, "PM.csv"), "w").close()

            with patch("architecture.helpers.subprocess.Popen") as popen:
                result = helpers.generate_csv(folder)

        self.assertTrue(result)
        popen.assert_not_called()

    def test_should_return_false_when_generate_csv_fails(self):
        with patch("architecture.helpers.os.listdir", side_effect=RuntimeError("boom")):
            self.assertFalse(helpers.generate_csv("."))

    def test_should_delete_not_compiled_version_and_return_sanitized_filename(self):
        current_directory = os.getcwd()
        with tempfile.TemporaryDirectory() as folder:
            os.makedirs(os.path.join(folder, "version-abcdef"), exist_ok=True)

            try:
                result = helpers.delete_not_compiled_version_and_return_filename(
                    "abc/def",
                    folder,
                    "component.jar",
                )
            finally:
                os.chdir(current_directory)

            self.assertEqual("abcdef", result)
            self.assertFalse(os.path.exists(os.path.join(folder, "version-abcdef")))

    def test_should_create_jar_file(self):
        process = Mock()
        with tempfile.TemporaryDirectory() as repository:
            jar_folder = os.path.join(repository, "jars")

            with patch("architecture.helpers.subprocess.Popen", return_value=process) as popen:
                helpers.create_jar_file("build/classes", "component.jar", jar_folder, repository)

            self.assertTrue(os.path.isdir(jar_folder))
            popen.assert_called_once_with(
                "jar -cf component.jar build/classes",
                cwd=repository,
                shell=False,
            )
        process.wait.assert_called_once()

    def test_should_sort_files_by_commit_order(self):
        files = ["commit-10", "commit-2", "commit-1"]

        self.assertEqual(["commit-1", "commit-2", "commit-10"], helpers.sort_files_by_commit_order_asc(files))
