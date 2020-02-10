# standard library
import os
import re
import shutil
import subprocess
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
from architecture.forms import FilesCompiledForm
from architecture.models import ArchitecturalMetricsByCommit, FileCommits
from common.utils import ViewUtils
from contributions.models import (Commit, Developer, Directory,
                                  IndividualContribution, Project,
                                  ProjectIndividualContribution, Tag)


def index(request):
    """"Architecture Configuration"""
    tag = ViewUtils.load_tag(request)
    template = loader.get_template('architecture/index.html')
    files = []

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = FilesCompiledForm(request.POST)
        project_id = int(request.POST.get('project_id')) if request.POST.get('project_id') else 0

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
    else:
        form = FilesCompiledForm(initial={'directory': 'compiled',
                                          'git_local_repository': 'G:/My Drive/MestradoUSP/programacao/projetos/git/ant',
                                          'build_path': 'build/classes'})
        files = FileCommits.objects.all().order_by("name")

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
        os.chdir(file.local_repository)
        i = 0
        commit_with_errors = []
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
                        # Go to version
                        hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-','')
                        object_commit = Commit.objects.filter(hash=hash_commit)[0]
                        checkout = subprocess.Popen('git reset --hard ' + hash_commit + '', cwd=file.local_repository)
                        checkout.wait()
                        print(os.environ.get('JAVA_HOME'))

                        # Compile
                        build = subprocess.Popen('build.bat', shell=False, cwd=file.local_repository)
                        build.wait()

                        # Create jar
                        jar_folder = current_project_path + '/' + compiled_directory + '/version-' + commit.replace("/",
                                                                                                                    "").replace(
                            ".", "-")
                        jar_file = '"'+current_project_path+'/'+compiled_directory+'/'+ 'version-' + commit.replace("/","").replace(".","-") +'/version-' + commit.replace("/","").replace(".","-") + '.jar"'

                        os.makedirs(jar_folder, exist_ok=True)

                        input_files = "'"+file.local_repository+"/"+build_path+"'"
                        print("comando: jar -cf "+jar_file+" "+input_files )
                        process = subprocess.Popen('jar -cf ' + jar_file + ' ' + build_path, cwd=file.local_repository)
                        process.wait()

                        # Check whether created jar is valid
                        os.chdir(current_project_path)
                        jar = jar_file.replace(current_project_path,"").replace("/","",1).replace("\"","")
                        # 100 KB
                        if os.path.getsize(jar) < 102400:
                            os.chdir(current_project_path + '/' + compiled_directory)
                            folder = 'version-' + commit.replace("/","").replace(".","-")
                            commit_with_errors.append(commit.replace("/","").replace(".","-"))
                            shutil.rmtree(folder, ignore_errors=True)
                            print("BUILD FAILED or Jar creation failed\n")
                            print(jar+" DELETED\n")
                            # TODO: extract method
                            object_commit.compilable = False
                            object_commit.mean_rmd_components = 0.0
                            object_commit.std_rmd_components = 0.0
                            object_commit.delta_rmd_components = 0.0

                            os.chdir(file.local_repository)
                        else:
                            object_commit.compilable = True

                        object_commit.save()

                        build_path_repository = build_path
                        if build_path.count('\\') <= 1 and build_path.count('/') <= 1:
                            build_path_repository = file.local_repository + "/" + build_path
                        if os.path.exists(build_path_repository):
                            shutil.rmtree(build_path_repository)

                except OSError as e:
                    print("Error: %s - %s." % (e.filename, e.strerror))
                except Exception as er:
                    print(er)
                    messages.error(request, 'Erro: '+er)
                finally:

                    os.chdir(file.local_repository)
            i+=1
    except Exception as e:
        print(e)
        # shutil.rmtree(compiled_directory, ignore_errors=True)
        messages.error(request, 'Could not create compiled.')
    finally:
        os.chdir(current_project_path)
    if len(commit_with_errors) > 0:
        try:
            f = open(compiled_directory.replace("jars","")+"log-compilation-errors.txt", 'w')
            myfile = File(f)
            first = True
            myfile.write(local_repository+"\n")
            myfile.write(build_path+"\n")
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

