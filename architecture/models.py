from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from contributions.models import Project, Commit, Directory, Tag, Developer


class FileCommits(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=200)
    directory = models.CharField(max_length=100)
    has_compileds = models.BooleanField(default=False)
    build_path = models.CharField(max_length=200)
    local_repository = models.CharField(max_length=200,default="G:/My Drive/MestradoUSP/programacao/projetos/git/ant")

    def __str__(self):
        return self.directory+"/"+self.name

class Compiled(models.Model):
    file = models.ForeignKey(FileCommits, on_delete=models.CASCADE, related_name='compileds')
    previous_compiled = models.ForeignKey('Compiled', on_delete=models.SET_NULL, null=True, default=None)
    name = models.CharField(max_length=200)
    hash_commit = models.CharField(max_length=300)
    filename = models.CharField(max_length=300)
    quality_delta = models.IntegerField(default=0)

class ArchitectureQualityByDeveloper(models.Model):
    developer = models.ForeignKey(Developer, related_name='developer_id', on_delete=models.CASCADE)
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    @property
    def commit_activity_in_this_tag(self):
        return Commit.objects.filter(tag_id=self.tag.id, committer_id=self.developer.id).count()
        # return Commit.objects.filter(tag_id=self.tag.id).count()
        # return len(self.metrics.all())

    @property
    def architecturally_impactful_commits(self):
        number = 0
        for metric in self.metrics.all():
            if metric.delta_rmd != 0:
                number += 1
        return number

    @property
    def exposition(self):
        return self.architecturally_impactful_commits/self.commit_activity_in_this_tag

    @property
    def delta_rmd(self):
        delta_rmd = 0.0
        for metric in self.metrics.all():
            delta_rmd += metric.delta_rmd
        return delta_rmd

class ArchitectureQualityMetrics(models.Model):
    previous_architecture_quality_metrics = models.ForeignKey('ArchitectureQualityMetrics', on_delete=models.SET_NULL, null=True, default=None)
    architecture_quality_by_developer_and_directory = models.ForeignKey(ArchitectureQualityByDeveloper, on_delete=models.CASCADE, related_name="metrics")
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='architectural_metrics')
    # directory = models.ForeignKey(Directory, on_delete=models.CASCADE)
    rmd = models.FloatField(null=True, default=0.0)
    rma = models.FloatField(null=True, default=0.0)
    rmi = models.FloatField(null=True, default=0.0)
    ca = models.IntegerField(null=True, default=0)
    ce = models.IntegerField(null=True, default=0)

    def delta_metrics(self, metric, value):
        previous_metric_value = 0.0
        if self.previous_architecture_quality_metrics is None:
            return previous_metric_value
        previous_metric_value = getattr(self.previous_architecture_quality_metrics,metric)

        return value - previous_metric_value

    @property
    def delta_rmd(self):
        return self.delta_metrics("rmd",self.rmd)

    @property
    def delta_rma(self):
        return self.delta_metrics("rma", self.rma)

    @property
    def delta_rmi(self):
        return self.delta_metrics("rmd", self.rmi)

    @property
    def delta_ca(self):
        return self.delta_metrics("ca", self.ca)

    @property
    def delta_ce(self):
        return self.delta_metrics("ce", self.ce)


# method for updating
@receiver(post_save, sender=Compiled, dispatch_uid="update_compiled")
def update_compiled(sender, instance, **kwargs):
    commit=Commit.objects.filter(hash=instance.hash_commit)
    if commit.count() > 0:
        commit=commit[0]
        if commit.parents:
            for parent in commit.parents:
                compiled = Compiled.objects.filter(hash_commit=parent.hash)
                instance.previous_compiled=compiled[0] if compiled.count() > 0 else None
                break
        instance.save()
