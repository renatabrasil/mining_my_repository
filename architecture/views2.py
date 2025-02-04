# standard library
import logging
import os
import re
import shutil
import subprocess
from collections import OrderedDict

# third-party
import numpy as np
import pandas as pd
# Django
from django.contrib import messages
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import loader
from django.urls import reverse
# local Django
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from architecture.models import FileCommits
from common.constants import CommonsConstantsUtils
from common.utils import ViewUtils
from contributions.models import (Commit, Developer, Directory,
                                  Project,
                                  Tag, ComponentCommit)
from contributions.repositories.commit_repository import CommitRepository
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.directory_repository import DirectoryRepository
from contributions.repositories.project_repository import ProjectRepository
from contributions.repositories.tag_repository import TagRepository

SCALE = 6
ROUDING_SCALE = 10 ** SCALE

# 1: ON, Otherwise: OFF
NO_OUTLIERS = 1

logger = logging.getLogger(__name__)

commit_repository = CommitRepository()
project_repository = ProjectRepository()
developer_repository = DeveloperRepository()
directory_repository = DirectoryRepository()
tag_repository = TagRepository()


@require_http_methods(["GET", "POST"])
def compiled(request, file_id):
    '''
    Method responsible for create compiled of all commits of interest. Commits are collected in a file that was generated
    by 'list_commits()', a method based on all commits considered when feature 'load commit' was chosen by user.
    Commits of interest are those whose:
    1 - Are java files
    2 - Are in master or trunk branch (which were defined as main branch on project model)
    3 - Has a parent or child commit (because of delta may be different than 0)
    4 - Are in main directory (which were defined on project model)
    '''
    file = FileCommits.objects.get(pk=file_id)
    current_project_path = os.getcwd()
    try:
        f = open(file.__str__(), 'r')
        myfile = File(f)
        compiled_directory = f'{file.directory}/{file.name.replace(".txt", "")}/jars'
        if not os.path.exists(compiled_directory):
            os.makedirs(compiled_directory, exist_ok=True)

        i = 0
        commit_with_errors = []

        error = False
        for commit in myfile:
            commit = commit.replace('\n', '')
            if i == 0:
                local_repository = commit
            elif i == 1:
                build_path = commit
            else:
                try:
                    jar_folder = f'{current_project_path}/{compiled_directory}/version-{commit.replace("/", "").replace(".", "-")}'

                    if not __has_jar_file__(jar_folder):
                        os.chdir(local_repository)

                        # Go to version
                        hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-', '')
                        object_commit = commit_repository.find_all_commits_by_hash(hash=hash_commit)

                        if object_commit.exists():
                            object_commit = object_commit[0]
                        else:
                            continue

                        if not object_commit.has_impact_loc:
                            continue

                        checkout = subprocess.Popen(f'git reset --hard {hash_commit}',
                                                    shell=False, cwd=local_repository)
                        checkout.wait()

                        logger.info(os.environ.get('JAVA_HOME'))
                        logger.info(os.environ.get('ANT_HOME'))
                        logger.info(os.environ.get('M2_HOME'))

                        # Prepare build commands
                        for command in file.tag.pre_build_commands:
                            rc = os.system(command)
                            if rc != 0:
                                print("Error on compile")
                                continue
                        # shutil.rmtree('C:/Users/brasi/Documents/ant/build', ignore_errors=True)

                        rc = os.system(file.tag.build_command)

                        if rc != 0:
                            print("Error on compile")
                            error = True

                        # Create jar
                        jar_folder = f'{current_project_path}/{compiled_directory}/version-{commit.replace("/", "").replace(".", "-")}'
                        jar_file = f'"{current_project_path}/{compiled_directory}/version-{commit.replace("/", "").replace(".", "-")}/version-{commit.replace("/", "").replace(".", "-")}.jar"'

                        os.makedirs(jar_folder, exist_ok=True)

                        input_files = f'"{local_repository}/{build_path}"'
                        logger.info(f'comando: jar -cf {jar_file} {input_files}')
                        process = subprocess.Popen(f'jar -cf {jar_file} {build_path}', cwd=local_repository,
                                                   shell=False)
                        process.wait()

                        # Check whether created jar is valid
                        os.chdir(current_project_path)
                        jar = jar_file.replace(current_project_path, "").replace("/", "", 1).replace("\"", "")
                        # 100 KB

                        if os.path.getsize(jar) < 3072000 or error:
                            error = False
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
                            __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory,
                                                           current_project_path, jar)

                            # os.system('bootstrap.bat')
                            # TODO: extract method
                            if object_commit is not None:
                                object_commit.compilable = False
                                object_commit.mean_rmd_components = 0.0
                                object_commit.std_rmd_components = 0.0
                                object_commit.delta_rmd_components = 0.0
                                object_commit.normalized_delta = 0.0

                            os.chdir(local_repository)
                        else:
                            error = False

                            if not __generate_csv__(jar_folder):
                                __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory,
                                                               current_project_path, jar)
                                object_commit.compilable = False
                            else:
                                object_commit.compilable = True

                            object_commit.save()

                        build_path_repository = local_repository + CommonsConstantsUtils.PATH_SEPARATOR + build_path
                        if build_path.count('\\') <= 1 and build_path.count(CommonsConstantsUtils.PATH_SEPARATOR) <= 1:
                            build_path_repository = local_repository + CommonsConstantsUtils.PATH_SEPARATOR + build_path
                        if os.path.exists(build_path_repository):
                            shutil.rmtree(build_path_repository)

                except OSError as e:
                    logger.exception(f"Error: {e.filename} - {e.strerror}.")
                except Exception as er:
                    logger.exception(er)
                    messages.error(request, f'Erro: {er}')
                finally:
                    os.chdir(local_repository)

            i += 1
    except Exception as e:
        print(e)
        messages.error(request, 'Could not create compiled.')
    finally:
        os.chdir(current_project_path)
        if len(commit_with_errors) > 0:
            try:
                f = open(compiled_directory.replace("jars", "") + "log-compilation-errors.txt", 'w+')
                myfile = File(f)
                first = True
                myfile.write(local_repository + "\n")
                myfile.write(build_path + "\n")
                for commit in commit_with_errors:
                    if first:
                        myfile.write(commit)
                        first = False
                    else:
                        myfile.write("\n" + commit)
            except OSError as e:
                print("Error: %s - %s." % (e.filename, e.strerror))
            finally:
                f.close()
    file.has_compileds = True
    file.save()

    return HttpResponseRedirect(reverse('architecture:index', ))


