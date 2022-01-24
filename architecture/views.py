import logging

from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template import loader
from django.urls import reverse
from django.views import View
from injector import inject

from architecture.forms import FilesCompiledForm
from architecture.models import FileCommits
from architecture.services import ArchitectureService
from common.constants import CommonsConstantsUtils
from contributions.models import Commit
from contributions.repositories.project_repository import ProjectRepository

logger = logging.getLogger(__name__)


class ArchitectureListView(View):
    @inject
    def __init__(self, arch_service: ArchitectureService, project_repository: ProjectRepository):
        self.arch_service = arch_service
        self.project_repository = project_repository
        self.logger = logging.getLogger(__name__)

    model = FileCommits
    template_name = 'architecture/index.html'
    context_object_name = 'file_commits'
    form_class = FilesCompiledForm

    context = {'title': 'Configuração do Projeto', 'form': form_class}

    def get(self, request):

        logger.info('[VIEW] - Display Project Settings form')

        project = self.project_repository.find_by_primary_key(pk=request.session['project'])
        files = FileCommits.objects.filter(tag__project=project).order_by("name")

        return render(request, self.template_name, {'files': files, **self.context})

    def post(self, request):
        logger.info('[VIEW] - Starting Project Settings')

        project_id = request.session['project']
        project = self.project_repository.find_by_primary_key(pk=project_id)

        # # create a form instance and populate it with data from the request:
        self.form_class = FilesCompiledForm(request.POST)

        # check whether it's valid:
        if self.form_class.is_valid:
            logger.info('[x] Form is valid')
            files = self.arch_service.create_files(request, project_id)
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

        logger.info('[VIEW] - Finishing Project Settings')
        return render(request, self.template_name, context)


class ArchitecturalMetricsView(View):
    @inject
    def __init__(self, arch_service: ArchitectureService, project_repository: ProjectRepository):
        self.arch_service = arch_service
        self.project_repository = project_repository
        self.logger = logging.getLogger(__name__)

    def get(self, request, file_id):
        self.logger.info(f'[VIEW] Starting calculate metrics and impactful commits ...')

        path = request.path.split(CommonsConstantsUtils.PATH_SEPARATOR)[2]

        if path == 'compileds':
            self.arch_service.compile_commits(request, file_id)
        elif path == 'extract_metrics_csv':
            self.arch_service.extract_and_calculate_architecture_metrics(request, file_id)
        elif path == 'metrics':
            self.arch_service.calculate_metrics(request, file_id)

        self.logger.info('[VIEW] Done calculate metrics and impactful commits ...')
        return HttpResponseRedirect(reverse('architecture:index', ))


class ImpactfulCommitsMetricsView(View):
    model = Commit
    template_name = 'architecture/impactful_commits.html'

    @inject
    def __init__(self, arch_service: ArchitectureService, project_repository: ProjectRepository):
        self.arch_service = arch_service
        self.project_repository = project_repository

    def post(self, request):
        context = self.arch_service.filter_impactful_commits(request, request.POST)

        template = loader.get_template(self.template_name)

        # if directory_filter > 0:
        #     template = loader.get_template('architecture/old_impactful_commits.html')
        # else:
        #     template = loader.get_template('architecture/impactful_commits.html')

        return HttpResponse(template.render(context, request))

    def get(self, request):
        context = self.arch_service.filter_impactful_commits(request=request, request_params=request.GET)

        template = loader.get_template(self.template_name)

        # if directory_filter > 0:
        #     template = loader.get_template('architecture/old_impactful_commits.html')
        # else:
        #     template = loader.get_template('architecture/impactful_commits.html')

        return HttpResponse(template.render(context, request))
