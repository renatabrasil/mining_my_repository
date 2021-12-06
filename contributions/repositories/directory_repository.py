from contributions.models import Directory
from contributions.repositories.model_repository import ModelRepository


class DirectoryRepository(ModelRepository):
    def __init__(self):
        super(DirectoryRepository, self).__init__(Directory)

    def find_by_primary_key(self, pk: int):
        return super(DirectoryRepository, self).find_by_primary_key(pk=pk)

    def find_all_visible_directories_order_by_id(self):
        return Directory.objects.filter(visible=True).order_by("id")
