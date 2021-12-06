from contributions.models import Developer
from contributions.repositories.model_repository import ModelRepository


class DeveloperRepository(ModelRepository):
    def __init__(self):
        super(DeveloperRepository, self).__init__(Developer)

    def find_all_developer_by_login(self, login: str):
        return Developer.objects.filter(login=login)

    def find_by_primary_key(self, pk: int):
        return super(DeveloperRepository, self).find_by_primary_key(pk=pk)

    def find_all_developer_by_iexact_name(self, name: str):
        return Developer.objects.filter(name__iexact=name)

    def find_all(self):
        return super(DeveloperRepository, self).find_all()
