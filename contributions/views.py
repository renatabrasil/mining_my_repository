import logging
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views import View
from django.views.generic.detail import BaseDetailView, DetailView
from injector import inject

from contributions.models import Commit
from contributions.services import ContributionsService, ContributionsDetailsService

logger = logging.getLogger(__name__)


class ContributionsListView(View):
    @inject
    def __init__(self, contributions_service: ContributionsService):
        self.contributions_service = contributions_service

    model = Commit
    template_name = 'contributions/index.html'
    context_object_name = 'commit'

    def get(self, request):
        start = time.time()

        context = self.contributions_service.index(request)

        end = time.time()
        logger.info("Tempo total: " + str(end - start))
        template = loader.get_template(self.template_name)

        return HttpResponse(template.render(context, request))

    def post(self, request):
        start = time.time()

        # LOAD FROM PYDRILLER
        request = self.contributions_service.process(request)

        # LOAD
        context = self.contributions_service.index(request)

        end = time.time()
        logger.info("Tempo total: " + str(end - start))

        return render(request, self.template_name, context)


class CommitDetailView(DetailView):
    model = Commit
    template_name = 'contributions/detail.html'


class ContributionsDetailView(BaseDetailView):
    @inject
    def __init__(self, contributions_service: ContributionsDetailsService):
        self.contributions_service = contributions_service

    model = Commit
    template_name = 'contributions/detail.html'
    context_object_name = 'commit'

    def get(self, request):
        return render(request, self.template_name, {'commit': None})

    def post(self, request):
        hash_commit = request.POST.get('hash')
        if hash_commit:
            request.session['hash'] = hash_commit
        else:
            if 'hash' in request.session:
                hash_commit = request.session['hash']
            else:
                hash_commit = None

        commit = self.contributions_service.show_commit(hash_commit)

        return render(request, self.template_name,
                      {'commit': commit, 'current_commit_hash': hash_commit, 'title': 'Detalhes do commit'})
