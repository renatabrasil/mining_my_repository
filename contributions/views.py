import logging
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views import View
from injector import inject

from contributions.models import Commit
from contributions.services import ContributionsService

logger = logging.getLogger(__name__)


class ContributionsView(View):
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
