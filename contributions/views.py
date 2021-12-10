import logging
import time

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from injector import inject

from common.utils import ViewUtils
from contributions.models import Commit
from contributions.services import ContributionsService

logger = logging.getLogger(__name__)


def set_default_filter_parameters(filter_: dict):
    filter_.pop('from_commit', None)
    filter_.pop('from_tag', None)
    filter_.pop('to_tag', None)
    filter_['only_modifications_with_file_types'] = ['.java']
    filter_['only_no_merge'] = True


class ContributionsView(View):
    @inject
    def __init__(self, contributions_service: ContributionsService):
        self.contributions_service = contributions_service

    model = Commit
    template_name = 'contributions/index.html'
    context_object_name = 'commit'

    def get(self, request):
        start = time.time()

        request = self.contributions_service.index(request)

        context = {
            'tag': request.GET.get('tag.description'),
            'current_tag_filter': request.GET.get('current_tag_filter'),
            'latest_commit_list': request.GET.get('latest_commit_list'),
        }

        end = time.time()
        self.logger.info("Tempo total: " + str(end - start))

        return render(request, self.template_name, context)

    def post(self, request):
        start = time.time()
        tag = ViewUtils.load_tag(request)

        # LOAD FROM PYDRILLER
        request = self.contributions_service.process(request)

        # LOAD

        tag = ViewUtils.load_tag(request)
        tag_id = request.POST.get('tag_filter_id')

        current_tag_filter = self.tag_repository.find_by_primary_key(pk=tag_id) if tag_id else None
        if not tag_id:
            latest_commit_list = self.commit_repository.find_all().order_by("tag_id", "author__name", "committer_date")

        paginator = Paginator(latest_commit_list, 100)

        page = request.GET.get('page')
        latest_commit_list = paginator.get_page(page)

        context = {
            'tag': tag.description,
            'current_tag_filter': current_tag_filter,
            'latest_commit_list': latest_commit_list,
        }

        end = time.time()
        self.logger.info("Tempo total: " + str(end - start))

        return render(request, self.template_name, context)

