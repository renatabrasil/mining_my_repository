from contributions.models import Tag
from contributions.repositories.model_repository import ModelRepository


class TagRepository(ModelRepository):
    def __init__(self):
        super(TagRepository, self).__init__(Tag)

    def find_by_primary_key(self, pk: int):  # pragma: no cover
        return super(TagRepository, self).find_by_primary_key(pk=pk)

    def find_all_major_tags_by_project(self, project_id: int, tag_id: int):  # pragma: no cover
        return Tag.objects.filter(project_id=project_id, id__gte=tag_id, major=True)
