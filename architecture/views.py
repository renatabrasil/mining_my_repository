import os
import shutil
import subprocess
import re
import csv
from collections import OrderedDict

from django.contrib import messages
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.template import loader
from django.urls import reverse

import architecture
from architecture.forms import FilesCompiledForm
from architecture.models import Compiled, FileCommits, ArchitectureQualityMetrics, ArchitectureQualityByDeveloper
from common.utils import ViewUtils
from contributions.models import Project, Commit, Developer, IndividualContribution, ProjectIndividualContribution, \
    Directory


def index(request):
    tag = ViewUtils.load_tag(request)
    # latest_question_list = Question.objects.order_by('-pub_date')[:5]
    template = loader.get_template('architecture/index.html')
    files = []
    # if 'files' in request.session:
    #     files = request.session['files']
    #     del request.session['files']

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = FilesCompiledForm(request.POST)
        project_id = int(request.POST.get('project_id')) if request.POST.get('project_id') else 0

        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            files = create_files(form, project_id)
            if files:
                messages.success(request, 'Files successfully created!')
            else:
                messages.error(request, 'Could not create files.')

            # HttpResponseRedirect(reverse('architecture:index',))
        # if a GET (or any other method) we'll create a blank form
    else:
        form = FilesCompiledForm(initial={'directory': 'compiled',
                                          'git_local_repository': 'G:/My Drive/MestradoUSP/programacao/projetos/git/ant',
                                          'build_path': 'build'})
        # files = FileCommits.objects.filter(directory='compiled', build_path='build')
        files = FileCommits.objects.all().order_by("name")

    context = {
        'tag': tag,
        'files': files,
        'form': form,
        # 'latest_question_list': latest_question_list,
    }

    return HttpResponse(template.render(context, request))


def results(request, project_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % project_id)

