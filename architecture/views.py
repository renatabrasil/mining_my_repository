# standard library
import os
import re
import shutil
import subprocess
import sys
from builtins import object
from collections import OrderedDict
from itertools import groupby

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
from django.utils.timezone import now

from architecture.forms import FilesCompiledForm
from architecture.models import ArchitecturalMetricsByCommit, FileCommits
from common.utils import ViewUtils
from contributions.models import (Commit, Developer, Directory,
                                  IndividualContribution, Project,
                                  ProjectIndividualContribution, Tag, ComponentCommit)
from dataanalysis.models import AnalysisPeriod

SCALE = 6
ROUDING_SCALE = 10**SCALE

# 1: ON, Otherwise: OFF
NO_OUTLIERS = 1


def index(request):
    """"Architecture Configuration"""
    tag = ViewUtils.load_tag(request)
    request.project = request.session['project']
    template = loader.get_template('architecture/index.html')
    files = []
    project_id = request.session['project']
    project = Project.objects.get(id=project_id)

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = FilesCompiledForm(request.POST)

        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            files = __create_files__(form, project_id)
            if files:
                messages.success(request, 'Files successfully created!')
            else:
                messages.error(request, 'Could not create files.')

            # HttpResponseRedirect(reverse('architecture:index',))
        # if a GET (or any other method) we'll create a blank form

    form = FilesCompiledForm(initial={'directory': 'compiled/'+project.project_name.lower().replace(' ','-'),
                                      'git_local_repository': 'G:/My Drive/MestradoUSP/programacao/projetos/git/ant',
                                      'build_path': 'build/classes'})
    files = FileCommits.objects.filter(tag__project=request.project).order_by("name")

    context = {
        'tag': tag,
        'files': files,
        'form': form,
    }

    return HttpResponse(template.render(context, request))

def results(request, project_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % project_id)

