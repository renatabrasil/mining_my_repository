import logging
import os

from django.core.files import File
from django.shortcuts import get_object_or_404
from injector import inject

from architecture.forms import FilesCompiledForm
from architecture.models import FileCommits
from contributions.models import Project
from contributions.repositories.commit_repository import CommitRepository


class ArchitectureService:
    @inject
    def __init__(self, form: FilesCompiledForm, commit_repository: CommitRepository):
        self.form = form
        self.commit_repository = commit_repository
        self.logger = logging.getLogger(__name__)

    def create_files(self, project_id):
        project = get_object_or_404(Project, pk=project_id)
        files = self.generate_list_of_compiled_commits(project)
        return files

    def generate_list_of_compiled_commits(self, project):
        '''
        Generate list of commits that will be compiled
        :param project: current project selected
        :param form: data from form
        '''
        # Restricting to commits which has children
        FileCommits.objects.filter(tag__project=project).delete()

        folder = self.form['directory'].subwidgets[0].data['attrs']['value']

        if not folder:
            raise ValueError("Directory is not informed")

        commits = self.commit_repository.find_all_commits_by_project_order_by_id_asc_as_list(project=project)

        if len(commits) == 0:
            raise ValueError("There is no commits loaded")

        first_commit = commits[0]

        files = []

        if not os.path.exists(folder):
            os.mkdir(folder)
        j = first_commit.tag.description
        try:
            j = j.replace("/", "-")
            filename = "commits-" + j + ".txt"
            file = self.update_file_commits(filename)
            file.tag = first_commit.tag
            files.append(file)
            f = open(file.__str__(), 'w')
            my_file = File(f)
            my_file.write(self.form['git_local_repository'].subwidgets[0].data['attrs']['value'] + "\n")
            my_file.write(self.form['build_path'].subwidgets[0].data['attrs']['value'] + "\n")
            i = 1
            for commit in commits:

                commit_tag = commit.tag.description.replace("/", "-")

                if j != commit_tag:
                    my_file.closed
                    f.closed
                    file.save()
                    i = 1
                    j = commit_tag
                    filename = "commits-" + j + ".txt"
                    file = self.update_file_commits(filename)
                    file.tag = commit.tag
                    f = open(file.__str__(), 'w')
                    my_file = File(f)
                    files.append(file)
                    my_file.write(self.form['git_local_repository'].subwidgets[0].data['attrs']['value'] + "\n")
                    my_file.write(self.form['build_path'].subwidgets[0].data['attrs']['value'] + "\n")
                if not commit.has_impact_loc and not commit.children_commit:
                    continue
                my_file.write(str(i) + "-" + commit.hash + "\n")
                i += 1
            my_file.closed
            f.closed
            file.save()

        except Exception as e:
            self.logger.exception(e.args[0])
            raise
        return files

    def update_file_commits(self, filename: str) -> FileCommits:
        file = FileCommits.objects.filter(name=filename)
        if file.count() > 0:
            file = file[0]
            file.name = filename
            file.directory = self.form['directory'].subwidgets[0].data['attrs']['value']
        else:
            file = FileCommits(directory=self.form['directory'].subwidgets[0].data['attrs']['value'], name=filename,
                               build_path=self.form['build_path'].subwidgets[0].data['attrs']['value'],
                               local_repository=self.form['git_local_repository'].subwidgets[0].data['attrs']['value'])

        return file

    # def compile_commits(self, file_id):
    #     '''
    #         Method responsible for create compiled of all commits of interest. Commits are collected in a file that was generated
    #         by 'list_commits()', a method based on all commits considered when feature 'load commit' was chosen by user.
    #         Commits of interest are those whose:
    #         1 - Are java files
    #         2 - Are in master or trunk branch (which were defined as main branch on project model)
    #         3 - Has a parent or child commit (because of delta may be different than 0)
    #         4 - Are in main directory (which were defined on project model)
    #         '''
    #     file = FileCommits.objects.get(pk=file_id)
    #     current_project_path = os.getcwd()
    #     try:
    #         f = open(file.__str__(), 'r')
    #         myfile = File(f)
    #         compiled_directory = f'{file.directory}/{file.name.replace(".txt", "")}/jars'
    #         if not os.path.exists(compiled_directory):
    #             os.makedirs(compiled_directory, exist_ok=True)
    #
    #         i = 0
    #         commit_with_errors = []
    #
    #         error = False
    #         for commit in myfile:
    #             commit = commit.replace('\n', '')
    #             if i == 0:
    #                 local_repository = commit
    #             elif i == 1:
    #                 build_path = commit
    #             else:
    #                 try:
    #                     jar_folder = f'{current_project_path}/{compiled_directory}/version-{commit.replace("/", "").replace(".", "-")}'
    #
    #                     if not __has_jar_file__(jar_folder):
    #                         os.chdir(local_repository)
    #
    #                         # Go to version
    #                         hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-', '')
    #                         object_commit = commit_repository.find_all_commits_by_hash(hash=hash_commit)
    #
    #                         if object_commit.exists():
    #                             object_commit = object_commit[0]
    #                         else:
    #                             continue
    #
    #                         if not object_commit.has_impact_loc:
    #                             continue
    #
    #                         checkout = subprocess.Popen(f'git reset --hard {hash_commit}',
    #                                                     shell=False, cwd=local_repository)
    #                         checkout.wait()
    #
    #                         logger.info(os.environ.get('JAVA_HOME'))
    #                         logger.info(os.environ.get('ANT_HOME'))
    #                         logger.info(os.environ.get('M2_HOME'))
    #
    #                         # Prepare build commands
    #                         for command in file.tag.pre_build_commands:
    #                             rc = os.system(command)
    #                             if rc != 0:
    #                                 print("Error on compile")
    #                                 continue
    #                         # shutil.rmtree('C:/Users/brasi/Documents/ant/build', ignore_errors=True)
    #
    #                         rc = os.system(file.tag.build_command)
    #
    #                         if rc != 0:
    #                             print("Error on compile")
    #                             error = True
    #
    #                         # Create jar
    #                         jar_folder = f'{current_project_path}/{compiled_directory}/version-{commit.replace("/", "").replace(".", "-")}'
    #                         jar_file = f'"{current_project_path}/{compiled_directory}/version-{commit.replace("/", "").replace(".", "-")}/version-{commit.replace("/", "").replace(".", "-")}.jar"'
    #
    #                         os.makedirs(jar_folder, exist_ok=True)
    #
    #                         input_files = f'"{local_repository}/{build_path}"'
    #                         logger.info(f'comando: jar -cf {jar_file} {input_files}')
    #                         process = subprocess.Popen(f'jar -cf {jar_file} {build_path}', cwd=local_repository,
    #                                                    shell=False)
    #                         process.wait()
    #
    #                         # Check whether created jar is valid
    #                         os.chdir(current_project_path)
    #                         jar = jar_file.replace(current_project_path, "").replace("/", "", 1).replace("\"", "")
    #                         # 100 KB
    #
    #                         if os.path.getsize(jar) < 3072000 or error:
    #                             error = False
    #                             # 1.1 76800
    #                             # 1.2 194560
    #                             # 1.3 352256
    #                             # 1.4: 460800
    #                             # 1.7.0 1433600
    #                             # 1.5.0 614400
    #                             # 1.6.0 1126400
    #                             # 1.8.0: 1843200
    #                             # 102400, 184320
    #                             # if os.path.getsize(jar) < 1771200:
    #                             __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory,
    #                                                            current_project_path, jar)
    #
    #                             # os.system('bootstrap.bat')
    #                             # TODO: extract method
    #                             if object_commit is not None:
    #                                 object_commit.compilable = False
    #                                 object_commit.mean_rmd_components = 0.0
    #                                 object_commit.std_rmd_components = 0.0
    #                                 object_commit.delta_rmd_components = 0.0
    #                                 object_commit.normalized_delta = 0.0
    #
    #                             os.chdir(local_repository)
    #                         else:
    #                             error = False
    #
    #                             if not __generate_csv__(jar_folder):
    #                                 __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory,
    #                                                                current_project_path, jar)
    #                                 object_commit.compilable = False
    #                             else:
    #                                 object_commit.compilable = True
    #
    #                             object_commit.save()
    #
    #                         build_path_repository = local_repository + '/' + build_path
    #                         if build_path.count('\\') <= 1 and build_path.count('/') <= 1:
    #                             build_path_repository = local_repository + "/" + build_path
    #                         if os.path.exists(build_path_repository):
    #                             shutil.rmtree(build_path_repository)
    #
    #                 except OSError as e:
    #                     logger.exception(f"Error: {e.filename} - {e.strerror}.")
    #                 except Exception as er:
    #                     logger.exception(er)
    #                     messages.error(request, f'Erro: {er}')
    #                 finally:
    #                     os.chdir(local_repository)
    #
    #             i += 1
    #     except Exception as e:
    #         print(e)
    #         messages.error(request, 'Could not create compiled.')
    #     finally:
    #         os.chdir(current_project_path)
    #         if len(commit_with_errors) > 0:
    #             try:
    #                 f = open(compiled_directory.replace("jars", "") + "log-compilation-errors.txt", 'w+')
    #                 myfile = File(f)
    #                 first = True
    #                 myfile.write(local_repository + "\n")
    #                 myfile.write(build_path + "\n")
    #                 for commit in commit_with_errors:
    #                     if first:
    #                         myfile.write(commit)
    #                         first = False
    #                     else:
    #                         myfile.write("\n" + commit)
    #             except OSError as e:
    #                 print("Error: %s - %s." % (e.filename, e.strerror))
    #             finally:
    #                 f.close()
    #     file.has_compileds = True
    #     file.save()
