from contributions.models import Modification
from contributions.repositories.model_repository import ModelRepository


class ModificationRepository(ModelRepository):
    def __init__(self):
        super(ModificationRepository, self).__init__(Modification)

    def find_all_modifications_by_path(self, directory_id: int):  # pragma: no cover
        return Modification.objects.filter(directory_id=directory_id)