def compileds(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    current_project_path = os.getcwd()
    try:
        f = open(file.__str__(), 'r')
        myfile = File(f)
        compiled_directory = file.directory+"/"+file.name.replace(".txt","")+"/jars"
        if not os.path.exists(compiled_directory):
            os.makedirs(compiled_directory, exist_ok=True)

        i = 0
        commit_with_errors = []
        commits_not_compilable = Commit.objects.filter(tag=file.tag,compilable=False).values_list("hash",flat=True)
        average_file_size = 0
        error = False
        for commit in myfile:
            commit = commit.replace('\n','')
            if i==0:
                local_repository = commit
            elif i==1:
                build_path = commit
            else:
                try:
                    jar_folder = current_project_path + '/' + compiled_directory + '/version-' + commit.replace("/",
                                                                                                                "").replace(
                        ".", "-")

                    if not __has_jar_file__(jar_folder):
                        os.chdir(local_repository)
                        # OPENJPA
                        # rc = os.system("mvn clean")

                        # Go to version
                        hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-','')
                        object_commit = Commit.objects.filter(hash=hash_commit)[0]
                        # if len(object_commit.parents)
                        if not (len(object_commit.parents) > 0 and object_commit.parents[0] is not None and object_commit.parents[0].compilable) and not (object_commit.children_commit is not None):
                            object_commit.compilable = True
                            object_commit.save()
                            continue
                        checkout = subprocess.Popen('git reset --hard ' + hash_commit + '', cwd=local_repository)
                        checkout.wait()
                        print(os.environ.get('JAVA_HOME'))
                        print(os.environ.get('ANT_HOME'))
                        print(os.environ.get('M2_HOME'))

                        # Lucene
                        # build = subprocess.Popen('python fix.py', shell=False, cwd=local_repository)
                        # build.wait()
                        # shutil.rmtree(local_repository+'/lib', ignore_errors=True)
                        # Compile
                        # build = subprocess.Popen('build.bat', shell=False, cwd=file.local_repository)
                        # https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running
                        # LUCENE
                        # rc = os.system("ant compile-core")
                        # OPENJPA
                        # build = subprocess.Popen('python C:/Users/brasi/Documents/openjpa/cutoff_snapshot.py C:/Users/brasi/Documents/openjpa/pom.xml', shell=False, cwd=local_repository)
                        # build.wait()
                        # build = subprocess.Popen('python C:/Users/brasi/Documents/openjpa/cutoff_snapshot.py C:/Users/brasi/Documents/openjpa/openjpa-kernel/pom.xml', shell=False, cwd=local_repository)
                        # build.wait()

                        # build = subprocess.Popen('python C:/Users/brasi/Documents/mining_my_repository/cutoff_snapshot.py C:/Users/brasi/Documents/maven/pom.xml', shell=False, cwd=local_repository)
                        # build.wait()
                        # build = subprocess.Popen('python C:/Users/brasi/Documents/mining_my_repository/cutoff_snapshot.py C:/Users/brasi/Documents/maven/maven-core/pom.xml', shell=False, cwd=local_repository)
                        # build.wait()

                        # Prepare build commands
                        for command in object_commit.tag.pre_build_commands:
                            rc = os.system(command)
                            if rc != 0:
                                print("Error on ant compile")
                                error = True
                                # break


                        rc = os.system(object_commit.tag.build_command)

                        # rc = os.system("ant compile")
                        if rc != 0:
                            print("Error on ant compile")
                            # error = True
                        # build = subprocess.Popen('ant compile-core', shell=False, cwd=file.local_repository)
                        # build.wait()

                        # Create jar
                        jar_folder = current_project_path + '/' + compiled_directory + '/version-' + commit.replace("/",
                                                                                                                    "").replace(
                            ".", "-")
                        jar_file = '"'+current_project_path+'/'+compiled_directory+'/'+ 'version-' + commit.replace("/","").replace(".","-") +'/version-' + commit.replace("/","").replace(".","-") + '.jar"'

                        os.makedirs(jar_folder, exist_ok=True)

                        input_files = "'"+local_repository+"/"+build_path+"'"
                        print("comando: jar -cf "+jar_file+" "+input_files )
                        process = subprocess.Popen('jar -cf ' + jar_file + ' ' + build_path, cwd=local_repository)
                        process.wait()

                        # Check whether created jar is valid
                        os.chdir(current_project_path)
                        jar = jar_file.replace(current_project_path,"").replace("/","",1).replace("\"","")
                        # 100 KB

                        if os.path.getsize(jar) < 102400 or error:
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
                            # TODO: extract method
                            object_commit.compilable = False
                            object_commit.mean_rmd_components = 0.0
                            object_commit.std_rmd_components = 0.0
                            object_commit.delta_rmd_components = 0.0
                            object_commit.normalized_delta = 0.0

                            os.chdir(local_repository)
                        else:
                            # if any(hash_commit == c for c in commits_not_compilable):
                            #     commit_with_errors.append(commit.replace("/","").replace(".","-")
                            if not __generate_csv__(jar_folder):
                                __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory,
                                                               current_project_path, jar)
                                object_commit.compilable = False
                            else:
                                object_commit.compilable = True
                            average_file_size = os.path.getsize(jar)

                        object_commit.save()

                        build_path_repository = local_repository+'/'+build_path
                        if build_path.count('\\') <= 1 and build_path.count('/') <= 1:
                            build_path_repository = local_repository + "/" + build_path
                        if os.path.exists(build_path_repository):
                            shutil.rmtree(build_path_repository)

                except OSError as e:
                    print("Error: %s - %s." % (e.filename, e.strerror))
                except Exception as er:
                    print(er)
                    messages.error(request, 'Erro: '+er)
                finally:

                    os.chdir(local_repository)
            i+=1
    except Exception as e:
        print(e)
        # shutil.rmtree(compiled_directory, ignore_errors=True)
        messages.error(request, 'Could not create compiled.')
    finally:
        os.chdir(current_project_path)
    if len(commit_with_errors) > 0:
        try:
            f = open(compiled_directory.replace("jars","")+"log-compilation-errors.txt", 'w+')
            # one_char = f.read(1)
            myfile = File(f)
            first = True
            # if not fetched then file is empty
            # if one_char:
            myfile.write(local_repository+"\n")
            myfile.write(build_path+"\n")
            # else:
            #     first = False
            for commit in commit_with_errors:
                if first:
                    myfile.write(commit)
                    first = False
                else:
                    myfile.write("\n"+commit)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))
        finally:
            f.close()
    file.has_compileds=True
    file.save()

    return HttpResponseRedirect(reverse('architecture:index',))


def __clean_not_compiled_version__(commit, commit_with_errors, compiled_directory, current_project_path, jar):
    os.chdir(current_project_path + '/' + compiled_directory)
    folder = 'version-' + commit.replace("/", "").replace(".", "-")
    # if not any(hash_commit == c for c in commits_not_compilable):
    commit_with_errors.append(commit.replace("/", "").replace(".", "-"))
    shutil.rmtree(folder, ignore_errors=True)
    print("BUILD FAILED or Jar creation failed\n")
    print(jar + " DELETED\n")


