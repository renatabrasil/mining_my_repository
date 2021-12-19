import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
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

        project = self.project_repository.find_by_primary_key(pk=request.session['project'])
        files = FileCommits.objects.filter(tag__project=project).order_by("name")

        return render(request, self.template_name, {'files': files, **self.context})

    def post(self, request):

        project_id = request.session['project']
        project = self.project_repository.find_by_primary_key(pk=project_id)

        # # create a form instance and populate it with data from the request:
        self.form_class = FilesCompiledForm(request.POST)

        # check whether it's valid:
        if self.form_class.is_valid:

            files = self.arch_service.create_files(project_id)
            if files:
                messages.success(request, 'Files successfully created!')
            else:
                messages.error(request, 'Could not create files.')

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

    def get(self, request, file_id):
        self.arch_service.compile_commits(file_id)

        return HttpResponseRedirect(reverse('architecture:index', ))
