import logging

from django.contrib import messages
from django.shortcuts import render
from django.views import View
from injector import inject

from architecture.forms import FilesCompiledForm
from architecture.models import FileCommits
from architecture.services import ArchitectureService
from contributions.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class ArchitectureListView(View):
    @inject
    def __init__(self, arch_service: ArchitectureService, project_repository: ProjectRepository):
        self.arch_service = arch_service
        self.project_repository = project_repository

    model = FileCommits
    template_name = 'architecture/index.html'
    context_object_name = 'file_commits'
    form_class = FilesCompiledForm

    context = {'title': 'Configuração do Projeto', 'form': form_class}

    def get(self, request):

        project_id = request.session['project']
        project = self.project_repository.find_by_primary_key(pk=project_id)

        files = FileCommits.objects.filter(tag__project=project).order_by("name")

        return render(request, self.template_name, {'files': files, **self.context})

    queryset = FileCommits.objects.all().order_by("name")

    def post(self, request):

        project_id = request.session['project']
        project = self.project_repository.find_by_primary_key(pk=project_id)

        # # create a form instance and populate it with data from the request:
        self.form_class = FilesCompiledForm(request.POST)

        # check whether it's valid:
        if self.form_class.is_valid:
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            files = self.arch_service.create_files(project_id)
            if files:
                messages.success(request, 'Files successfully created!')
            else:
                messages.error(request, 'Could not create files.')

        self.form_class = FilesCompiledForm(
            initial={'directory': 'compiled/' + project.project_name.lower().replace(' ', '-'),
                     'git_local_repository': 'G:/My Drive/MestradoUSP/programacao/projetos/git/ant',
                     'build_path': 'build/classes'})
        files = FileCommits.objects.filter(tag__project=project).order_by("name")

        context = {
            'files': files,
            'form': self.form_class,
            **self.context,
        }

        return render(request, self.template_name, context)


class ArchitecturalMetricsView(View):
    @inject
    def __init__(self, arch_service: ArchitectureService, project_repository: ProjectRepository):
        self.arch_service = arch_service
        self.project_repository = project_repository

    def post(self, request):
        print("")