# Using overall design evaluation
def impactful_commits(request):
    export_csv = (request.GET.get("export_csv") or request.POST.get("export_csv") == "true") if True else False
    # full_tag = (request.GET.get("until_tag") and request.POST.get("until_tag") == "true") if True else False

    full_tag = request.POST.get('until_tag')
    if not full_tag:
        if request.GET.get('until_tag') and request.GET.get('until_tag') == 'true':
            full_tag = True
        until_tag_state = ''

    directories = Directory.objects.filter(visible=True).order_by("name")
    developers = Developer.objects.all().order_by("name")
    commits = []
    directory_name = 'all'
    tag_name = 'tag-all'
    dev_name = 'dev-all'
    directory_filter = 0
    tag_filter = 0
    developer_filter = 0
    delta_check = ''

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
            tag_name = 'tag-' + Tag.objects.get(pk=tag_filter).description.replace('/', '_')

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
            query.setdefault('delta_rmd_components__gt', 0)
            delta_check = 'positive'
        elif request.POST.get('delta_rmd_components') == 'negative' or request.GET.get('delta_rmd_components') == 'negative':
            query.setdefault('delta_rmd_components__lt', 0)
            delta_check = 'negative'
        elif request.POST.get('delta_rmd') == 'negative' or request.GET.get('delta_rmd') == 'negative':
            query.setdefault('delta_rmd__lt', 0) if directory_filter > 0 else query.setdefault('delta_rmd_components__lt', 0)
            delta_check = 'negative'


        if directory_filter > 0:
            if 'delta_rmd__lt' in query or 'delta_rmd__gt' in query:
                commits = ArchitecturalMetricsByCommit.objects.filter(**query)
            else:
                commits = ArchitecturalMetricsByCommit.objects.exclude(delta_rmd=0).filter(**query)

            commits = sorted(commits, key=lambda x: x.commit.author_experience, reverse=False)
        else:
            if 'delta_rmd_components__lt' in query or 'delta_rmd_components__gt' in query:
                commits = Commit.objects.filter(**query)
            else:
                commits = Commit.objects.exclude(delta_rmd_components=0).filter(**query)
            commits = sorted(commits, key=lambda x: x.author_experience, reverse=False)

    if export_csv:

        if directory_filter > 0:
            metrics_dict = [[x.commit.author_experience,x.commit.delta_rmd, x.commit.tag.description, x.commit.directory.name] for x in commits]
        else:
            metrics_dict = [[x.author_experience, x.delta_rmd_components, x.tag.description] for x
                            in commits]

            # metrics_dict = []
            # for i, g in groupby(sorted(metrics_aux), key=lambda x: x[0]):
            #     metrics_dict.append([i, sum(v[1] for v in g)])

        if len(metrics_dict) > 0:
            if directory_filter > 0:
                my_df = pd.DataFrame(metrics_dict, columns=['x','y','tag','component'])
            else:
                my_df = pd.DataFrame(metrics_dict, columns=['x','y','tag'])

            my_df.to_csv(dev_name+'-'+directory_name+'_'+tag_name+'_delta-'+delta_check+'.csv', index=False, header=True)

            rho = my_df.corr(method='spearman')
            # ax = my_df.hist(column='x', bins=10, grid=False, figsize=(12, 8), color='#86bf91',
            #              zorder=2, rwidth=0.9)
            # my_df.boxplot(by='y', column=['x'], grid=False)
            # boxplot = my_df.boxplot(column=['x', 'y'])
            # boxplot = my_df.boxplot(column=['x'])
            # boxplot = my_df.boxplot(column=['y'])

            # sb.heatmap(rho,
            #             xticklabels=rho.columns,
            #             yticklabels=rho.columns)

            # s = sb.heatmap(rho,
            #            xticklabels=rho.columns,
            #            yticklabels=rho.columns,
            #            cmap='RdBu_r',
            #            annot=True,
            #            linewidth=0.5)

            # x=my_df.iloc[:,0]
            # y = my_df.iloc[:,1]
            # slope, intercept, r, p, stderr = scipy.stats.linregress(x, y)

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
        'until_tag_state': full_tag,
    }

    return HttpResponse(template.render(context, request))