# Using overall design evaluation
def impactful_commits(request):
    tag = ViewUtils.load_tag(request)
    export_csv = (request.GET.get("export_csv") or request.POST.get("export_csv") == "true") if True else False
    # full_tag = (request.GET.get("until_tag_state") and request.POST.get("until_tag") == "true") if True else False

    full_tag = request.POST.get('until_tag')
    if not full_tag:
        if request.GET.get('until_tag') is not None and request.GET.get('until_tag') == 'on':
            full_tag = 'on'
        # until_tag_state = ''

    # analysis_check = request.POST.get('analysis') if request.POST.get('analysis') is not None else request.GET.get('analysis') == 'geral'

    directories = Directory.objects.filter(visible=True).order_by("name")
    developers = Developer.objects.all().order_by("name")
    developers = [d for d in developers if d.commits.exclude(normalized_delta=0).filter(tag__project=request.session['project'])]
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
        directory_filter = int(request.POST.get('directory_id')) if request.POST.get('directory_id') else int(request.GET.get('directory_id'))
        if directory_filter > 0:
            query.setdefault('directory_id', directory_filter)
            directory_name = Directory.objects.get(pk=directory_filter).name.replace('/', '_')

    if request.POST.get('tag_id') or request.GET.get('tag_id'):
        tag_filter = int(request.POST.get('tag_id')) if request.POST.get('tag_id') else int(request.GET.get('tag_id'))
        if tag_filter > 0:
            if full_tag:
                tag_query_str = 'tag_id'
            else:
                tag_query_str = 'tag_id__lte'
            if directory_filter > 0:
                query.setdefault('commit__'+tag_query_str, tag_filter)
            else:
                query.setdefault(tag_query_str, tag_filter)
            query.setdefault('tag__project_id', request.session['project'])
            tag_name = Tag.objects.get(pk=tag_filter).description.replace('/', '_')

    if request.POST.get('developer_id') or request.GET.get('developer_id'):
        developer_filter = int(request.POST.get('developer_id')) if request.POST.get('developer_id') else int(request.GET.get('developer_id'))
        if developer_filter > 0:
            if directory_filter > 0:
                query.setdefault('commit__author_id', developer_filter)
            else:
                query.setdefault('author_id', developer_filter)
            dev_name = Developer.objects.get(pk=developer_filter).name.replace(" ", "_").lower()

    if len(query) > 0:
        if request.POST.get('delta_rmd') == 'positive' or request.GET.get('delta_rmd') == 'positive':
            query.setdefault('delta_rmd__gt', 0)
            delta_check = 'positive'
        elif request.POST.get('delta_rmd_components') == 'positive' or request.GET.get('delta_rmd_components') == 'positive':
            query.setdefault('normalized_delta__gt', 0)
            delta_check = 'positive'
        elif request.POST.get('delta_rmd_components') == 'negative' or request.GET.get('delta_rmd_components') == 'negative':
            query.setdefault('normalized_delta__lt', 0)
            delta_check = 'negative'
        elif request.POST.get('delta_rmd') == 'negative' or request.GET.get('delta_rmd') == 'negative':
            query.setdefault('delta_rmd__lt', 0) if directory_filter > 0 else query.setdefault('normalized_delta__lt', 0)
            delta_check = 'negative'


        if directory_filter > 0:
            if 'delta_rmd__lt' in query or 'delta_rmd__gt' in query:
                commits = ArchitecturalMetricsByCommit.objects.filter(**query)
            else:
                commits = ArchitecturalMetricsByCommit.objects.exclude(delta_rmd=0).filter(**query)

            commits = sorted(commits, key=lambda x: x.commit.author_experience, reverse=False)
        else:
            if 'normalized_delta__lt' in query or 'normalized_delta__gt' in query:
                commits = request.commit_db.filter(**query)
            else:
                # commits = Commit.objects.exclude(delta_rmd_components=0).exclude(author_id=41).exclude(author_id=20).exclude(author_id=11).filter(**query)
                # query.setdefault('author_id__in', [41,20,11])
                if request.POST.get('analysis') == 'geral' or request.GET.get('analysis') == 'geral':
                    analysis_check = 'geral'
                    commits = request.commit_db.filter(**query)
                else:
                    analysis_check = 'impactful_commits'
                    commits = request.commit_db.exclude(normalized_delta=0).filter(**query)
            commits = sorted(commits, key=lambda x: x.author_experience, reverse=False)


    if export_csv:

        delta_threshold = 0
        if directory_filter > 0:
            commits = sorted(commits, key=lambda x: x.id, reverse=False)
            metrics_dict = [[x.commit.id,x.commit.author_experience,x.commit.delta_rmd * ROUDING_SCALE, x.commit.total_commits, x.commit.author_seniority, x.commit.u_cloc] for x in commits]

            del query['directory_id']
            components = ArchitecturalMetricsByCommit.no_outliers_objects.exclude(delta_rmd=0).filter(**query).order_by(
                'id')
            components_metrics = [[x.id, x.author_experience, x.delta_rmd * ROUDING_SCALE, x.commit.u_cloc] for x in
                                  components]

            my_df = pd.DataFrame(components_metrics,
                                 columns=['time', 'experiencia', 'degradacao', 'LOC'])
            my_df.to_csv('component_metrics.csv', index=False, header=True)
        else:
            commits = sorted(commits, key=lambda x: x.id, reverse=False)
            # metrics_dict = [[x.author_experience, x.delta_rmd_components, x.tag.description, x.changed_architecture] for x
            #                 in commits]
            # metrics_dict = [[x.author_experience, x.delta_rmd_components, x.u_cloc, x.total_commits, x.author_seniority] for x in commits]

            deltas = [abs(x.normalized_delta) for x in commits]


            # delta_threshold = np.percentile(deltas, 50)
            # delta_threshold = 21.62/(10 ** 7)

            # Maiores
            # metrics_dict = [[x.id, x.author_experience, x.delta_rmd_components*(10**6), x.total_commits, x.author_seniority, x.u_cloc]
            #                 for x in commits if abs(x.delta_rmd_components) > delta_threshold]

            # Statistics
            # devs = set([x.author for x in commits if abs(x.delta_rmd_components) < (1000/(10**7))])
            # total_devs = set([x.author for x in Commit.objects.all()])
            #
            # inovatos = set([x.author for x in commits if x.is_author_newcomer and abs(x.delta_rmd_components) < (1000/(10**7))])
            # ilong_devs = set([x.author for x in commits if not x.is_author_newcomer and abs(x.delta_rmd_components) < (1000/(10**7))])
            #
            # novatos = set([x.author for x in Commit.objects.all() if x.is_author_newcomer])
            # long_devs = set([x.author for x in Commit.objects.all() if not x.is_author_newcomer])

            # Standard
            # metrics_dict = [
            #     [x.id, x.author_experience, x.delta_rmd_components * (10 ** 7), x.total_commits, x.author_seniority,
            #      x.u_cloc]
            #     for x in commits if
            #     abs(x.delta_rmd_components) < (1000 / (10 ** 7))]

            if delta_threshold != 0:
                metrics_dict = [
                    [x.id, x.author_experience, x.normalized_delta * ROUDING_SCALE, x.total_commits, x.author_seniority,
                     x.u_cloc]
                    for x in commits if abs(x.normalized_delta) < delta_threshold]
            else:
                metrics_dict = [
                    [x.id, x.author_experience, x.normalized_delta * ROUDING_SCALE, x.total_commits, x.author_seniority,
                     x.u_cloc] for x in commits]

                # components_metrics = [[c.id, c.author_experience, c.commit.normalized_delta * ROUDING_SCALE, c.commit.u_cloc] for c in [list(x.component_commits.all()) for x in commits]]

                components_metrics = []
                for commit in commits:
                    for component in commit.component_commits.all():
                        component_degradation = ArchitecturalMetricsByCommit.objects.filter(commit=commit, directory=component.component)
                        if component_degradation.exists():
                            component_degradation = component_degradation[0]
                            components_metrics.append([component.id, component.author_experience, component_degradation.delta_rmd * ROUDING_SCALE, commit.u_cloc])
                        else:
                            print('oi')

                my_df = pd.DataFrame(components_metrics,
                                     columns=['time', 'experiencia', 'degradacao', 'LOC'])
                my_df.to_csv('component_metrics.csv', index=False, header=True)

                # dictionary[new_key] = dictionary[old_key]
                # del dictionary[old_key]
                # del query['directory_id']
                # components = ArchitecturalMetricsByCommit.no_outliers_objects.exclude(delta_rmd=0).filter(**query).order_by('id')
                # components_metrics = [[x.id, x.author_experience, x.delta_rmd * ROUDING_SCALE, x.commit.u_cloc] for x in components]
                # metrics_dict = [
                #     [x.id, x.author_experience, x.normalized_delta * ROUDING_SCALE, x.total_commits, x.author_seniority,
                #      x.u_cloc] for x in commits if x.author_experience <= 10000]


        if len(metrics_dict) > 0:
            if directory_filter > 0:
                my_df = pd.DataFrame(metrics_dict, columns=['commit','experiencia','degradacao','q_commit', 'senioridade','LOC'])
            else:
                # my_df = pd.DataFrame(metrics_dict, columns=['x', 'y', 'loc','commits', 't'])
                # my_df = pd.DataFrame(metrics_dict, columns=['x','y','tag','mudou'])
                my_df = pd.DataFrame(metrics_dict, columns=['commit', 'experiencia', 'degradacao', 'q_commit', 'senioridade', 'LOC'])

            name = ''
            if dev_name:
                name += dev_name+'-'
            if directory_name:
                name += directory_name+'-'
            if tag_name:
                name += tag_name + '-'
            if delta_check:
                name += delta_check
            if name.endswith('-'):
                name = name[:-1]
            if analysis_check == 'geral':
                name += 't'

            # name += '-maiores'
            if delta_threshold != 0:
                name += '-maioria'
            name += '.csv'

            my_df.to_csv(name, index=False, header=True)

            # Complementary data analysis
            # if len(longterm_devs) > 0:
            #     my_df = pd.DataFrame(longterm_devs, columns=['commit','experiencia', 'degradacao', 'q_commit', 'senioridade','LOC'])
            #     my_df.to_csv('longterm_devs_' + name, index=False, header=True)
            #
            # if len(newcomers) > 0:
            #     my_df = pd.DataFrame(newcomers, columns=['commit','experiencia', 'degradacao', 'q_commit', 'senioridade','LOC'])
            #     my_df.to_csv('newcomers_' + name, index=False, header=True)

            # if len(novices) > 0:
            #     my_df = pd.DataFrame(novices, columns=['x', 'y', 'commits'])
            #     my_df.to_csv('novices_' + tag_name + '.csv', index=False, header=True)
            #
            # commits_df = pd.DataFrame(commits_df, columns=['versao', 'commit'])
            # commits_df.to_csv('commits_by_version.csv', index=False, header=True)

    if directory_filter > 0:
        template = loader.get_template('architecture/old_impactful_commits.html')
    else:
        template = loader.get_template('architecture/impactful_commits.html')

    context = {

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
        myfile = File(f)
        i = 0
        for commit in myfile:
            if i > 1:
                commit = commit.replace('\n','')
                try:
                    # Go to version
                    hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-','')
                    object_commit = Commit.objects.filter(hash=hash_commit, compilable=True)
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
                    print("Error: %s - %s." % (e.filename, e.strerror))
                except Exception as er:
                    print(er)
            i+=1
    except Exception as e:
        print(e)
    finally:
        f.close()

def calculate_metrics(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt", "")
    metrics_directory = directory_name+"/metrics"
    if not os.path.exists(metrics_directory):
        os.makedirs(metrics_directory, exist_ok=True)
    if os.path.exists(directory_name+"/log-compilation-errors.txt"):
        update_compilable_commits(directory_name+"/log-compilation-errors.txt")
    directory_name = directory_name + "/jars"
    metrics = __read_PM_file__(directory_name,file.tag.id)
    file.metrics_calculated_at = timezone.localtime(timezone.now())
    file.save()
    directories = metrics.keys()
    for directory in directories:
        contributions = __pre_correlation__(metrics, directory)
        if contributions:
            my_df = pd.DataFrame(contributions)
            my_df.columns = ["Developer", "Specific XP", "Global XP", "Degrad Delta"]
            my_df.to_csv(metrics_directory+'/'+directory.replace('/','_')+'.csv', index=False, header=True)
    return HttpResponseRedirect(reverse('architecture:index', ))

def calculate_architecture_metrics(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt","")
    directory_name = directory_name+"/jars"
    if os.path.exists(directory_name):
        arr = os.listdir(directory_name)
        sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
        for subdirectory in sorted_files:
            __generate_csv__(directory_name + "/" + subdirectory)
    return HttpResponseRedirect(reverse('architecture:index',))

def metrics_by_commits(request):
    directories = Directory.objects.filter(visible=True).order_by("name")
    template = loader.get_template('architecture/metrics_by_directories.html')
    tag = ViewUtils.load_tag(request)
    architectural_metrics_list = []

    directories_filter = 0
    developer_id = 0
    if request.POST.get('directory_id'):
        directories_filter = int(request.POST.get('directory_id'))
        # directories_filter = Directory.objects.get(pk=directories_filter)
        if request.POST.get('developer_id'):
            developer_id = int(request.POST.get('developer_id'))
            architectural_metrics_list = ArchitecturalMetricsByCommit.objects.filter(directory_id=directories_filter,
                                                                                       commit__author_id=developer_id,
                                                                                       commit__tag_id=tag)
        else:
            architectural_metrics_list = ArchitecturalMetricsByCommit.objects.filter(directory_id=int(directories_filter),commit__tag_id=tag)

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

def metrics_by_developer(request):
    template = loader.get_template('architecture/metrics_by_developer.html')
    tag = ViewUtils.load_tag(request)
    architectural_metrics_list = []
    developer = None
    if request.POST.get('developer_id'):
        developer_id = int(request.POST.get('developer_id'))
        developer = Developer.objects.get(pk=developer_id)
        architectural_metrics_list = ArchitecturalMetricsByCommit.objects.filter(commit__author_id=developer_id,
                                                                                   commit__tag_id=tag.id)
    context = {
        'tag': tag,
        'results': architectural_metrics_list,
        'current_developer': developer,
    }
    return HttpResponse(template.render(context, request))

def quality_between_versions(request):
    template = loader.get_template('architecture/metrics_between_versions.html')
    tag = ViewUtils.load_tag(request)
    directory = request.POST.get('directory')
    metrics_by_directories = OrderedDict()
    metrics = []
    if directory:
        if os.path.exists(directory):
            arr = os.listdir(directory)
            sorted_files = sorted(arr, key=lambda x: int(x.split('#')[len(x.split('#'))-1]))
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
                            row[5] = row[5].replace('\n', '')
                            row[0] = row[0].replace('.', '/')
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

                # components_mean = np.mean([float(c[version]) for c in list(metrics_by_directories.values())])
                # ANT
                name_version = version.replace('rel#','').replace('-','',1).replace('_','.').replace('#','-')
                # Lucene
                # name_version = version.replace('_','.').replace('#','/')
                architectural_quality = np.mean(components_mean)
                metrics.append([name_version, architectural_quality])

                # FIXME this is too naive and just work for this project. Should be fix soon.
                # Ant
                Tag.objects.filter(description__endswith=name_version, project=request.session['project']).update(
                    delta_rmd_components=architectural_quality)
                # Lucene
                # Tag.objects.filter(description__endswith=name_version,project=request.session['project']).update(delta_rmd_components=architectural_quality)

        # my_df_metrics = pd.DataFrame.from_dict(metrics, orient='index', columns=['version', 'y'])
        my_df_metrics = pd.DataFrame(metrics, columns=['versao', 'D'])
        my_df = pd.DataFrame(metrics_by_directories)
        print(my_df)
        my_df_metrics.to_csv('metrics_by_version.csv', index=True, index_label='idx', header=True)
        my_df.to_csv(directory.replace('/', '_') + '.csv', index=True, header=True)
    context = {
        'tag': tag,
    }
    return HttpResponse(template.render(context, request))

# values: [degradation, impactful commits, loc, degrad/loc]
def metrics_by_developer_csv(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    developers_metrics = ArchitecturalMetricsByCommit.objects.filter(commit__tag_id=file.tag.id)
    metrics = {}
    for info_developer in developers_metrics:
        if info_developer.project_individual_contribution.author not in metrics:
            metrics.setdefault(info_developer.project_individual_contribution.author, [info_developer.project_individual_contribution.experience_bf, 0.0, 0, 0])
        metrics[info_developer.project_individual_contribution.author][1] += info_developer.delta_rmd
        metrics[info_developer.project_individual_contribution.author][2] += info_developer.architecturally_impactful_commits
        metrics[info_developer.project_individual_contribution.author][3] += info_developer.architectural_impactful_loc
        # metrics[info_developer.developer][2] += info_developer.ratio_degrad_loc

    my_df = pd.DataFrame.from_dict(metrics, orient='index', columns=['Global XP (BF)', 'Degrad', 'Impactful Commit', 'Loc'])
    print(my_df)
    my_df.to_csv(file.directory + '/' + file.name.replace(file.directory,"").replace(".txt","") +'.csv', index=True, header=True)

    return HttpResponseRedirect(reverse('architecture:index', ))

################ Auxiliary methods ###################

# return a dictionary
# key: module (component)
# value: dictionary
#   key: commit
#   value: metrics (RMD)
# {"org.apache.ant": {"da5a13f8e4e0e4475f942b5ae5670271b711d423": 0.5565}, {"66c400defd2ed0bd492715a7f4f10e2545cf9d46": 0.0}}
def __read_PM_file__(folder,tag_id):
    metrics = {}
    tag = Tag.objects.get(id=tag_id)
    previous_commit = None
    start_commit_analysis_period = Commit.objects.all().first()
    first_commit_id = start_commit_analysis_period.pk

    ArchitecturalMetricsByCommit.objects.filter(commit__tag_id=tag_id).delete()
    Commit.objects.filter(tag_id=tag_id).update(mean_rmd_components=0.0, std_rmd_components=0.0, delta_rmd_components=0.0, normalized_delta=0.0)
    Directory.objects.filter(initial_commit__tag_id=tag_id).update(visible=False)
    Commit.objects.filter(changed_architecture=True, tag_id=tag_id).update(changed_architecture=False)
    analysis_period = None
    components_evolution = []
    n_commits = 0

    # To sort in natural order
    arr = os.listdir(folder)
    sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
    last_architectural_metric = None
    for subdirectory in sorted_files:
    # if subdirectory == 'version-89-8f30c476dd9095c50540b5fb96711d58fe8bf217' or subdirectory == 'version-91-64809d976e89e1dc36efd825772caf2b07c4f7da':
        # Commit.objects.filter(hash='651b15a3e54f2cdc486595962630c25061d20df5').update(mean_rmd_components=0.0, std_rmd_components=0.0, delta_rmd_components=0.0)
        subdirectory = os.path.join(folder, subdirectory)
        components_db = Directory.objects.filter(visible=True)
        components = []
        print("\n"+os.path.join(folder, subdirectory)+"\n----------------------\n")
        for filename in [f for f in os.listdir(subdirectory) if f.endswith(".csv")]:
            try:
                f = open(os.path.join(subdirectory, filename), "r")
                content = f.readlines()
                hash = f.name.split('\\')[1].split('-')[2]
                if Commit.objects.filter(hash=hash).count() > 0:
                    commit = Commit.objects.filter(hash=hash)[0]
                else:
                    continue
                commit_rmds = []
                new_metric = True
                if commit.parents and commit.parents[0] is not None:
                    previous_commit = commit.parents[0]
                else:
                    previous_commit = None

                for line in content[1:]:
                    row = line.split(',')
                    row[5]=row[5].replace('\n', '')
                    row[0] = row[0].replace('.','/')

                    # FIXME: Parametrizar
                    # prefix ='src/main/'
                    # prefix = 'lucene/core/src/java/'
                    # prefix = 'openjpa-kernel/src/main/java/'
                    # prefix = 'maven-core/src/main/java/'
                    directory_str = tag.main_directory_prefix + row[0]
                    directory = Directory.objects.filter(name__exact=directory_str)
                    if directory.count() == 0:
                        continue
                    directory = directory[0]

                    component_commit = ComponentCommit.objects.filter(commit=commit, component=directory)
                    if component_commit.exists():
                        component_commit = component_commit[0]
                    else:
                        component_commit = ComponentCommit.objects.filter(component=directory, commit_id__lte=commit.id,
                                                                          commit__author=commit.author).last()

                    # Change architecture
                    components.append(directory)

                    print(line.replace("\n",""))

                    architecture_metrics = ArchitecturalMetricsByCommit.objects.filter(
                        directory__name__exact=directory_str, commit_id=commit.id)
                    if architecture_metrics.count() == 0:
                        # TODO: use delta
                        architecture_metrics = ArchitecturalMetricsByCommit(component_commit=component_commit, commit=commit,
                                                                            directory=directory,
                                                                          rmd=float(row[5]), rma=float(row[4]),
                                                                          rmi=float(row[3]), ca=float(row[1]),
                                                                          ce=float(row[2]))
                    else:
                        architecture_metrics = architecture_metrics[0]
                        # new_metric = False
                    # Has ancestor and it is compilable
                    if previous_commit:
                        previous_architecture_metrics = ArchitecturalMetricsByCommit.objects.filter(directory_id=directory.id, commit_id=previous_commit.id)
                        if previous_architecture_metrics.count() > 0:
                            architecture_metrics.previous_architecture_quality_metrics = previous_architecture_metrics[0]
                            architecture_metrics.delta_rmd = architecture_metrics.rmd - architecture_metrics.previous_architecture_quality_metrics.rmd
                            if architecture_metrics.delta_rmd != 0 and round(architecture_metrics.delta_rmd, SCALE) == 0.0:
                                architecture_metrics.delta_rmd = 0.0
                    # Ancestor is not compilable
                    elif previous_commit and not previous_commit.compilable:
                        architecture_metrics.delta_rmd = 0.0
                    # It is an orphan commit
                    else:
                        # It is the initial commit in this component
                        if directory.initial_commit == commit:
                            architecture_metrics.delta_rmd = architecture_metrics.rmd
                        else:
                            architecture_metrics.delta_rmd = 0.0

                    if new_metric:
                        # Delta normalization by LOC changed
                        architecture_metrics.delta_rmd /= commit.u_cloc
                        architecture_metrics.delta_rmd = 0 if round(architecture_metrics.delta_rmd,SCALE) == 0.0 else architecture_metrics.delta_rmd
                        architecture_metrics.save()
                        directory.save()

                    commit_rmds.append([architecture_metrics.rmd, True if directory.initial_commit == commit else False])
            finally:
                f.close()

                if new_metric:

                    # FIXME: to prevent error. Shoud be fixed as soon as posible. It is not the right behaviour in all cases
                    if len(commit_rmds) > 0:
                        commit.mean_rmd_components = np.mean([c[0] for c in commit_rmds])
                        commit.std_rmd_components = np.std([c[0] for c in commit_rmds], ddof=1)
                        commit.delta_rmd_components = commit.mean_rmd_components

                    # Delta calculation
                    if previous_commit is not None and previous_commit.compilable and previous_commit.tag == commit.tag:
                        commit.delta_rmd_components -=previous_commit.mean_rmd_components
                        if round(commit.delta_rmd_components,SCALE) == 0.0:
                            commit.delta_rmd_components = 0
                    else:
                        commit.delta_rmd_components = 0.0

                    # Delta normalization by LOC changed
                    commit.normalized_delta = commit.delta_rmd_components/commit.u_cloc
                    if round(commit.normalized_delta, SCALE) == 0.0:
                        commit.normalized_delta = 0.0

                    removed_components = [x for x in list(components_db) if x not in components]
                    add_components = [x for x in components if x not in list(components_db)]
                    diff_components = removed_components + add_components
                    n_commits += 1
                    if len(diff_components) > 0:
                        components_evolution.append([n_commits, len(diff_components)])

                        if commit.pk != first_commit_id:
                            # n_commits = 0
                            commit.changed_architecture = True
                            if analysis_period is None:
                                analysis_period = AnalysisPeriod(start_commit=start_commit_analysis_period)
                            if last_architectural_metric is not None:
                                analysis_period.end_commit = last_architectural_metric.commit
                            else:
                                analysis_period.end_commit = commit
                            analysis_period.save()
                            start_commit_analysis_period = commit
                        analysis_period = AnalysisPeriod(start_commit=start_commit_analysis_period)
                        analysis_period.save()
                        commit.analysis_period = analysis_period
                        for a_component in diff_components:
                            if a_component.visible:
                                a_component.visible = False
                            else:
                                a_component.visible = True
                            a_component.save()
                    else:
                        components_evolution.append([n_commits, len(diff_components)])
                    commit.compilable = True
                    commit.save()
                    last_architectural_metric = architecture_metrics

    # my_df = pd.DataFrame(components_evolution, columns=['commits', 'diff_components'])
    # my_df.to_csv('diff_components_' + str(tag_id)+ '.csv', index=False, header=True)

    print(components_evolution)

    return metrics

def __create_files__(form, project_id):
    project = get_object_or_404(Project, pk=project_id)
    files=list_commits(project, form)
    return files

def __pre_correlation__(metrics, component):
    correlation = []
    # developers = list(metrics[component].keys()).values_list("committer__name", flat=True).distinct()
    developers = set([d.committer for d in list(metrics[component].keys())])
    tag = list(metrics[component].keys())[0].tag
    for developer in developers:
        # individual_metrics = __get_quality_contribution_by_developer__(metrics, component, developer, tag)
        individual_metrics = __get_quality_contribution_by_developer__(component, developer, tag)
        if individual_metrics is not None:
            correlation.append(individual_metrics)
    print(correlation)
    return correlation


def __get_quality_contribution_by_developer__(component, developer, tag):
    # Developer experience in this component
    full_component = 'src/main/'+component.replace(".", "/")
    directory = Directory.objects.filter(name__exact=full_component)
    if directory.count() == 0:
        return None
    directory = directory[0]
    contributor = IndividualContribution.objects.filter(author_id=developer.id, directory_report__directory=directory,
                                                       directory_report__tag_id=tag.id)
    global_contributor = ProjectIndividualContribution.objects.filter(author_id=developer.id, project_report__tag_id=tag.id)

    contributions = []
    if contributor.count() > 0 and global_contributor.count() > 0:
        contributor = contributor[0]
        global_contributor = global_contributor[0]
    else:
        return None

    metrics_by_developer = ArchitecturalMetricsByCommit.objects.filter(commit__author=global_contributor.author, commit__tag=tag, directory=directory)
    if metrics_by_developer.count() == 0:
        return None

    metrics_by_developer = metrics_by_developer[0]
    # Global XP, Specific XP, XP, Degradation, Loc, Degradation/Loc
    # xp = (8*global_contributor.experience_bf + 2*contributor.experience_bf)/10
    xp = global_contributor.experience_bf

    return [contributor.author.name, contributor.experience_bf, xp,
            metrics_by_developer.delta_rmd]

def list_commits(project,form):
    # Restricting to commits which has children
    # first_commit = Commit.objects.filter(children_commit__gt=0).first()
    FileCommits.objects.filter(tag__project=project).delete()
    folder = form['directory'].value()

    # commits = [i for i in list(Commit.objects.filter(id__gte=first_commit.id).order_by("id"))]
    commits = [i for i in list(Commit.objects.filter(tag__project=project).order_by("id"))]
    first_commit = commits[0]

    files = []

    if not os.path.exists(folder):
        os.mkdir(folder)
    j = first_commit.tag.description
    try:
        file = None
        j=j.replace("/","-")
        filename = "commits-" + j + ".txt"
        file = __update_file_commits__(form,filename)
        file.tag = first_commit.tag
        files.append(file)
        f = open(file.__str__(), 'w')
        myfile = File(f)
        myfile.write(form['git_local_repository'].value() + "\n")
        myfile.write(form['build_path'].value() + "\n")
        # myfile.write(ViewUtils.load_tag(request) + "\n")
        i = 1
        for commit in commits:

            commit_tag = commit.tag.description.replace("/","-")

            if j != commit_tag:
                myfile.closed
                f.closed
                file.save()
                i = 1
                j = commit_tag
                filename="commits-" + j + ".txt"
                file = __update_file_commits__(form,filename)
                file.tag = commit.tag
                f = open(file.__str__(), 'w')
                myfile = File(f)
                files.append(file)
                myfile.write(form['git_local_repository'].value() + "\n")
                myfile.write(form['build_path'].value() + "\n")
            myfile.write(str(i) + "-" + commit.hash + "\n")
            i += 1
        myfile.closed
        f.closed
        file.save()

        # files = [f for f in listdir(folder) if isfile(join(folder, f))]
    except Exception as e:
        print(e.args[0])
        files = []
    return files

def __generate_csv__(folder):
    current_project_path = os.getcwd()
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            if "PM.csv" not in os.listdir(folder) and filename.endswith(".jar"):
                # print(os.path.join(directory, filename))
                try:
                    arcan_metrics = subprocess.Popen('java -jar Arcan-1.2.1-SNAPSHOT.jar'
                                                     ' -p ' + folder + ' -out ' + folder + ' -pm -folderOfJars', cwd=current_project_path)
                    arcan_metrics.wait()
                except Exception as er:
                    print(er)
                    return False
                continue
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

def __has_jar_file__(directory):
    exists = False
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if exists:
                break
            if filename.endswith(".jar"):
                exists = True
    return exists


class ProcessException(object):
    pass


def execute(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Poll process for new output until finished
    while True:
        nextline = process.stdout.readline()
        if nextline == '' and process.poll() is not None:
            break
        sys.stdout.write(nextline)
        sys.stdout.flush()

    output = process.communicate()[0]
    exitCode = process.returncode

    if (exitCode == 0):
        return output
    else:
        raise ProcessException(command, exitCode, output)