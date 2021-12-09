from contributions.repositories.commit_repository import CommitRepository
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.tag_repository import TagRepository


class ContributionsService:
    def __init__(self, tag_repository: TagRepository, commit_repository: CommitRepository,
                 developer_repository: DeveloperRepository):
        self.tag_repository = tag_repository
