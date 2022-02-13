import logging
import os
import re
import shutil
import subprocess
from collections import OrderedDict

import numpy as np
import pandas as pd
from django.contrib import messages
from django.core.files import File
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from injector import inject

from architecture.forms import FilesCompiledForm
from architecture.helpers import has_jar_file, delete_not_compiled_version_and_return_filename, generate_csv, \
    get_compiled_directory_name, build_path_name, sort_files_by_commit_order_asc
from architecture.models import FileCommits
from common import constants
from common.constants import CommonsConstants
from common.constants import ExtensionsFile
from common.utils import ViewUtils
from contributions.models import Project, ComponentCommit, Commit, Directory, Tag
from contributions.repositories.commit_repository import CommitRepository
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.directory_repository import DirectoryRepository
from contributions.repositories.tag_repository import TagRepository

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


class ArchitectureService:
    @inject
    def __init__(self, form: FilesCompiledForm, commit_repository: CommitRepository,
                 developer_repository: DeveloperRepository, directory_repository: DirectoryRepository,
                 tag_repository: TagRepository):
        self.form = form
        self.commit_repository = commit_repository
        self.developer_repository = developer_repository
        self.directory_repository = directory_repository
        self.tag_repository = tag_repository
        self.__compiled_directory = ''
        self.__local_repository = ''
        self.__build_path = ''

    def create_files(self, request, project_id):
        logger.info(f'[{ArchitectureService.__name__}] - Starting Create files ...')

        project = get_object_or_404(Project, pk=project_id)
        files = self.generate_list_of_compiled_commits(request, project)

        logger.info(f'[{ArchitectureService.__name__}] - Done Create files ...')
        return files

    def generate_list_of_compiled_commits(self, request, project):
        '''
        Generate list of commits that will be compiled
        :param project: current project selected
        :param form: data from form
        '''
        # Restricting to commits which has children
        logger.info(f'[{ArchitectureService.__name__}] - Starting generating list of commits ...')

        FileCommits.objects.filter(tag__project=project).delete()

        folder_form = request.POST.get('directory')
        git_local_directory_form = request.POST.get('git_local_repository')
        build_path_form = request.POST.get('build_path')

        if not folder_form:
            raise ValueError('Directory is not informed')

        commits = self.commit_repository.find_all_commits_by_project_order_by_id_asc_as_list(project=project)

        if len(commits) == 0:
            raise ValueError('There is no commits loaded')

        first_commit = commits[0]

        files = []

        if not os.path.exists(folder_form):
            os.mkdir(folder_form)
        tag_description = first_commit.tag.description
        try:
            tag_description = tag_description.replace(CommonsConstants.PATH_SEPARATOR,
                                                      CommonsConstants.HYPHEN_SEPARATOR)
            filename = 'commits-' + tag_description + ExtensionsFile.TXT

            file = self.update_current_file(filename)

            file.tag = first_commit.tag
            files.append(file)

            f = open(file.__str__(), 'w')
            my_file = File(f)
            my_file.write(git_local_directory_form + CommonsConstants.END_STR)
            my_file.write(build_path_form + CommonsConstants.END_STR)

            i = 1
            for commit in commits:

                commit_tag = commit.tag.description.replace(CommonsConstants.PATH_SEPARATOR,
                                                            CommonsConstants.HYPHEN_SEPARATOR)

                if tag_description != commit_tag:
                    my_file.closed
                    f.closed
                    file.save()

                    i = 1
                    tag_description = commit_tag
                    filename = 'commits-' + tag_description + ExtensionsFile.TXT

                    file = self.update_current_file(filename)
                    file.tag = commit.tag

                    f = open(file.__str__(), 'w')
                    my_file = File(f)

                    files.append(file)
                    my_file.write(git_local_directory_form + CommonsConstants.END_STR)
                    my_file.write(build_path_form + CommonsConstants.END_STR)

                if not commit.has_impact_loc and not commit.children_commit:
                    continue
                my_file.write(
                    str(i) + CommonsConstants.HYPHEN_SEPARATOR + commit.hash + CommonsConstants.END_STR)
                logger.info(f'{str(i) + CommonsConstants.HYPHEN_SEPARATOR + commit.hash} saved')
                i += 1

            my_file.closed
            f.closed
            file.save()

            logger.info(f'[{ArchitectureService.__name__}] - Done generating list of commits ...')
        except Exception as e:
            logger.exception(e.args[0])
            raise
        return files

    def update_current_file(self, filename: str) -> FileCommits:
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

    def compile_commits(self, request, file_id):
        '''
            Method responsible for create compiled of all commits of interest. Commits are collected in a file that was generated
            by 'list_commits()', a method based on all commits considered when feature 'load commit' was chosen by user.
            Commits of interest are those whose:
            1 - There are java files
            2 - There are in master or trunk branch (which were defined as main branch on project model)
            3 - Has a parent or child commit (because of delta may be different than 0)
            4 - There are in main directory (which were defined on project model)
            '''
        file_db = FileCommits.objects.get(pk=file_id)
        current_project_path = os.getcwd().replace('\\', constants.CommonsConstants.PATH_SEPARATOR)
        try:
            file = open(file_db.__str__(), 'r')
            file_system = File(file)

            self.__compiled_directory = get_compiled_directory_name(file_db)

            if not os.path.exists(self.__compiled_directory):
                os.makedirs(self.__compiled_directory, exist_ok=True)

            i = 0
            commits_with_errors = []
            error = False
            for commit in file_system:
                commit = commit.replace(constants.CommonsConstants.END_STR, '')
                if i == 0:
                    self.__local_repository = commit
                elif i == 1:
                    self.__build_path = commit
                else:
                    try:
                        jar_folder = build_path_name(
                            [current_project_path, self.__compiled_directory,
                             f'version-{commit.replace(constants.CommonsConstants.PATH_SEPARATOR, "").replace(".", constants.CommonsConstants.HYPHEN_SEPARATOR)}'])

                        if not has_jar_file(jar_folder):
                            os.chdir(self.__local_repository)

                            # Go to version
                            hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace(
                                constants.CommonsConstants.HYPHEN_SEPARATOR, '')
                            object_commit = self.commit_repository.find_all_commits_by_hash(hash=hash_commit).first()

                            if not object_commit or not object_commit.has_impact_loc:
                                continue

                            self.__checkout_commit(object_commit.hash, self.__local_repository)

                            print(os.environ.get('JAVA_HOME'))
                            print(os.environ.get('ANT_HOME'))
                            print(os.environ.get('M2_HOME'))

                            # Prepare build commands
                            has_error = not object_commit.prepare_build()

                            has_error = not object_commit.build()

                            # Create jar
                            jar_folder = build_path_name([current_project_path, self.__compiled_directory,
                                                          f'version-{object_commit.hash.replace(CommonsConstants.PATH_SEPARATOR, "").replace(".", CommonsConstants.HYPHEN_SEPARATOR)}'])
                            jar_file = build_path_name([jar_folder,
                                                        f'version-{object_commit.hash.replace(CommonsConstants.PATH_SEPARATOR, "").replace(".", CommonsConstants.HYPHEN_SEPARATOR)}{ExtensionsFile.JAR}'])

                            os.makedirs(jar_folder, exist_ok=True)

                            object_commit.compile(jar_name=jar_file, build_path=self.__build_path,
                                                  repository=self.__local_repository)

                            # Check whether created jar is valid
                            os.chdir(current_project_path)
                            jar = jar_file.replace(current_project_path, '').replace(
                                CommonsConstants.PATH_SEPARATOR, '',
                                1).replace('"', '')
                            # 100 KB

                            if os.path.getsize(jar) < 3072000 or has_error:
                                has_error = False
                                # 1.1 76800
                                # 1.2 194560
                                # 1.3 352256
                                # 1.4: 460800
                                # 1.7.0 1433600
                                # 1.5.0 614400
                                # 1.6.0 1126400
                                # 1.8.0: 1843200
                                # 102400, 184320
                                # if os.path.getsize(jar) < 1771200:
                                commits_with_errors.append(delete_not_compiled_version_and_return_filename(commit,
                                                                                                           current_project_path + CommonsConstants.PATH_SEPARATOR + self.__compiled_directory,
                                                                                                           jar))

                                if object_commit:
                                    object_commit.clean_all_commits_metrics()

                                os.chdir(self.__local_repository)
                            else:
                                has_error = False

                                if not generate_csv(jar_folder):
                                    commits_with_errors.append(delete_not_compiled_version_and_return_filename(commit,
                                                                                                               current_project_path + CommonsConstants.PATH_SEPARATOR + self.__compiled_directory,
                                                                                                               jar))
                                    object_commit.set_compilable(status=False)
                                else:
                                    object_commit.set_compilable(status=True)

                                object_commit.save()

                            build_path_repository = self.__local_repository + CommonsConstants.PATH_SEPARATOR + self.__build_path
                            if self.__build_path.count('\\') <= 1 and self.__build_path.count(
                                    CommonsConstants.PATH_SEPARATOR) <= 1:
                                build_path_repository = self.__local_repository + CommonsConstants.PATH_SEPARATOR + self.__build_path
                            if os.path.exists(build_path_repository):
                                shutil.rmtree(build_path_repository)

                    except OSError as e:
                        logger.exception(f'Error: {e.filename} - {e.strerror}.')
                    except Exception as er:
                        logger.exception(er)
                        messages.error(request, f'Erro: {er}')
                    finally:
                        os.chdir(self.__local_repository)

                i += 1
        except Exception as e:
            print(e)
            messages.error(request, 'Could not create compiled.')
        finally:
            os.chdir(current_project_path)
            self.__create_file_with_errors(commits_with_errors)
            file_db.has_compileds = True
            file_db.save()

    def __create_file_with_errors(self, commits_with_errors: []):
        if len(commits_with_errors) > 0:
            try:
                file = open(self.__compiled_directory.replace('jars', '') + 'log-compilation-errors.txt', 'w+')
                file_system = File(file)
                first = True
                file_system.write(self.__local_repository + CommonsConstants.END_STR)
                for commit in commits_with_errors:
                    file_system.write(self.__build_path + CommonsConstants.END_STR)
                    if first:
                        file_system.write(commit)
                        first = False
                    else:
                        file_system.write(CommonsConstants.END_STR + commit)
            except OSError as e:
                logger.exception('Error: %s - %s.' % (e.filename, e.strerror))
            finally:
                file.close()

    def __checkout_commit(self, hash_commit: str, local_repository: str) -> None:
        checkout = subprocess.Popen(f'git reset --hard {hash_commit}',
                                    shell=False, cwd=local_repository)
        checkout.wait()

    def extract_and_calculate_architecture_metrics(self, request, file_id):
        file = FileCommits.objects.get(pk=file_id)

        directory_name = file.__str__().replace(ExtensionsFile.TXT, '')
        directory_name = directory_name + CommonsConstants.PATH_SEPARATOR + 'jars'

        if os.path.exists(directory_name):
            sorted_files = sort_files_by_commit_order_asc(files=os.listdir(directory_name))
            for subdirectory in sorted_files:
                generate_csv(directory_name + CommonsConstants.PATH_SEPARATOR + subdirectory)

        return HttpResponseRedirect(reverse('architecture:index', ))

    def calculate_metrics(self, request, file_id):
        """
        Process metrics calculation request from view
        """
        logger.info(f'[{__name__}] Starting calculate metrics from file_id {file_id}')

        file = FileCommits.objects.get(pk=file_id)

        directory_name = file.__str__().replace(ExtensionsFile.TXT, '')
        metrics_directory = directory_name + CommonsConstants.PATH_SEPARATOR + 'jars'

        if not os.path.exists(metrics_directory):
            os.makedirs(metrics_directory, exist_ok=True)

        self.read_pm_file(metrics_directory, file_id)

        error_file_name = directory_name + CommonsConstants.PATH_SEPARATOR + 'log-compilation-errors' + ExtensionsFile.TXT

        if os.path.exists(error_file_name):
            self.__update_compilable_commits(error_file_name)

        file.metrics_calculated_at = timezone.localtime(timezone.now())
        file.save()

        logger.info(f'[{__name__}] Done calculate metrics from file_id {file_id}')
        return HttpResponseRedirect(reverse('architecture:index', ))

    def calculate_metrics_between_versions(self, request):
        template = loader.get_template('architecture/metrics_between_versions.html')
        tag = ViewUtils.load_tag(request)
        directory = request.POST.get('directory')
        metrics_by_directories = OrderedDict()
        metrics = []
        if directory:
            if os.path.exists(directory):
                files = os.listdir(directory)
                sorted_files = sorted(files, key=lambda x: int(x.split('#')[len(x.split('#')) - 1]))
                for subdirectory in sorted_files:
                    generate_csv(directory + CommonsConstants.PATH_SEPARATOR + subdirectory)
                    version = subdirectory
                    subdirectory = os.path.join(directory, subdirectory)
                    print("\n" + subdirectory + "\n----------------------\n")
                    csv_files = [f for f in os.listdir(subdirectory) if f.endswith(ExtensionsFile.CSV)]
                    for filename in csv_files:
                        try:
                            file = open(os.path.join(subdirectory, filename), "r")
                            content = file.readlines()
                            for line in content[1:]:
                                col = line.split(',')
                                rmd = col[5].replace(CommonsConstants.END_STR, '')
                                package = col[0].replace('.', CommonsConstants.PATH_SEPARATOR)
                                print(line.replace(CommonsConstants.END_STR, ""))

                                if package not in metrics_by_directories:
                                    metrics_by_directories.setdefault(package, {})
                                if version not in metrics_by_directories[package]:
                                    metrics_by_directories[package].setdefault(version, 0.0)
                                metrics_by_directories[package][version] = rmd

                        finally:
                            file.close()

                    components_mean = []
                    dict2 = list(metrics_by_directories.values())
                    for value in dict2:
                        if version in value:
                            components_mean.append(float(value[version]))

                    # ANT
                    name_version = version.replace('rel#', '').replace('-', '', 1).replace('_', '.').replace('#',
                                                                                                             '-')
                    # Lucene
                    name_version = version.replace('_', '.').replace('#', '-')
                    # Cassandra
                    name_version = version.replace('_', '.').replace('#', '-')

                    architectural_quality = np.mean(components_mean)
                    metrics.append([name_version, architectural_quality])

                    # FIXME this is too naive and just work for this project. Should be fix soon.
                    # Ant
                    self.tag_repository.update(Tag, {'delta_rmd_components': architectural_quality})

            my_df_metrics = pd.DataFrame(metrics, columns=['versao', 'D'])
            my_df = pd.DataFrame(metrics_by_directories)
            print(my_df)
            my_df_metrics.to_csv('metrics_by_version.csv', index=True, index_label='idx', header=True)
            my_df.to_csv(directory.replace(CommonsConstants.PATH_SEPARATOR, '_') + ExtensionsFile.CSV, index=True,
                         header=True)
        context = {
            'title': 'Cálculo de qualidade da arquitetura por versões',
            'tag': tag,
        }
        return HttpResponse(template.render(context, request))

    def filter_impactful_commits(self, request, request_params: dict):
        logger.info(f'[{__name__}] Starting to filter metrics with params: [{request_params}]')

        export_csv = request_params.get('export_csv') == 'true'
        full_tag = request_params.get('until_tag')

        directories = self.directory_repository.find_all_visible_directories_by_project_id_order_by_name(
            project_id=request.session['project'])
        developers = self.developer_repository.find_all().order_by('name')
        developers = [d for d in developers if
                      d.commits.exclude(normalized_delta=0).filter(tag__project=request.session['project'])]

        commits = []

        directory_name = ''
        tag_name = ''
        dev_name = ''
        directory_filter = 0
        tag_filter = 0
        developer_filter = 0
        delta_check = ''
        analysis_check = ''

        query = {}

        if request_params.get('directory_id'):
            directory_filter = int(request_params.get('directory_id'))
            if directory_filter > 0:
                query.setdefault('directory_id', directory_filter)
                directory_name = self.directory_repository.find_by_primary_key(pk=directory_filter).name.replace(
                    CommonsConstants.PATH_SEPARATOR, '_')

        if request_params.get('tag_id'):
            tag_filter = int(request_params.get('tag_id'))
            if tag_filter > 0:
                if full_tag:
                    tag_query_str = 'tag_id'
                else:
                    tag_query_str = 'tag_id__lte'
                if directory_filter > 0:
                    query.setdefault('commit__' + tag_query_str, tag_filter)
                else:
                    query.setdefault(tag_query_str, tag_filter)

                query.setdefault('tag__project_id', request.session['project'])
                tag_name = self.tag_repository.find_by_primary_key(pk=tag_filter).description.replace(
                    CommonsConstants.PATH_SEPARATOR, '_')

        if request_params.get('developer_id'):
            developer_filter = int(request_params.get('developer_id'))
            if developer_filter > 0:
                if directory_filter > 0:
                    query.setdefault('commit__author_id', developer_filter)
                else:
                    query.setdefault('author_id', developer_filter)

                dev_name = self.developer_repository.find_by_primary_key(pk=developer_filter).name.replace(' ',
                                                                                                           '_').lower()

        if len(query) > 0:
            if request_params.get('delta_rmd') == 'positive':
                query.setdefault('delta_rmd__gt', 0)
                delta_check = 'positive'
            elif request_params.get('delta_rmd_components') == 'positive':
                query.setdefault('normalized_delta__gt', 0)
                delta_check = 'positive'
            elif request_params.get('delta_rmd_components') == 'negative':
                query.setdefault('normalized_delta__lt', 0)
                delta_check = 'negative'
            elif request_params.get('delta_rmd') == 'negative':
                query.setdefault('delta_rmd__lt', 0) if directory_filter > 0 else query.setdefault(
                    'normalized_delta__lt',
                    0)
                delta_check = 'negative'

            if directory_filter > 0:
                if 'delta_rmd__lt' in query or 'delta_rmd__gt' in query:
                    commits = ComponentCommit.objects.filter(**query)
                else:
                    commits = ComponentCommit.objects.exclude(delta_rmd=0).filter(**query)

                commits = sorted(commits, key=lambda x: x.commit.author_experience, reverse=False)
            else:
                if 'normalized_delta__lt' in query or 'normalized_delta__gt' in query:
                    commits = request.commit_db.filter(**query)
                else:
                    if request_params.get('analysis') == 'geral':
                        analysis_check = 'geral'
                        commits = request.commit_db.filter(**query)
                    else:
                        analysis_check = 'impactful_commits'
                        commits = request.commit_db.exclude(normalized_delta=0).filter(**query)

                commits = sorted(commits, key=lambda x: x.author_experience, reverse=False)

        if export_csv:

            if directory_filter > 0:
                commits = sorted(commits, key=lambda x: x.id, reverse=False)
                metrics_dict = [
                    [x.commit.id, x.commit.author_experience, x.commit.delta_rmd * CommonsConstants.ROUDING_SCALE,
                     x.commit.total_commits,
                     x.commit.author_seniority, x.commit.u_cloc] for x in commits]

                del query['directory_id']
                components = ComponentCommit.no_outliers_objects.exclude(delta_rmd=0).filter(**query).order_by(
                    'id')
                components_metrics = [
                    [x.id, x.author_experience, x.delta_rmd / x.commit.u_cloc * CommonsConstants.ROUDING_SCALE,
                     x.commit.u_cloc] for x in
                    components]

                my_df = pd.DataFrame(components_metrics,
                                     columns=['time', 'experiencia', 'degradacao', 'LOC'])
                my_df.to_csv('component_metrics' + ExtensionsFile.CSV, index=False, header=True)
            else:
                commits = sorted(commits, key=lambda x: x.id, reverse=False)

                name = ''
                if dev_name:
                    name += dev_name + CommonsConstants.HYPHEN_SEPARATOR
                if directory_name:
                    name += directory_name + CommonsConstants.HYPHEN_SEPARATOR
                if tag_name:
                    name += tag_name + CommonsConstants.HYPHEN_SEPARATOR
                if delta_check:
                    name += delta_check
                if name.endswith(CommonsConstants.HYPHEN_SEPARATOR):
                    name = name[:-1]
                if analysis_check == 'geral':
                    name += 't'

                metrics_dict = [
                    [x.id, x.author_experience, x.normalized_delta * CommonsConstants.ROUDING_SCALE,
                     x.total_commits,
                     x.author_seniority,
                     x.u_cloc] for x in commits]

                components_metrics = []
                metrics_count = 0
                for commit in commits:
                    for component_degradation in commit.component_commits.all():
                        if component_degradation.delta_rmd != 0:
                            components_metrics.append(
                                [component_degradation.id, component_degradation.author_experience,
                                 component_degradation.delta_rmd * CommonsConstants.ROUDING_SCALE,
                                 commit.u_cloc])
                        else:
                            metrics_count += 1
                            print('Component does not degrade. Counter: ' + str(
                                metrics_count))

                my_df = pd.DataFrame(components_metrics,
                                     columns=['time', 'experiencia', 'degradacao', 'LOC'])
                my_df.to_csv('component_metrics_' + name + ExtensionsFile.CSV, index=False, header=True)

            if len(metrics_dict) > 0:
                if directory_filter > 0:
                    my_df = pd.DataFrame(metrics_dict,
                                         columns=['commit', 'experiencia', 'degradacao', 'q_commit', 'senioridade',
                                                  'LOC'])
                else:
                    my_df = pd.DataFrame(metrics_dict,
                                         columns=['commit', 'experiencia', 'degradacao', 'q_commit', 'senioridade',
                                                  'LOC'])

                name += ExtensionsFile.CSV

                my_df.to_csv(name, index=False, header=True)

        context = {
            'title': 'Relatório de commits impactantes',
            'metrics': commits,
            'current_directory_id': directory_filter,
            'current_tag_id': tag_filter,
            'current_developer_id': developer_filter,
            'directories': directories,
            'developers': developers,
            'delta_check': delta_check,
            'analysis_check': analysis_check,
            'until_tag_state': full_tag,
        }

        logger.info(f'[{__name__}] Done to filter metrics')
        return context

    def read_pm_file(self, folder, tag_id):
        '''Read PM.csv files from each commit of a specific tag'''
        tag = self.tag_repository.find_by_primary_key(pk=tag_id)

        self.clean_all_commits_metrics()

        components_evolution = []
        n_commits = 0
        metrics = {}

        sorted_files = sort_files_by_commit_order_asc(files=os.listdir(folder))
        for subdirectory in sorted_files:

            subdirectory = os.path.join(folder, subdirectory)
            components = []

            logger.info("\n" + os.path.join(folder, subdirectory) + "\n----------------------\n")
            commit = None

            csv_files = [f for f in os.listdir(subdirectory) if f.endswith(ExtensionsFile.CSV)]

            for filename in csv_files:
                try:
                    logger.info(f'file: {filename}')

                    rmd = 0.0

                    file = open(os.path.join(subdirectory, filename), "r")
                    content = file.readlines()

                    hash_commit = file.name.split('\\')[1].split('-')[2]
                    commit = self.commit_repository.find_all_commits_by_hash(hash=hash_commit).first()

                    commit_rmds = []

                    for line in content[1:]:
                        col = line.split(',')
                        rmd = float(col[5].replace(CommonsConstants.END_STR, ''))
                        package = col[0].replace('.', CommonsConstants.PATH_SEPARATOR)

                        directory_str = tag.main_directory_prefix + package
                        directory = Directory.objects.filter(name__exact=directory_str)

                        if not directory.exists():
                            continue

                        directory = directory.first()

                        # Change architecture
                        components.append(directory)

                        print(line.replace("\n", ""))

                        commit_rmds.append([rmd, True if directory.initial_commit == commit else False])

                finally:
                    file.close()
                    # Hypothesis 1: processing
                    commit.h1_calculate_commit_degradation(commit_rmds)

        logger.info(components_evolution)

        return metrics

    def clean_all_commits_metrics(self):
        Commit.objects.update(mean_rmd_components=0.0, std_rmd_components=0.0,
                              delta_rmd_components=0.0, normalized_delta=0.0, compilable=False)
        ComponentCommit.objects.update(delta_rmd=0.0, rmd=0.0)
        Directory.objects.update(visible=False)

    def __update_compilable_commits(self, commits_with_errors):
        try:
            file = open(commits_with_errors, 'r')
            my_file = File(file)
            i = 0
            for commit in my_file:
                if i > 1:
                    commit = commit.replace(constants.CommonsConstants.END_STR, '')
                    try:
                        # Go to version
                        hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace(
                            constants.CommonsConstants.HYPHEN_SEPARATOR, '')
                        object_commit = self.commit_repository.find_all_compilable_commits_by_hash(hash=hash_commit)
                        if not object_commit.exists():
                            continue
                        else:
                            object_commit = object_commit[0]

                        object_commit.clean_all_commits_metrics()
                        object_commit.save()

                    except OSError as e:
                        logger.exception('Error: %s - %s.' % (e.filename, e.strerror))
                    except Exception as er:
                        logger.exception(er)
                i += 1
        except Exception as e:
            logger.exception(e)
            raise
        finally:
            file.close()
