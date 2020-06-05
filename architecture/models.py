# Django
from django.db import models

# local Django
from contributions.models import Commit, Directory, Tag, Modification, NoOutlierCommitManager, AUTHOR_FILTER, Developer, \
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
    component_commit = models.ForeignKey(ComponentCommit, on_delete=models.CASCADE, related_name='architectural_metrics', null=True)
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='architectural_metrics')
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

    def delta_metrics(self, metric, value):
        previous_metric_value = 0.0
        try:
            if len(self.commit.parents) == 0:
                if self.commit.is_initial_commit_in_component(self.directory):
                    return self.rmd / self.commit.u_cloc
                else:
                    return 0.0

            parent_commit = self.commit.parents[0]
            if self.previous_architecture_quality_metrics is None:
                if not parent_commit.compilable and (
                        parent_commit.author == self.commit.author and len(parent_commit.parents) > 0):
                    previous_commit_parent = parent_commit.parents[0]
                    previous_commit_metric = ArchitecturalMetricsByCommit.objects.filter(
                        commit=previous_commit_parent, directory=self.directory)
                    if previous_commit_metric.count() > 0:
                        previous_commit_metric = previous_commit_metric[0]
                        self.previous_architecture_quality_metrics = previous_commit_metric
                    else:
                        return 0.0
                else:
                    return 0.0

            previous_metric_value = getattr(self.previous_architecture_quality_metrics, metric)
            return (value - previous_metric_value) / self.commit.u_cloc
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

    # def save(self, *args, **kwargs):
    #     # self.delta_rmd = self.delta_metrics("rmd",self.rmd)
    #
    #     if self.pk is None:
    #         '''cloc_accumulation, commits_accumulation are referred sum of all this activities up (by not included) the current commit'''
    #
    #         previous_contribution_to_component = ArchitecturalMetricsByCommit.objects.filter(commit__author=self.commit.author,
    #                                                                                          directory=self.directory,
    #                                                                                          commit__modifications__directory = self.directory,
    #                                                                                          commit__tag__lte=self.commit.tag.id).last()
    #         file_by_authors = Modification.objects.none()
    #
    #         # because components are saved directly
    #         if previous_contribution_to_component is not None:
    #             cloc_accumulation = previous_contribution_to_component.cloc_accumulation
    #             self.commits_accumulation = previous_contribution_to_component.commits_accumulation + 1
    #             self.cloc_accumulation = cloc_accumulation + previous_contribution_to_component.commit.cloc_uncommented(self.directory)
    #             # because Modification model imply any directory whether they are components or not
    #             file_by_authors = Modification.objects.filter(commit__author=self.commit.author,
    #                                                           commit__tag_id__lte=self.commit.tag.id,
    #                                                           commit_id__lt=self.commit.id,
    #                                                           directory__name__startswith=self.directory.name)
    #
    #         files = file_by_authors.values("path").distinct().count()
    #
    #         self.author_experience = 0.2 * self.commits_accumulation + 0.4 * files + 0.4 * self.cloc_accumulation
    #
    #     super(ArchitecturalMetricsByCommit, self).save(*args, **kwargs)  # Call the "real" save() method.

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
