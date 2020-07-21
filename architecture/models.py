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


class ArchitecturalMetricsByCommit(models.Model):
    author_experience = models.FloatField(null=True, default=0.0)
    cloc_accumulation = models.IntegerField(default=0)
    commits_accumulation = models.IntegerField(default=0)
    previous_architecture_quality_metrics = models.ForeignKey('ArchitecturalMetricsByCommit', on_delete=models.SET_NULL,
                                                              null=True, default=None)
    component_commit = models.ForeignKey(ComponentCommit, on_delete=models.CASCADE,
                                         related_name='architectural_metrics', null=True)
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='architectural_metrics', null=True)
    commit_str = models.CharField(max_length=200, default="", blank=True, null=True)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='architectural_metrics')
    rmd = models.FloatField(null=True, default=0.0)
    delta_rmd = models.FloatField(null=True, default=0.0)
    rma = models.FloatField(null=True, default=0.0)
    rmi = models.FloatField(null=True, default=0.0)
    ca = models.IntegerField(null=True, default=0)
    ce = models.IntegerField(null=True, default=0)

    objects = models.Manager()  # The default manager.
    no_outliers_objects = NoOutlierMetricManager()  # The specific manager.

    @property
    def author_experience(self):
        return self.component_commit.author_experience if self.component_commit is not None else 0

    @property
    def commit_loc(self):
        return self.commit.cloc_uncommented(self.directory)

    @property
    def architectural_impactful_loc(self):
        number = 0
        for mod in self.commit.modifications.all():
            if mod.directory == self.directory:
                if self.delta_rmd != 0:
                    number += mod.u_cloc
        return number

