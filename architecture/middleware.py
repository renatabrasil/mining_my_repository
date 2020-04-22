from architecture.views import NO_OUTLIERS
from contributions.models import Commit


class SetupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        commit_db = Commit.objects
        if NO_OUTLIERS and NO_OUTLIERS==1:
            commit_db = Commit.no_outliers_objects

        request.commit_db = commit_db

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response