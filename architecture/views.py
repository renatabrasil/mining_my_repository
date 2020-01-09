import json
import os
import shutil
import subprocess
import re
import matplotlib.pyplot as plt
from collections import OrderedDict

import pandas as pd
from django.contrib import messages
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404

# Create your views here.
from django.template import loader
from django.urls import reverse

from architecture.forms import FilesCompiledForm
from architecture.models import FileCommits, ArchitecturalMetricsByCommit
from common.utils import ViewUtils
from contributions.models import Project, Commit, Developer, IndividualContribution, ProjectIndividualContribution, \
    Directory


def index(request):
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
                        if os.path.getsize(jar) < 3080:
                            os.chdir(current_project_path + '/' + compiled_directory)
                            folder = 'version-' + commit.replace("/","").replace(".","-")
                            commit_with_errors.append(commit.replace("/","").replace(".","-"))
                            shutil.rmtree(folder, ignore_errors=True)
                            print("BUILD FAILED or Jar creation failed\n")
                            print(jar+" DELETED\n")

                            os.chdir(file.local_repository)

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

def impactful_commits(request):
    template = loader.get_template('architecture/impactful_commits.html')

    metrics = []

    metrics = [c for c in ArchitecturalMetricsByCommit.objects.all() if c.delta_rmd > 0]


    context = {

        'metrics': metrics,

    }

    return HttpResponse(template.render(context, request))

def calculate_metrics(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt", "")
    metrics_directory = directory_name+"/metrics"
    if not os.path.exists(metrics_directory):
        os.makedirs(metrics_directory, exist_ok=True)
    directory_name = directory_name + "/jars"
    metrics = __read_PM_file__(directory_name)
    directories = metrics.keys()
    for directory in directories:
        contributions = __pre_correlation__(metrics, directory)
        if contributions:
            my_df = pd.DataFrame(contributions)
            my_df.columns = ["Developer", "Global XP", "Specific XP", "XP (8/2)", "Degrad Delta", "Impactful commits", "Loc"]
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
def __read_PM_file__(folder):
    metrics = {}
    collected_data = []
    previous_commit = None
    # To sort in natural order
    arr = os.listdir(folder)
    sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
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
                    if not commit.has_files_in_this_directory(directory):
                        continue

                    print(line.replace("\n",""))

                    architecture_metrics = ArchitecturalMetricsByCommit.objects.filter(
                        directory__name__exact='src/main/' + row[0], commit_id=commit.id)
                    if architecture_metrics.count() == 0:
                        # TODO: use delta
                        architecture_metrics = ArchitecturalMetricsByCommit(commit=commit, directory=directory,
                                                                          rmd=float(row[5]), rma=float(row[4]),
                                                                          rmi=float(row[3]), ca=float(row[1]),
                                                                          ce=float(row[2]))
                    if row[0] not in metrics:
                        metrics.setdefault(row[0],{})
                    if previous_commit and previous_commit in metrics[row[0]]:
                        if hasattr(architecture_metrics, 'pk') and architecture_metrics.pk is None:
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

                    metrics[row[0]].setdefault(commit, [row[5], delta])

                    collected_data.append([commit.committer.id, delta])
            finally:
                f.close()
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

    metrics_by_developer = ArchitecturalMetricsByCommit.objects.filter(commit__author=global_contributor, commit__tag=tag, directory=directory)
    if metrics_by_developer.count() == 0:
        return None

    metrics_by_developer = metrics_by_developer[0]
    # Global XP, Specific XP, XP, Degradation, Loc, Degradation/Loc
    xp = (8*global_contributor.experience_bf + 2*contributor.experience_bf)/10

    return [metrics_by_developer.project_individual_contribution.author.name,
            metrics_by_developer.project_individual_contribution.experience_bf, contributor.experience_bf, xp,
            metrics_by_developer.delta_rmd, metrics_by_developer.architecturally_impactful_commits,
            metrics_by_developer.architectural_impactful_loc]

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