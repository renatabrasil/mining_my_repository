# Django
from django.db import models

# local Django
from contributions.models import Commit, Directory, Tag, AUTHOR_FILTER, Developer, \
    ComponentCommit


class FileCommits(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='files')
    metrics_calculated_at = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=200)
    directory = models.CharField(max_length=100)
    has_compileds = models.BooleanField(default=False)
    build_path = models.CharField(max_length=200)
    local_repository = models.CharField(max_length=200, default="G:/My Drive/MestradoUSP/programacao/projetos/git/ant")

    def __str__(self):
        return self.directory + "/" + self.name


class NoOutlierMetricManager(models.Manager):
    def get_queryset(self):
        ids = []
        for author in AUTHOR_FILTER:
            author_db = Developer.objects.get(name=author)
            if author_db:
                ids.append(author_db.id)
        return super().get_queryset().exclude(commit__author_id__in=ids)