# Using overall design evaluation
@require_http_methods(["GET", "POST"])
def impactful_commits(request):
    export_csv = (request.GET.get("export_csv") or request.POST.get("export_csv") == "true")

    full_tag = request.POST.get('until_tag')

    if not full_tag and (request.GET.get('until_tag') and request.GET.get('until_tag') == 'on'):
        full_tag = 'on'

    directories = Directory.objects.filter(visible=True, project_id=request.session['project']).order_by("name")
    developers = developer_repository.find_all().order_by("name")
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

    if request.POST.get('directory_id') or request.GET.get('directory_id'):
        directory_filter = int(request.POST.get('directory_id')) if request.POST.get('directory_id') else int(
            request.GET.get('directory_id'))
        if directory_filter > 0:
            query.setdefault('directory_id', directory_filter)
            directory_name = directory_repository.find_by_primary_key(pk=directory_filter).name.replace(
                CommonsConstantsUtils.PATH_SEPARATOR, '_')

    if request.POST.get('tag_id') or request.GET.get('tag_id'):
        tag_filter = int(request.POST.get('tag_id')) if request.POST.get('tag_id') else int(request.GET.get('tag_id'))
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
            tag_name = tag_repository.find_by_primary_key(pk=tag_filter).description.replace(
                CommonsConstantsUtils.PATH_SEPARATOR, '_')

    if request.POST.get('developer_id') or request.GET.get('developer_id'):
        developer_filter = int(request.POST.get('developer_id')) if request.POST.get('developer_id') else int(
            request.GET.get('developer_id'))
        if developer_filter > 0:
            if directory_filter > 0:
                query.setdefault('commit__author_id', developer_filter)
            else:
                query.setdefault('author_id', developer_filter)
            dev_name = developer_repository.find_by_primary_key(pk=developer_filter).name.replace(" ", "_").lower()

    if len(query) > 0:
        if request.POST.get('delta_rmd') == 'positive' or request.GET.get('delta_rmd') == 'positive':
            query.setdefault('delta_rmd__gt', 0)
            delta_check = 'positive'
        elif request.POST.get('delta_rmd_components') == 'positive' or request.GET.get(
                'delta_rmd_components') == 'positive':
            query.setdefault('normalized_delta__gt', 0)
            delta_check = 'positive'
        elif request.POST.get('delta_rmd_components') == 'negative' or request.GET.get(
                'delta_rmd_components') == 'negative':
            query.setdefault('normalized_delta__lt', 0)
            delta_check = 'negative'
        elif request.POST.get('delta_rmd') == 'negative' or request.GET.get('delta_rmd') == 'negative':
            query.setdefault('delta_rmd__lt', 0) if directory_filter > 0 else query.setdefault('normalized_delta__lt',
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
                if request.POST.get('analysis') == 'geral' or request.GET.get('analysis') == 'geral':
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
                [x.commit.id, x.commit.author_experience, x.commit.delta_rmd * ROUDING_SCALE, x.commit.total_commits,
                 x.commit.author_seniority, x.commit.u_cloc] for x in commits]

            del query['directory_id']
            components = ComponentCommit.no_outliers_objects.exclude(delta_rmd=0).filter(**query).order_by(
                'id')
            components_metrics = [
                [x.id, x.author_experience, x.delta_rmd / x.commit.u_cloc * ROUDING_SCALE, x.commit.u_cloc] for x in
                components]

            my_df = pd.DataFrame(components_metrics,
                                 columns=['time', 'experiencia', 'degradacao', 'LOC'])
            my_df.to_csv('component_metrics.csv', index=False, header=True)
        else:
            commits = sorted(commits, key=lambda x: x.id, reverse=False)

            name = ''
            if dev_name:
                name += dev_name + '-'
            if directory_name:
                name += directory_name + '-'
            if tag_name:
                name += tag_name + '-'
            if delta_check:
                name += delta_check
            if name.endswith('-'):
                name = name[:-1]
            if analysis_check == 'geral':
                name += 't'

            metrics_dict = [
                [x.id, x.author_experience, x.normalized_delta * ROUDING_SCALE, x.total_commits, x.author_seniority,
                 x.u_cloc] for x in commits]

            components_metrics = []
            metrics_count = 0
            for commit in commits:
                for component_degradation in commit.component_commits.all():
                    if component_degradation.delta_rmd != 0:
                        components_metrics.append([component_degradation.id, component_degradation.author_experience,
                                                   component_degradation.delta_rmd * ROUDING_SCALE,
                                                   commit.u_cloc])
                    else:
                        metrics_count += 1
                        print('Component does not degrade. Counter: ' + str(
                            metrics_count))

            my_df = pd.DataFrame(components_metrics,
                                 columns=['time', 'experiencia', 'degradacao', 'LOC'])
            my_df.to_csv('component_metrics_' + name + '.csv', index=False, header=True)

        if len(metrics_dict) > 0:
            if directory_filter > 0:
                my_df = pd.DataFrame(metrics_dict,
                                     columns=['commit', 'experiencia', 'degradacao', 'q_commit', 'senioridade', 'LOC'])
            else:
                my_df = pd.DataFrame(metrics_dict,
                                     columns=['commit', 'experiencia', 'degradacao', 'q_commit', 'senioridade', 'LOC'])

            name += '.csv'

            my_df.to_csv(name, index=False, header=True)

    if directory_filter > 0:
        template = loader.get_template('architecture/old_impactful_commits.html')
    else:
        template = loader.get_template('architecture/impactful_commits.html')

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

    return HttpResponse(template.render(context, request))