# Using individual component evaluation
def old_impactful_commits(request):
    export_csv = (request.GET.get("export_csv") and request.GET.get("export_csv") == "true") if True else False

    directories = Directory.objects.filter(visible=True).order_by("name")
    developers = Developer.objects.all().order_by("name")
    metrics = []
    directory_name = 'all'
    tag_name = 'tag-all'
    dev_name = 'dev-all'
    directory_filter = 0
    tag_filter = 0
    developer_filter = 0
    delta_check = ''

    query = {}

    if request.POST.get('directory_id') or request.GET.get('directory_id'):
        directory_filter = int(request.POST.get('directory_id')) if request.POST.get('directory_id') else int(request.GET.get('directory_id'))
        if directory_filter > 0:
            query.setdefault('directory_id', directory_filter)
            directory_name = Directory.objects.get(pk=directory_filter).name.replace('/', '_')

    if request.POST.get('tag_id') or request.GET.get('tag_id'):
        tag_filter = int(request.POST.get('tag_id')) if request.POST.get('tag_id') else int(request.GET.get('tag_id'))
        if tag_filter > 0:
            query.setdefault('commit__tag_id', tag_filter)
            tag_name = 'tag-' + Tag.objects.get(pk=tag_filter).description.replace('/', '_')

    if request.POST.get('developer_id') or request.GET.get('developer_id'):
        developer_filter = int(request.POST.get('developer_id')) if request.POST.get('developer_id') else int(request.GET.get('developer_id'))
        if developer_filter > 0:
            query.setdefault('commit__author_id', developer_filter)
            dev_name = Developer.objects.get(pk=developer_filter).name.split(' ')[0].lower()

    if len(query) > 0:
        if request.POST.get('delta_rmd') == 'positive' or request.GET.get('delta_rmd') == 'positive':
            query.setdefault('delta_rmd__gt', 0)
            delta_check = 'positive'
        elif request.POST.get('delta_rmd') == 'negative' or request.GET.get('delta_rmd') == 'negative':
            query.setdefault('delta_rmd__lt', 0)
            delta_check = 'negative'

        if 'delta_rmd__lt' in query or 'delta_rmd__gt' in query:
            metrics = ArchitecturalMetricsByCommit.objects.filter(**query)
        else:
            metrics = ArchitecturalMetricsByCommit.objects.exclude(delta_rmd=0).filter(**query)

    metrics = sorted(metrics, key=lambda x: x.commit.author_experience, reverse=False)

    if export_csv:

        if directory_filter > 0:
            metrics_dict = [[x.commit.author_experience,x.delta_rmd, x.commit.tag.description, x.directory.name] for x in metrics]
        else:
            metrics_aux = [[x.commit.author_experience, x.delta_rmd, x.commit.tag.description] for x
                            in metrics]

            metrics_dict = []
            for i, g in groupby(sorted(metrics_aux), key=lambda x: x[0]):
                metrics_dict.append([i, sum(v[1] for v in g)])

        if len(metrics_dict) > 0:
            # my_df = pd.DataFrame(metrics_dict, columns=['x','y','tag','component'])
            my_df = pd.DataFrame(metrics_dict)

            my_df.to_csv(dev_name+'-'+directory_name+'_'+tag_name+'_delta-'+delta_check+'.csv', index=False, header=False)

            rho = my_df.corr(method='spearman')
            # hist = my_df.hist(bins=3)
            # ax = my_df.hist(column='x', bins=10, grid=False, figsize=(12, 8), color='#86bf91',
            #              zorder=2, rwidth=0.9)
            # my_df.boxplot(by='y', column=['x'], grid=False)

            # sb.heatmap(rho,
            #             xticklabels=rho.columns,
            #             yticklabels=rho.columns)

            # s = sb.heatmap(rho,
            #            xticklabels=rho.columns,
            #            yticklabels=rho.columns,
            #            cmap='RdBu_r',
            #            annot=True,
            #            linewidth=0.5)

            # x=my_df.iloc[:,0]
            # y = my_df.iloc[:,1]
            # slope, intercept, r, p, stderr = scipy.stats.linregress(x, y)

    template = loader.get_template('architecture/impactful_commits.html')
    context = {

        'metrics': metrics,
        'current_directory_id': directory_filter,
        'current_tag_id': tag_filter,
        'current_developer_id': developer_filter,
        'directories': directories,
        'developers': developers,
        'delta_check': delta_check,
    }

    return HttpResponse(template.render(context, request))

