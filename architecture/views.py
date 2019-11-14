import os
import shutil
import subprocess

from django.contrib import messages
from django.core.files import File
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.template import loader
from django.urls import reverse

import architecture
from architecture.forms import FilesCompiledForm
from architecture.models import Compiled, FileCommits
from common.utils import ViewUtils
from contributions.models import Project, Commit


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
        files = FileCommits.objects.filter(directory='compiled', build_path='build')

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
                    checkout = subprocess.Popen('git reset --hard ' + commit + '', cwd=file.local_repository)
                    checkout.wait()
                    print(os.environ.get('JAVA_HOME'))

                    # compilar
                    build = subprocess.Popen('build.bat', shell=False, cwd=file.local_repository)
                    build.wait()
                    # stdout, stderr = build.communicate()

                    # criar o jar
                    jar_file = '"'+current_project_path+'/'+compiled_directory+'/version-' + commit.replace("/","").replace(".","-") + '.jar"'
                    input_files = "'"+file.local_repository+"/"+build_path+"'"
                    print("comando: jar -cf "+jar_file+" "+input_files )
                    # FIX: create on local repository folder
                    # subprocess.Popen("jar -cf "+jar_file+" "+build_path, cwd=file.local_repository)
                    process = subprocess.Popen('jar -cf ' + jar_file + ' ' + build_path, cwd=file.local_repository)
                    process.wait()

                    if os.path.exists(file.local_repository+"/"+build_path):
                        shutil.rmtree(file.local_repository+"/"+build_path)

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


def create_files(form, project_id):
    project = get_object_or_404(Project, pk=project_id)
    files=list_commits(project, form)
    return files


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
        for commit in commits:
            myfile.write(commit.hash+"\n")
            commit_tag = commit.tag.description.replace("/","-")
            if j != commit_tag:
                myfile.closed
                f.closed
                file.save()
                j = commit_tag
                filename="commits-" + j + ".txt"
                file = __update_file_commits__(form,filename)
                file.project = project
                f = open(file.__str__(), 'w')
                myfile = File(f)
                files.append(file)
        myfile.closed
        f.closed
        file.save()

        # files = [f for f in listdir(folder) if isfile(join(folder, f))]
    except Exception as e:
        print(e.args[0])
        files = []
    return files

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