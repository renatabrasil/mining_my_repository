from django.db import models

from contributions.models import Commit, Directory, Tag


class FileCommits(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(max_length=200)
    directory = models.CharField(max_length=100)
    has_compileds = models.BooleanField(default=False)
    build_path = models.CharField(max_length=200)
    local_repository = models.CharField(max_length=200,default="G:/My Drive/MestradoUSP/programacao/projetos/git/ant")

    def __str__(self):
        return self.directory+"/"+self.name

class ArchitecturalMetricsByCommit(models.Model):
    previous_architecture_quality_metrics = models.ForeignKey('ArchitecturalMetricsByCommit', on_delete=models.SET_NULL, null=True, default=None)
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='architectural_metrics')
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='architectural_metrics')
    rmd = models.FloatField(null=True, default=0.0)
    delta_rmd = models.FloatField(null=True, default=0.0)
    rma = models.FloatField(null=True, default=0.0)
    rmi = models.FloatField(null=True, default=0.0)
    ca = models.IntegerField(null=True, default=0)
    ce = models.IntegerField(null=True, default=0)

    @property
    def commit_loc(self):
        return self.commit.cloc_uncommented(self.directory)

    def delta_metrics(self, metric, value):
        previous_metric_value = 0.0
        try:
            if self.previous_architecture_quality_metrics is None:
                return previous_metric_value/self.commit.u_cloc
            previous_metric_value = getattr(self.previous_architecture_quality_metrics,metric)
            return (value - previous_metric_value)/self.commit.u_cloc
        except ZeroDivisionError:
            return 0.0

    # @property
    # def delta_rmd(self):
    #     return self.delta_metrics("rmd",self.rmd)

    @property
    def delta_rma(self):
        return self.delta_metrics("rma", self.rma)

    @property
    def delta_rmi(self):
        return self.delta_metrics("rmi", self.rmi)

    @property
    def delta_ca(self):
        return self.delta_metrics("ca", self.ca)

    @property
    def delta_ce(self):
        return self.delta_metrics("ce", self.ce)

    @property
    def architectural_impactful_loc(self):
        number = 0
        for mod in self.commit.modifications.all():
            if mod.directory == self.directory:
                if self.delta_rmd != 0:
                    number += mod.u_cloc
        return number

    def save(self, *args, **kwargs):
        self.delta_rmd = self.delta_metrics("rmd",self.rmd)

        super(ArchitecturalMetricsByCommit, self).save(*args, **kwargs)  # Call the "real" save() method.

    # @property
    # def exposition(self):
    #     return self.architectural_impactful_loc / self.commit_activity_in_this_tag


# method for updating
# @receiver(post_save, sender=Compiled, dispatch_uid="update_compiled")
# def update_compiled(sender, instance, **kwargs):
#     commit=Commit.objects.filter(hash=instance.hash_commit)
#     if commit.count() > 0:
#         commit=commit[0]
#         if commit.parents:
#             for parent in commit.parents:
#                 compiled = Compiled.objects.filter(hash_commit=parent.hash)
#                 instance.previous_compiled=compiled[0] if compiled.count() > 0 else None
#                 break
#         instance.save()
