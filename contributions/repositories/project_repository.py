from contributions.models import Project
from contributions.repositories.model_repository import ModelRepository


class ProjectRepository(ModelRepository):
    def __init__(self):
        super(ProjectRepository, self).__init__(Project)

    def find_by_primary_key(self, pk: int) -> Project:  # pragma: no cover
        return super(ProjectRepository, self).find_by_primary_key(pk=pk)

    def find_project_by_name(self, name: str) -> Project:  # pragma: no cover
        return Project.objects.get(project_name=name)
