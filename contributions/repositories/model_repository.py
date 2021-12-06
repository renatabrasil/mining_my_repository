from django.db import models
from django.db.models import Model


class ModelRepository:
    def __init__(self, model: models.Model):
        self._model = model

    def insert(self, model: Model):
        return model.save()

    def update(self, model: Model, fields: dict):
        self._model.objects.filter(pk=model.pk).update(**fields)
        model.refresh_from_db()
        return model

    def find_by_primary_key(self, pk: int):
        return self._model.objects.get(pk=pk)

    def find_all(self):
        return self._model.objects.all()
