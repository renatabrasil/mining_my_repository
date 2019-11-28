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

class ArchitectureQualityMetrics(models.Model):
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.DO_NOTHING, related_name='architecture_quality_metrics')
    # All metrics are deltas
    rmd = models.FloatField(null=True, default=0.0)
    rma = models.FloatField(null=True, default=0.0)
    rmi = models.FloatField(null=True, default=0.0)
    ca = models.FloatField(null=True, default=0.0)
    ce = models.FloatField(null=True, default=0.0)

class ArchitectureQualityByDeveloper(models.Model):
    architecture_quality_metrics = models.ForeignKey(ArchitectureQualityMetrics, on_delete=models.CASCADE, related_name='metrics_by_developer')
    developer = models.ForeignKey(Developer, related_name='developer_id', on_delete=models.CASCADE)

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
