import os
import shutil
import subprocess

from architecture.constants import ConstantsUtils
from architecture.models import FileCommits
from common.constants import ExtensionsFile, ConstantsUtils


def get_compiled_directory_name(file: FileCommits) -> str:
    return build_path_name(
        [file.directory, file.name.replace(ExtensionsFile.TXT, ""), 'jars'])  # With no separator in the beginning


def build_path_name(path: list[str]) -> str:
    """
        Returns relative path in str

        param: list of folders in order
    """
    build_path = ''
    for name in path:
        build_path += ConstantsUtils.PATH_SEPARATOR + name
    return build_path.replace(ConstantsUtils.PATH_SEPARATOR, '', 1)


def has_jar_file(directory: str) -> bool:
    exists = False
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if exists:
                break
            if filename.endswith(ExtensionsFile.JAR) or filename.endswith(ExtensionsFile.CSV):
                exists = True
    return exists


def generate_csv(folder: str) -> bool:
    try:
        if not os.path.exists(folder):
            return True
        for filename in os.listdir(folder):
            if "PM.csv" not in os.listdir(folder) and filename.endswith(ExtensionsFile.JAR):
                arcan_metrics = subprocess.Popen(ConstantsUtils.ARCAN_CMD_EXECUTE_PREFIX +
                                                 ' -p ' + '"' + folder + '"' + ' -out ' + '"' + folder + '"' + ' -pm -folderOfJars',
                                                 shell=False,
                                                 cwd=os.getcwd())
                arcan_metrics.wait()

        return True
    except Exception as er:
        print(er)
        return False


def delete_not_compiled_version(commit: str, compiled_directory: str,
                                current_project_path: str, jar_filename: str) -> list[str]:
    commits_with_errors = []

    os.chdir(current_project_path + ConstantsUtils.PATH_SEPARATOR + compiled_directory)

    folder = 'version-' + commit.replace(ConstantsUtils.PATH_SEPARATOR, "").replace(".", "-")
    commits_with_errors.append(commit.replace(ConstantsUtils.PATH_SEPARATOR, "").replace(".", "-"))

    shutil.rmtree(folder, ignore_errors=True)

    print("BUILD FAILED or Jar creation failed\n")
    print(jar_filename + " DELETED\n")

    return commits_with_errors


def create_jar_file(build_path, jar_file, jar_folder, local_repository):
    os.makedirs(jar_folder, exist_ok=True)
    input_files = f'"{local_repository}/{build_path}"'
    self.logger.info(f'comando: jar -cf {jar_file} {input_files}')
    process = subprocess.Popen(f'jar -cf {jar_file} {build_path}', cwd=local_repository,
                               shell=False)
    process.wait()
