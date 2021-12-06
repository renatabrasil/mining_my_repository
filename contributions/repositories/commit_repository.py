from contributions.models import Commit, Project
from contributions.repositories.model_repository import ModelRepository


class CommitRepository(ModelRepository):
    def __init__(self):
        super(CommitRepository, self).__init__(Commit)

    def find_all_distinct_commits_by_tag_description(self, description: str):
        return Commit.objects.filter(tag__description=description).distinct()

    def find_all_distinct_commits_by_committer_and_modifications_for_specific_directory(self, committer_id: int,
                                                                                        tag_id: int,
                                                                                        modifications: list):
        return Commit.objects.filter(committer_id=committer_id, tag_id__lte=tag_id,
                                     modifications__in=modifications).distinct()

    def find_all_commits_by_tag(self, tag_id: int):
        return Commit.objects.filter(tag_id=tag_id)

    def find_all_commits_by_author_id(self, author_id: int):
        return Commit.objects.filter(author_id=author_id)

    def find_all_previous_commits(self, commit: Commit):
        return Commit.objects.filter(tag=commit.tag, id__lt=commit.id,
                                     tag__real_tag_description__iexact=commit.tag.real_tag_description)

    def find_by_primary_key(self, pk: int):
        return super(CommitRepository, self).find_by_primary_key(pk)

    def find_all(self):
        return super(CommitRepository, self).find_all()

    def find_all_commits_by_project_order_by_id_asc(self, project: Project):
        return Commit.objects.filter(tag__project=project).order_by("id")

    def find_all_commit_from_all_previous_tag(self, tag_id: int, project_id: int):
        return Commit.objects.filter(tag_id__lte=tag_id, tag__project__id=project_id)

    def find_all_commits_by_project_order_by_id_asc_as_list(self, project: Project):
        return list(self.find_all_commits_by_project_order_by_id_asc())

    def find_all_commits_by_hash(self, hash: str):
        return Commit.objects.filter(hash=hash)

    def find_all_compilable_commits_by_hash(self, hash: str):
        return Commit.objects.filter(hash=hash, compilable=True)

    def update(self, commit: Commit, fields: dict):
        return super(CommitRepository, self).update(commit, fields)

    def insert(self, commit: Commit):
        return super(CommitRepository, self).insert(model=commit)
