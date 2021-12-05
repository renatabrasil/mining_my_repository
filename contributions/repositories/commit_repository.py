from django.db.models import QuerySet

from contributions.models import Commit, Project


class CommitRepository:
    def find_all_commits_by_project_order_by_id_asc(self, project: Project):
        return list(Commit.objects.filter(tag__project=project).order_by("id"))

    def update(self, commits: QuerySet, **fields):
        commits.update(**fields)

    def find_and_update_commit_by_tag(self, tag_id: int, **fields):
        commits = Commit.objects.update(**fields)
