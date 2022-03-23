import os
import shutil
import subprocess

from architecture.constants import ConstantsUtils
from architecture.models import FileCommits
from common.constants import ExtensionsFile, CommonsConstants


def get_compiled_directory_name(file: FileCommits) -> str:
    return build_path_name(
        [file.directory, file.name.replace(ExtensionsFile.TXT, ""), 'jars'])


def build_path_name(path: [str]) -> str:
    """
        Returns relative path in str

        param: list of folders in order
    """
    build_path = ''
    for name in path:
        build_path += CommonsConstants.PATH_SEPARATOR + name
    return build_path.replace(CommonsConstants.PATH_SEPARATOR, '', 1)  # With no separator in the beginning


def has_jar_file(directory: str) -> bool:
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.endswith(ExtensionsFile.JAR) or filename.endswith(ExtensionsFile.CSV):
                return True
    return False


def generate_csv(folder: str) -> bool:
    try:
        if not os.path.exists(folder):
            return True
        for filename in os.listdir(folder):
            if "PM.csv" not in os.listdir(folder) and filename.endswith(ExtensionsFile.JAR):
                arcan_metrics = subprocess.Popen(CommonsConstants.ARCAN_CMD_EXECUTE_PREFIX +
                                                 ' -p ' + '"' + folder + '"' + ' -out ' + '"' + folder + '"' + ' -pm -folderOfJars',
                                                 shell=False,
                                                 cwd=os.getcwd())
                arcan_metrics.wait()

        return True
    except Exception as er:
        print(er)
        return False


def delete_not_compiled_version_and_return_filename(commit: str, directory: str, jar_filename: str) -> str:
    os.chdir(directory)

    filename = commit.replace(CommonsConstants.PATH_SEPARATOR, "").replace(".",
                                                                           CommonsConstants.HYPHEN_SEPARATOR)

    folder = 'version-' + filename

    shutil.rmtree(folder, ignore_errors=True)

    print("BUILD FAILED or Jar creation failed\n")
    print(jar_filename + " DELETED\n")

    return filename


def create_jar_file(build_path: str, jar_file: str, jar_folder: str, local_repository: str) -> None:
    os.makedirs(jar_folder, exist_ok=True)

    input_files = f'"{local_repository}/{build_path}"'
    # self.logger.info(f'comando: jar -cf {jar_file} {input_files}')
    process = subprocess.Popen(f'jar -cf {jar_file} {build_path}', cwd=local_repository,
                               shell=False)
    process.wait()


def sort_files_by_commit_order_asc(files: [str]):
    return sorted(files, key=lambda x: int(x.split('-')[1]))


def generate_csv(folder):
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if "PM.csv" not in os.listdir(folder) and filename.endswith(ExtensionsFile.JAR):
                try:
                    arcan_metrics = subprocess.Popen(ConstantsUtils.ARCAN_CMD_EXECUTE_PREFIX +
                                                     ' -p ' + '"' + folder + '"' + ' -out ' + '"' + folder + '"' + ' -pm -folderOfJars',
                                                     shell=False,
                                                     cwd=os.getcwd())
                    arcan_metrics.wait()
                except Exception as er:
                    print(er)
                    return False
            else:
                continue
    return True