# def export_to_csv_metrics(request):
#     project = Project.objects.get(project_name="Apache Ant")
#     tag = ViewUtils.load_tag(request)
#
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename='+ project.project_name +'"-metrics.csv"'
#     # writer = csv.writer(response)
#     pd.DataFrame(contributions)
#
#
#     writer.writerow(["Classificacao de desenvolvedores por experiencia"])
#     writer.writerow([""])
#
#     return response

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
                    object_commit = Commit.objects.filter(hash=hash_commit)[0]
                    object_commit.compilable = False
                    object_commit.mean_rmd_components = 0.0
                    object_commit.std_rmd_components = 0.0
                    object_commit.delta_rmd_components = 0.0
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
    if directory:
        if os.path.exists(directory):
            arr = os.listdir(directory)
            sorted_files = sorted(arr, key=lambda x: int(x.split('-')[2]))
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
        my_df = pd.DataFrame(metrics_by_directories)
        print(my_df)
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
    collected_data = []

    previous_commit = None

    # To sort in natural order
    arr = os.listdir(folder)
    sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
    last_commit = None
    for subdirectory in sorted_files:
        subdirectory = os.path.join(folder, subdirectory)
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

                    directory = Directory.objects.filter(name__exact='src/main/' + row[0], visible=True)
                    if directory.count() == 0:
                        continue
                    directory = directory[0]
                    # if not commit.has_files_in_this_directory(directory):
                    #     continue

                    print(line.replace("\n",""))

                    architecture_metrics = ArchitecturalMetricsByCommit.objects.filter(
                        directory__name__exact='src/main/' + row[0], commit_id=commit.id)
                    if architecture_metrics.count() == 0:
                        # TODO: use delta
                        architecture_metrics = ArchitecturalMetricsByCommit(commit=commit, directory=directory,
                                                                          rmd=float(row[5]), rma=float(row[4]),
                                                                          rmi=float(row[3]), ca=float(row[1]),
                                                                          ce=float(row[2]))
                    else:
                        architecture_metrics = architecture_metrics[0]
                        new_metric = False
                    if row[0] not in metrics:
                        metrics.setdefault(row[0],{})
                    if previous_commit and previous_commit in metrics[row[0]]:
                        previous_architecture_quality_metrics = ArchitecturalMetricsByCommit.objects.filter(directory_id=directory.id, commit_id=previous_commit.id)
                        if previous_architecture_quality_metrics.count() > 0:
                            architecture_metrics.previous_architecture_quality_metrics = previous_architecture_quality_metrics[0]
                        delta = float(row[5]) - float(metrics[row[0]][previous_commit][0])
                    elif not previous_commit:
                        delta = 0.0
                    else:
                        delta = float(row[5])
                    if hasattr(architecture_metrics, 'pk') and architecture_metrics.pk is None:
                        architecture_metrics.save()

                    # commit_rmds.append(architecture_metrics.rmd)
                    commit_rmds.append([architecture_metrics.rmd, True if directory.initial_commit == commit else False])

                    metrics[row[0]].setdefault(commit, [row[5], delta])

                    collected_data.append([commit.committer.id, delta])
            finally:
                f.close()
                # commit_rmds = ArchitecturalMetricsByCommit.objects.filter(commit=commit).distinct().values_list("rmd", flat=True)

                # commit_rmds = [c.rmd for c in ]

                if new_metric:

                    commit.mean_rmd_components = np.mean([c[0] for c in commit_rmds])
                    commit.std_rmd_components = np.std([c[0] for c in commit_rmds], ddof=1)
                    commit.delta_rmd_components = commit.mean_rmd_components

                    # if previous_commit is None and directory.initial_commit == commit:
                    #     commit_rmds.append(architecture_metrics.rmd)
                    # else:
                    #     commit_rmds.append(0.0)
                    if previous_commit is not None and previous_commit.compilable:
                        commit.delta_rmd_components -=previous_commit.mean_rmd_components
                    elif (previous_commit is not None and not previous_commit.compilable) and (last_commit is not None and last_commit.author == commit.author):
                        commit.delta_rmd_components -= last_commit.mean_rmd_components
                    elif any(True == c[1] for c in commit_rmds):
                        commit.delta_rmd_components = np.mean([c[0] for c in commit_rmds if c[1] == True])
                    else:
                        commit.delta_rmd_components = 0.0

                    commit.delta_rmd_components/=commit.u_cloc

                    commit.save()
                last_commit = commit
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
    full_component = 'src/main/'+component.replace(".","/")
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
    folder = form['directory'].value()

    # commits = [i for i in list(Commit.objects.filter(id__gte=first_commit.id).order_by("id"))]
    commits = [i for i in list(Commit.objects.all().order_by("id"))]
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
                continue
            else:
                continue

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