def update_compilable_commits(commits_with_errors):
    try:
        f = open(commits_with_errors, 'r')
        my_file = File(f)
        i = 0
        for commit in my_file:
            if i > 1:
                commit = commit.replace('\n', '')
                try:
                    # Go to version
                    hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-', '')
                    object_commit = commit_repository.find_all_compilable_commits_by_hash(hash=hash_commit)
                    if not object_commit.exists():
                        continue
                    else:
                        object_commit = object_commit[0]

                    object_commit.compilable = False
                    object_commit.mean_rmd_components = 0.0
                    object_commit.std_rmd_components = 0.0
                    object_commit.delta_rmd_components = 0.0
                    object_commit.normalized_delta = 0.0
                    object_commit.save()

                except OSError as e:
                    logger.exception("Error: %s - %s." % (e.filename, e.strerror))
                except Exception as er:
                    logger.exception(er.with_traceback())
            i += 1
    except Exception as e:
        logger.exception(e.with_traceback())
        raise
    finally:
        f.close()


@require_http_methods(["GET", "POST"])
def calculate_metrics(request, file_id):
    '''Process metrics calculation request from view'''
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt", "")
    metrics_directory = directory_name + "/metrics"
    if not os.path.exists(metrics_directory):
        os.makedirs(metrics_directory, exist_ok=True)
    if os.path.exists(directory_name + "/log-compilation-errors.txt"):
        update_compilable_commits(directory_name + "/log-compilation-errors.txt")
    directory_name = directory_name + "/jars"
    file.metrics_calculated_at = timezone.localtime(timezone.now())
    file.save()
    return HttpResponseRedirect(reverse('architecture:index', ))