def build_compileds(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    current_project_path = os.getcwd()
    try:
        f = open(file.__str__(), 'r')
        myfile = File(f)
        previous_commit = None
        compiled_directory = file.directory+"/"+file.name.replace(".txt","")+"/jars"
        if not os.path.exists(compiled_directory):
            os.makedirs(compiled_directory, exist_ok=True)
        os.chdir(file.local_repository)
        # FIX: if we are using local repository as entry point
        # if not os.path.exists("jars"):
        #     os.mkdir("jars")
        i = 0
        # bootstrap = subprocess.Popen('bootstrap.bat', shell=False, cwd=file.local_repository)
        # bootstrap.wait()
        for commit in myfile:
            commit = commit.replace('\n','')
            if i==0:
                local_repository = commit
            elif i==1:
                build_path = commit
            else:
                try:
                    # Ir para a versao
                    # checkout = subprocess.Popen('git reset --hard '+commit, cwd=file.local_repository)
                    hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', commit).group(0).replace('-','')
                    checkout = subprocess.Popen('git reset --hard ' + hash_commit + '', cwd=file.local_repository)
                    checkout.wait()
                    print(os.environ.get('JAVA_HOME'))

                    # compilar
                    # TODO: Check whether it is a successfull action.
                    build = subprocess.Popen('build.bat', shell=False, cwd=file.local_repository)
                    build.wait()
                    # stdout, stderr = build.communicate()

                    # criar o jar
                    # index = re.search(r'[^-*/+-]+', commit).group(0)
                    jar_folder = current_project_path + '/' + compiled_directory + '/version-' + commit.replace("/",
                                                                                                                "").replace(
                        ".", "-")
                    jar_file = '"'+current_project_path+'/'+compiled_directory+'/'+ 'version-' + commit.replace("/","").replace(".","-") +'/version-' + commit.replace("/","").replace(".","-") + '.jar"'

                    os.makedirs(jar_folder, exist_ok=True)
                    # m = re.search(r'[^-*/+-]+', commit).group(0)
                    input_files = "'"+file.local_repository+"/"+build_path+"'"
                    print("comando: jar -cf "+jar_file+" "+input_files )
                    # FIX: create on local repository folder
                    # subprocess.Popen("jar -cf "+jar_file+" "+build_path, cwd=file.local_repository)
                    process = subprocess.Popen('jar -cf ' + jar_file + ' ' + build_path, cwd=file.local_repository)
                    process.wait()

                    build_path_repository = build_path
                    if build_path.count('\\')==0 and build_path.count('/')==0:
                        build_path_repository = file.local_repository+"/"+build_path
                    if os.path.exists(build_path_repository):
                        shutil.rmtree(build_path_repository)


                except Exception as er:
                    print(er)
                    messages.error(request, 'Erro: '+er)

            i+=1
            # subprocess.run(["jar", "-cf", commit+".jar", ""])
            # compiled = Compiled(file=file, name="1"+commit, hash_commit=commit, previous_compiled=previous_commit)
            # compiled.save()
            previous_commit = commit
    except Exception as e:
        print(e)
        shutil.rmtree(compiled_directory, ignore_errors=True)
        messages.error(request, 'Could not create compiled.')
    finally:
        os.chdir(current_project_path)
    file.has_compileds=True
    file.save()

    return HttpResponseRedirect(reverse('architecture:index',))

def calculate_metrics(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt", "")
    directory_name = directory_name + "/jars"
    metrics = read_PM_file(directory_name)
    directories = metrics.keys()
    for directory in directories:
        contributions = pre_correlation(metrics, directory)
        with open(directory.replace('/','_')+'.csv', 'w') as csvFile:
            writer = csv.writer(csvFile)
            for contribution in contributions:
                writer.writerow(contribution)
        csvFile.close()
    return HttpResponseRedirect(reverse('architecture:index', ))

def calculate_architecture_metrics(request, file_id):
    file = FileCommits.objects.get(pk=file_id)
    directory_name = file.__str__().replace(".txt","")
    directory_name = directory_name+"/jars"
    if os.path.exists(directory_name):
        for filename in os.listdir(directory_name):
            generate_csv(directory_name+"/"+filename)
    return HttpResponseRedirect(reverse('architecture:index',))

def generate_csv(folder):
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


# return a dictionary
# key: module (component)
# value: dictionary
#   key: commit
#   value: metrics (RMD)
# {"org.apache.ant": {"da5a13f8e4e0e4475f942b5ae5670271b711d423": 0.5565}, {"66c400defd2ed0bd492715a7f4f10e2545cf9d46": 0.0}}
def read_PM_file(folder):
    metrics = {}
    collected_data = []
    previous_commit = None
    for dirpath, dirnames, filenames in os.walk(folder):
        for filename in [f for f in filenames if f.endswith(".csv")]:
            print(os.path.join(dirpath, filename))
            try:
                f = open(os.path.join(dirpath, filename), "r")
                content = f.readlines()
                hash = f.name.split('\\')[1].split('-')[2]
                if Commit.objects.filter(hash=hash).count() > 0:
                    commit = Commit.objects.filter(hash=hash)[0]
                else:
                    continue

                architecture_metrics = None
                for line in content[2:]:
                    print(line)
                    row = line.split(',')
                    row[5]=row[5].replace('\n', '')
                    row[0] = row[0].replace('.','/')

                    architecture_metrics = ArchitectureQualityMetrics.objects.filter(
                        architecture_quality_by_developer_and_directory__directory__name__exact='src/main/' + row[0], commit_id=commit.id)
                    if architecture_metrics.count() == 0:
                        directory = Directory.objects.filter(name__exact='src/main/' + row[0])
                        directory = directory[0]

                        architecture_quality_by_developer = ArchitectureQualityByDeveloper.objects.filter(tag_id=commit.tag.id, directory_id=directory.id,
                                                                      developer_id=commit.committer.id)
                        if architecture_quality_by_developer.count() > 0:
                            architecture_quality_by_developer=architecture_quality_by_developer[0]
                        else:
                            architecture_quality_by_developer = ArchitectureQualityByDeveloper(developer=commit.committer,
                                                                                               directory=directory,
                                                                                               tag=commit.tag)
                            architecture_quality_by_developer.save()

                        # TODO: use delta
                        architecture_metrics = ArchitectureQualityMetrics(commit=commit,
                                                                          architecture_quality_by_developer_and_directory=architecture_quality_by_developer,
                                                                          rmd=float(row[5]), rma=float(row[4]),
                                                                          rmi=float(row[3]), ca=float(row[1]),
                                                                          ce=float(row[2]))
                    # else:
                    #     architecture_metrics = architecture_metrics[0]

                    if row[0] not in metrics:
                        metrics.setdefault(row[0],{})
                    if previous_commit and previous_commit in metrics[row[0]]:
                        if hasattr(architecture_metrics, 'pk') and architecture_metrics.pk is None:
                            previous_architecture_quality_metrics = ArchitectureQualityMetrics.objects.filter(architecture_quality_by_developer_and_directory__directory_id=directory.id, commit_id=previous_commit.id)
                            if previous_architecture_quality_metrics.count() > 0:
                                architecture_metrics.previous_architecture_quality_metrics = previous_architecture_quality_metrics[0]
                        delta = float(row[5]) - float(metrics[row[0]][previous_commit][0])
                    elif not previous_commit:
                        delta = 0.0
                    else:
                        delta = float(row[5])
                    if hasattr(architecture_metrics, 'pk') and architecture_metrics.pk is None:
                        architecture_metrics.save()
                    # architecture_metrics.rmd = delta
                    metrics[row[0]].setdefault(commit, [row[5], delta])

                    collected_data.append([commit.committer.id, delta])


                previous_commit = commit
            finally:
                f.close()
    return metrics

def create_files(form, project_id):
    project = get_object_or_404(Project, pk=project_id)
    files=list_commits(project, form)
    return files

def pre_correlation(metrics, component):
    correlation = []
    # developers = list(metrics[component].keys()).values_list("committer__name", flat=True).distinct()
    developers = set([d.committer for d in list(metrics[component].keys())])
    tag = list(metrics[component].keys())[0].tag
    for developer in developers:
        correlation.append(get_quality_contribution_by_developer(metrics, component, developer, tag))
    print(correlation)
    return correlation

def get_quality_contribution_by_developer(metrics, component, developer, tag):
    # Developer experience in this component
    full_component = 'src/main/'+component.replace(".","/")
    contributor = IndividualContribution.objects.filter(author_id=developer.id, directory_report__directory__name__exact=full_component,
                                                       directory_report__tag_id=tag.id)
    global_contributor = ProjectIndividualContribution.objects.filter(author_id=developer.id, project_report__tag_id=tag.id)
    contributions = []
    if contributor.count() > 0 and global_contributor.count() > 0:
        contributor = contributor[0]
        global_contributor = global_contributor[0]
    else:
        return [0,0,0,0]

    contributions_pairs = {}
    delta = 0.0
    for commit, metric in metrics[component].items():
        if commit.committer == developer:
            delta += float(metric[1])
        # if commit not in contributions_pairs:
        #     contributions_pairs.setdefault()

    return [contributor.author.name, global_contributor.experience, contributor.experience, delta]

def list_commits(project,form):
    first_commit = Commit.objects.filter(children_commit__gt=0).first()
    folder = form['directory'].value()

    commits = [i for i in list(Commit.objects.filter(id__gte=first_commit.id).order_by("id"))]
    files = []

    if not os.path.exists(folder):
        os.mkdir(folder)
    j = first_commit.tag.description
    try:
        file = None
        j=j.replace("/","-")
        filename = "commits-" + j + ".txt"
        file = __update_file_commits__(form,filename)
        file.project = project
        files.append(file)
        f = open(file.__str__(), 'w')
        myfile = File(f)
        myfile.write(form['git_local_repository'].value() + "\n")
        myfile.write(form['build_path'].value() + "\n")
        # myfile.write(ViewUtils.load_tag(request) + "\n")
        i = 1
        for commit in commits:
            myfile.write(str(i)+"-"+commit.hash+"\n")
            commit_tag = commit.tag.description.replace("/","-")
            i += 1
            if j != commit_tag:
                myfile.closed
                f.closed
                file.save()
                i = 1
                j = commit_tag
                filename="commits-" + j + ".txt"
                file = __update_file_commits__(form,filename)
                file.project = project
                f = open(file.__str__(), 'w')
                myfile = File(f)
                files.append(file)
                myfile.write(form['git_local_repository'].value() + "\n")
                myfile.write(form['build_path'].value() + "\n")
        myfile.closed
        f.closed
        file.save()

        # files = [f for f in listdir(folder) if isfile(join(folder, f))]
    except Exception as e:
        print(e.args[0])
        files = []
    return files

def architecture_metrics(request):
    # ArchitectureQualityMetrics.objects.filter(commit__tag_id=tag)
    directories = Directory.objects.filter(visible=True).order_by("name")
    template = loader.get_template('architecture/architecture_metrics_by_directories.html')
    tag = ViewUtils.load_tag(request)
    # architectural_metrics_list = ArchitectureQualityMetrics.objects.filter(commit__tag_id=tag)
    architectural_metrics_list = []

    directories_filter = None
    if request.POST.get('directory_id'):
        directories_filter = request.POST.get('directory_id')
        # directories_filter = Directory.objects.get(pk=directories_filter)
        if request.POST.get('developer_id'):
            architectural_metrics_list = ArchitectureQualityByDeveloper.objects.filter(directory_id=int(directories_filter),
                                                                                       developer_id=int(request.POST.get('developer_id')),
                                                                                       tag_id=tag)
            # architectural_metrics_list = ArchitectureQualityMetrics.objects.filter(directory_id=int(directories_filter),
            #                                                                        commit__author_id=int(request.POST.get('developer_id')),
            #                                                                        commit__tag_id=tag)
        else:
            architectural_metrics_list = ArchitectureQualityByDeveloper.objects.filter(directory_id=int(directories_filter),tag_id=tag)

    results = OrderedDict()
    for metric in architectural_metrics_list:
        if metric.directory not in results:
            results.setdefault(metric.directory, list())
        results[metric.directory] += metric.metrics.all()
    context = {
        'tag': tag,
        'results': results,
        'directories': directories,
    }

    return HttpResponse(template.render(context, request))

def architecture_metrics_by_developer(request):
    template = loader.get_template('architecture/architecture_metrics_by_developer.html')
    tag = ViewUtils.load_tag(request)
    architectural_metrics_list = []
    developer = None
    if request.POST.get('developer_id'):
        developer_id = int(request.POST.get('developer_id'))
        developer = Developer.objects.get(pk=developer_id)
        architectural_metrics_list = ArchitectureQualityByDeveloper.objects.filter(developer_id=developer_id,
                                                                                   tag_id=tag.id)
    context = {
        'tag': tag,
        'results': architectural_metrics_list,
        'current_developer': developer,
    }
    return HttpResponse(template.render(context, request))

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