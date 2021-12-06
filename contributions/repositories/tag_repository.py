from contributions.models import Tag
from contributions.repositories.model_repository import ModelRepository


class TagRepository(ModelRepository):
    def __init__(self):
        super(TagRepository, self).__init__(Tag)

    def find_by_primary_key(self, pk: int):
        return super(TagRepository, self).find_by_primary_key(pk=pk)