@require_http_methods(["GET", "POST"])
def calculate_architecture_metrics(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt", "")
    directory_name = directory_name + "/jars"
    if os.path.exists(directory_name):
        arr = os.listdir(directory_name)
        sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
        for subdirectory in sorted_files:
            __generate_csv__(directory_name + "/" + subdirectory)
    return HttpResponseRedirect(reverse('architecture:index', ))


@require_GET
def metrics_by_commits(request):
    directories = directory_repository.find_all_visible_directories_order_by_id().order_by("name")
    template = loader.get_template('architecture/metrics_by_directories.html')
    tag = ViewUtils.load_tag(request)
    architectural_metrics_list = []

    directories_filter = 0
    developer_id = 0
    if request.POST.get('directory_id'):
        directories_filter = int(request.POST.get('directory_id'))
        if request.POST.get('developer_id'):
            developer_id = int(request.POST.get('developer_id'))
            architectural_metrics_list = ComponentCommit.objects.filter(component_id=directories_filter,
                                                                        commit__author_id=developer_id,
                                                                        commit__tag_id=tag)
        else:
            architectural_metrics_list = ComponentCommit.objects.filter(
                component_id=int(directories_filter), commit__tag_id=tag)

    results = OrderedDict()
    for metric in architectural_metrics_list:
        if metric.directory not in results:
            results.setdefault(metric.directory, list())
        results[metric.directory].append(metric)
    context = {
        'tag': tag,
        'results': results,
        'directories': directories,
        'current_directory_id': directories_filter,
        'current_developer_id': developer_id,
    }

    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def metrics_by_developer(request):
    template = loader.get_template('architecture/metrics_by_developer.html')
    tag = ViewUtils.load_tag(request)
    architectural_metrics_list = []
    developer = None
    if request.POST.get('developer_id'):
        developer_id = int(request.POST.get('developer_id'))
        developer = Developer.objects.get(pk=developer_id)
        architectural_metrics_list = ComponentCommit.objects.filter(commit__author_id=developer_id,
                                                                    commit__tag_id=tag.id)
    context = {
        'tag': tag,
        'results': architectural_metrics_list,
        'current_developer': developer,
    }
    return HttpResponse(template.render(context, request))


@require_http_methods(["GET", "POST"])
def quality_between_versions(request):
    template = loader.get_template('architecture/metrics_between_versions.html')
    tag = ViewUtils.load_tag(request)
    directory = request.POST.get('directory')
    metrics_by_directories = OrderedDict()
    metrics = []
    if directory:
        if os.path.exists(directory):
            arr = os.listdir(directory)
            sorted_files = sorted(arr, key=lambda x: int(x.split('#')[len(x.split('#')) - 1]))
            for subdirectory in sorted_files:
                __generate_csv__(directory + "/" + subdirectory)
                version = subdirectory
                subdirectory = os.path.join(directory, subdirectory)
                print("\n" + subdirectory + "\n----------------------\n")
                for filename in [f for f in os.listdir(subdirectory) if f.endswith(".csv")]:
                    try:
                        f = open(os.path.join(subdirectory, filename), "r")
                        content = f.readlines()
                        for line in content[1:]:
                            row = line.split(',')
                            row[5] = row[5].replace(CommonsConstantsUtils.END_STR, '')
                            row[0] = row[0].replace('.', CommonsConstantsUtils.PATH_SEPARATOR)
                            print(line.replace("\n", ""))

                            if row[0] not in metrics_by_directories:
                                metrics_by_directories.setdefault(row[0], {})
                            if version not in metrics_by_directories[row[0]]:
                                metrics_by_directories[row[0]].setdefault(version, 0.0)
                            metrics_by_directories[row[0]][version] = row[5]

                    finally:
                        f.close()

                components_mean = []
                dict2 = list(metrics_by_directories.values())
                for value in dict2:
                    if version in value:
                        components_mean.append(float(value[version]))

                # ANT
                name_version = version.replace('rel#', '').replace('-', '', 1).replace('_', '.').replace('#', '-')
                # Lucene
                name_version = version.replace('_', '.').replace('#', '-')
                # Cassandra
                name_version = version.replace('_', '.').replace('#', '-')

                architectural_quality = np.mean(components_mean)
                metrics.append([name_version, architectural_quality])

                # FIXME this is too naive and just work for this project. Should be fix soon.
                # Ant
                tag_repository.update(Tag, {'delta_rmd_components': architectural_quality})

        my_df_metrics = pd.DataFrame(metrics, columns=['versao', 'D'])
        my_df = pd.DataFrame(metrics_by_directories)
        print(my_df)
        my_df_metrics.to_csv('metrics_by_version.csv', index=True, index_label='idx', header=True)
        my_df.to_csv(directory.replace(CommonsConstantsUtils.PATH_SEPARATOR, '_') + '.csv', index=True, header=True)
    context = {
        'title': 'Cálculo de qualidade da arquitetura por versões',
        'tag': tag,
    }
    return HttpResponse(template.render(context, request))


################ Auxiliary methods ###################

@require_http_methods(["GET", "POST"])
def __read_pm_file(folder, tag_id):
    '''Read PM.csv files from each commit of a specific tag'''
    metrics = {}
    tag = tag_repository.find_by_primary_key(pk=tag_id)

    Commit.objects.update(mean_rmd_components=0.0, std_rmd_components=0.0,
                          delta_rmd_components=0.0, normalized_delta=0.0, compilable=False)
    ComponentCommit.objects.update(delta_rmd=0.0, rmd=0.0)
    Directory.objects.update(visible=False)
    Commit.objects.update(changed_architecture=False)
    components_evolution = []
    n_commits = 0

    # To sort in natural order
    arr = os.listdir(folder)
    sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
    for subdirectory in sorted_files:
        subdirectory = os.path.join(folder, subdirectory)
        components_db = directory_repository.find_all_visible_directories_order_by_id()
        components = []
        print("\n" + os.path.join(folder, subdirectory) + "\n----------------------\n")
        for filename in [f for f in os.listdir(subdirectory) if f.endswith(".csv")]:
            try:
                rmd = 0.0
                f = open(os.path.join(subdirectory, filename), "r")
                content = f.readlines()
                hash_commit = f.name.split('\\')[1].split('-')[2]
                commits = commit_repository.find_all_commits_by_hash(hash=hash_commit)
                if commits.count() > 0:
                    commit = commits[0]

                # else:
                #     continue
                commit_rmds = []

                for line in content[1:]:
                    row = line.split(',')
                    row[5] = row[5].replace(CommonsConstantsUtils.END_STR, '')
                    row[0] = row[0].replace('.', CommonsConstantsUtils.PATH_SEPARATOR)

                    directory_str = tag.main_directory_prefix + row[0]
                    directory = Directory.objects.filter(name__exact=directory_str)
                    if directory.count() == 0:
                        continue
                    directory = directory[0]

                    # Change architecture
                    components.append(directory)

                    print(line.replace("\n", ""))
                    rmd = float(row[5])

                    commit_rmds.append(
                        [rmd, True if directory.initial_commit == commit else False])

            finally:
                f.close()
                # Hypothesis 1: processing
                commit = h1_calculate_commit_degradation(commit, commit_rmds)

                # TODO: delete
                # To save changes in directories
                removed_components = [x for x in list(components_db) if x not in components]
                add_components = [x for x in components if x not in list(components_db)]
                diff_components = removed_components + add_components
                n_commits += 1
                if len(diff_components) > 0:
                    components_evolution.append([n_commits, len(diff_components)])
                    for a_component in diff_components:
                        if a_component.visible:
                            a_component.visible = False
                        else:
                            a_component.visible = True
                        a_component.save()
                else:
                    components_evolution.append([n_commits, len(diff_components)])

    print(components_evolution)

    return metrics


def __create_files__(form, project_id):
    project = get_object_or_404(Project, pk=project_id)
    files = generate_list_of_compiled_commits(project, form)
    return files


def generate_list_of_compiled_commits(project, form):
    '''
    Generate list of commits that will be compiled
    :param project: current project selected
    :param form: data from form
    '''
    # Restricting to commits which has children
    FileCommits.objects.filter(tag__project=project).delete()
    folder = form['directory'].value()

    if not folder:
        raise ValueError("Directory is not informed")

    commits = commit_repository.find_all_commits_by_project_order_by_id_asc_as_list(project=project)

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
        file = __update_file_commits__(form, filename)
        file.tag = first_commit.tag
        files.append(file)
        f = open(file.__str__(), 'w')
        my_file = File(f)
        my_file.write(form['git_local_repository'].value() + "\n")
        my_file.write(form['build_path'].value() + "\n")
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
                file = __update_file_commits__(form, filename)
                file.tag = commit.tag
                f = open(file.__str__(), 'w')
                my_file = File(f)
                files.append(file)
                my_file.write(form['git_local_repository'].value() + "\n")
                my_file.write(form['build_path'].value() + "\n")
            if not commit.has_impact_loc and not commit.children_commit:
                continue
            my_file.write(str(i) + "-" + commit.hash + "\n")
            i += 1
        my_file.closed
        f.closed
        file.save()

    except Exception as e:
        logger.exception(e.args[0])
        raise
    return files


def __generate_csv__(folder):
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if "PM.csv" not in os.listdir(folder) and filename.endswith(".jar"):
                try:
                    arcan_metrics = subprocess.Popen('java -jar Arcan-1.2.1-SNAPSHOT.jar'
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


def __update_file_commits__(form, filename):
    file = FileCommits.objects.filter(name=filename)
    if file.count() > 0:
        file = file[0]
        file.name = filename
        file.directory = form['directory'].value()
    else:
        file = FileCommits(directory=form['directory'].value(), name=filename, build_path=form['build_path'].value(),
                           local_repository=form['git_local_repository'].value())

    return file


def __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory, current_project_path, jar):
    os.chdir(current_project_path + CommonsConstantsUtils.PATH_SEPARATOR + compiled_directory)
    folder = 'version-' + commit.replace(CommonsConstantsUtils.PATH_SEPARATOR, "").replace(".",
                                                                                           CommonsConstantsUtils.HYPHEN_SEPARATOR)
    commit_with_errors.append(
        commit.replace(CommonsConstantsUtils.PATH_SEPARATOR, "").replace(".", CommonsConstantsUtils.HYPHEN_SEPARATOR))
    shutil.rmtree(folder, ignore_errors=True)
    print("BUILD FAILED or Jar creation failed\n")
    print(jar + " DELETED\n")


def __has_jar_file__(directory):
    exists = False
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if exists:
                break
            if filename.endswith(".jar") or filename.endswith(".csv"):
                exists = True
    return exists


def __belongs_to_component__(component, directories):
    '''
    Checks whether a commit belongs to analized commit (in case that project has separate compilated modules, e.g. Hadoop)
    :param component:
    :param directories:
    :return: whether belongs or not
    '''
    for dir in directories:
        if dir.name.startswith(component):
            return True
    return False


def h2_calculate_component_degradation(commit, directory, rmd):
    '''Invoked by __read_PM_file__

     return a dictionary key: module (component) value: dictionary key: commit value: metrics (RMD) {"org.apache.ant": {
        # "da5a13f8e4e0e4475f942b5ae5670271b711d423": 0.5565}, {"66c400defd2ed0bd492715a7f4f10e2545cf9d46": 0.0}}
    '''
    component_commit = ComponentCommit.objects.filter(commit=commit, component=directory)
    if component_commit.exists():
        component_commit = component_commit[0]
        component_commit.rmd = rmd
        previous_component = retrieve_previous_component_commit(commit, directory)
        component_commit.delta_rmd = rmd - previous_component.rmd if previous_component else rmd
        if component_commit.delta_rmd != 0:
            uloc = commit.non_blank_cloc(component_commit.component)
            if uloc > 0:
                component_commit.delta_rmd /= uloc

        component_commit.save()
    return component_commit


def h1_calculate_commit_degradation(commit, commit_rmds):
    '''Invoked by __read_PM_file__'''
    if len(commit_rmds) > 0:
        commit.mean_rmd_components = np.mean([c[0] for c in commit_rmds])
        commit.std_rmd_components = np.std([c[0] for c in commit_rmds], ddof=1)
        commit.delta_rmd_components = commit.mean_rmd_components

    # Delta calculation
    commit.previous_impactful_commit = retrieve_previous_commit(commit)

    if commit.has_impact_loc and (
            commit.previous_impactful_commit is not None and commit.previous_impactful_commit.compilable and commit.previous_impactful_commit.tag == commit.tag):
        commit.delta_rmd_components -= commit.previous_impactful_commit.mean_rmd_components
    # elif commit.previous_impactful_commit is not None and not commit.previous_impactful_commit.compilable:
    else:
        commit.delta_rmd_components = 0.0

    # Delta normalization by LOC changed
    if commit.u_cloc > 0:
        commit.normalized_delta = commit.delta_rmd_components / commit.u_cloc
    else:
        commit.normalized_delta = commit.delta_rmd_components
        logger.error("****** CASO ESPECIAL: commit sem linha de impacto (LOC=0) com delta diferentee de zero ******")

    commit.compilable = True
    commit.save()

    return commit


def retrieve_previous_commit(commit):
    if commit:
        if len(commit.parents) > 0:
            return commit.parents[0]
        return commit_repository.find_all_previous_commits(commit=commit).last()

    return None


def retrieve_previous_component_commit(commit, directory):
    component = ComponentCommit.objects.filter(component=directory, commit_id__lt=commit.id,
                                               commit__author=commit.author, commit__tag=commit.tag,
                                               commit__tag__real_tag_description__iexact=commit.tag.real_tag_description)
    if component.exists():
        return component.last()
    return None
