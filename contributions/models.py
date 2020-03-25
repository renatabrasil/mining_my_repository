# standard library
import re
import warnings
from datetime import date

# third-party
import numpy as np

# Django
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from pydriller import GitRepository

# local Django
from common.utils import CommitUtils
from dataanalysis.models import AnalysisPeriod


class Developer(models.Model):
    name = models.CharField(max_length=200)
    login = models.CharField(max_length=60, default='')
    email = models.CharField(max_length=200)

    def __str__(self):
        return self.name + ' (login: ' + self.login + ', email: ' + self.email + ')'


class Project(models.Model):
    project_name = models.CharField(max_length=200)
    project_path = models.CharField(max_length=200)

    def __str__(self):
        return self.project_name

    @property
    def first_tag(self):
        return self.tags.all().first()


class Tag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tags')
    description = models.CharField(max_length=100)
    previous_tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True, default=None)
    # alias = models.CharField(max_length=40, null=True)
    v1_1 = 1

    @staticmethod
    def line_base():
        return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]

    @staticmethod
    def line_1_10_x():
        return Tag.line_base() + [24, 25, 26, 27, 28, 29, 30, 31]

    @staticmethod
    def line_1_9_x():
        return Tag.line_base() + [17, 18, 19, 20, 21, 22, 23]

    def __str__(self):
        return self.description

    # def save(self, *args, **kwargs):
    #     if self.alias is None:
    #         self.alias = self.description
    #
    #     super(Tag, self).save(*args, **kwargs)  # Call the "real" save() method.


class Directory(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='directories')
    visible = models.BooleanField(default=False)
    initial_commit = models.ForeignKey('Commit', on_delete=models.CASCADE, related_name='starter_directories',
                                       null=True)

    def __str__(self):
        return self.name + " - Visible: " + str(self.visible)


class Commit(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='commits')
    children_commit = models.ForeignKey('Commit', on_delete=models.SET_NULL, related_name='parent_rel', null=True,
                                        default=None)
    hash = models.CharField(max_length=180, default="")
    msg = models.CharField(max_length=300, default="")
    parents_str = models.CharField(max_length=180)
    author = models.ForeignKey(Developer, related_name='commits', on_delete=models.CASCADE)
    author_experience = models.FloatField(null=True, default=0.0)
    author_date = models.DateTimeField(default=now, editable=False)
    committer = models.ForeignKey(Developer, related_name='committer_id', on_delete=models.CASCADE)
    committer_date = models.DateTimeField(default=now, editable=False)

    author_seniority = models.IntegerField(default=0)
    total_commits = models.IntegerField(default=0)

    # key: tag_id, value: sum of u_cloc of all commits by this author in this tag
    changed_architecture = models.BooleanField(default=False)
    analysis_period = models.ForeignKey(AnalysisPeriod, on_delete=models.DO_NOTHING, null=True)
    cloc_activity = models.IntegerField(default=0)
    compilable = models.BooleanField(default=True)
    _parents = []
    # mean rmd
    mean_rmd_components = models.FloatField(null=True, default=0.0)
    # standard deviation rmd
    std_rmd_components = models.FloatField(null=True, default=0.0)
    # delta
    delta_rmd_components = models.FloatField(null=True, default=0.0)

    def __str__(self):
        return self.hash + " - Author: " + self.author.name + " - Tag: " + self.tag.description

    def calculate_boosting_factor(self, activity_array):
        if not activity_array or len(activity_array) == 1:
            return 0.0
        elif len(activity_array) == 2:
            return 0.5
        mean_value = np.mean(activity_array)
        min_value = np.min(activity_array)
        max_value = np.max(activity_array)

        numerator = (mean_value - min_value)

        if numerator == 0.0:
            return 0.0
        try:
            return numerator / (max_value - min_value)
        except ZeroDivisionError:
            return 0.0

    def has_files_in_this_directory(self, directory):
        for mod in self.modifications.all():
            if mod.directory == directory:
                return True
        return False

    @property
    def parents(self):
        self._parents = []
        lista = self.parents_str.split(",")
        for parent_hash in lista:
            parent = Commit.objects.filter(hash=parent_hash)
            if parent.count() > 0:
                parent = parent[0]
                self._parents.append(parent)
        return self._parents

    @parents.setter
    def parents(self, list):
        self._parents = list

    @property
    def number_of_java_files(self):
        total_java_files = 0
        for modification in self.modifications.all():
            if modification.is_java_file:
                total_java_files = total_java_files + 1
        return total_java_files

    @property
    def cloc(self):
        cloc = 0
        for mod in self.modifications.all():
            cloc += mod.cloc
        return cloc

    @property
    def u_cloc(self):
        u_cloc = 0
        for mod in self.modifications.all():
            u_cloc += mod.u_cloc
        return u_cloc

    @property
    def total_delta(self):
        delta = 0.0
        for metric in self.architectural_metrics.all():
            delta += metric.delta_rmd
        return delta

    def cloc_uncommented(self, directory):
        cloc = 0
        for mod in self.modifications.all():
            if mod.directory == directory:
                cloc += mod.u_cloc
        return cloc

    def is_initial_commit_in_component(self, directory):
        for dir in self.starter_directories.all():
            if dir == directory:
                return True
        return False

    @property
    def delta_rmd(self):
        return self.delta_rmd_components

    def save(self, *args, **kwargs):
        self.author.save()
        self.committer.save()

        previous_commit = Commit.objects.filter(author=self.author).last()
        if self.pk is not None:
            previous_commit = Commit.objects.filter(author=self.author, id__lt=self.pk).last()

        first_commit = Commit.objects.filter(author=self.author).first()

        if first_commit is not None and previous_commit is not None:
            self.total_commits = previous_commit.total_commits + 1
            self.author_seniority = self.author_date - first_commit.author_date
            self.author_seniority = self.author_seniority.days

        for hash in self.parents:
            parent = Commit.objects.filter(hash=hash)
            if parent.count() > 0:
                self.parent = parent[0]

        if self.pk is None:
            self.author_experience = 0.0
            previous_commit = None

            file_by_authors = Modification.objects.none()
            if previous_commit.total_commits > 0:
                file_by_authors = Modification.objects.filter(commit__author=self.author)

            self.cloc_activity = 0
            if previous_commit is not None:
                self.cloc_activity = previous_commit.cloc_activity

            # cloc_activity = [c.u_cloc for c in file_by_authors]
            # cloc = sum(cloc_activity)

            files = file_by_authors.values("path").distinct().count()

            self.author_experience = 0.2 * previous_commit.total_commits + 0.4 * files + 0.4 * self.cloc_activity

        super(Commit, self).save(*args, **kwargs)  # Call the "real" save() method.


class Modification(models.Model):
    old_path = models.CharField(max_length=200, null=True)
    new_path = models.CharField(max_length=200, null=True)
    path = models.CharField(max_length=200, null=True, default="")
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='modifications')
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='modifications')
    ADDED = 'ADD'
    DELETED = 'DEL'
    MODIFIED = 'MOD'
    RENAMED = 'REN'
    CHANGE_TYPES_CHOICES = [
        (ADDED, 'Added'),
        (DELETED, 'Deleted'),
        (MODIFIED, 'Modified'),
        (RENAMED, 'Renamed'),
    ]
    change_type = models.CharField(
        max_length=10,
        choices=CHANGE_TYPES_CHOICES,
        default=MODIFIED,
    )
    diff = models.TextField(default="")
    source_code = models.TextField(null=True)
    source_code_before = models.TextField(null=True)
    added = models.IntegerField(default=0)
    removed = models.IntegerField(default=0)
    cloc = models.IntegerField(default=0)
    u_cloc = models.IntegerField(default=0)
    # FIXME
    nloc = models.IntegerField(default=0, null=True)
    complexity = models.IntegerField(null=True)

    # token_count = models.CharField(max_length=200,null=True)

    # def __eq__(self, other):
    # 	return isinstance(other, self.__class__) and (self.commit.hash == other.commit.hash and self.file == other.file)

    def __str__(self):
        return "Commit: " + self.commit.hash + " - Directory: " + self.directory.name + " - File name: " + self.file

    def __diff_text__(self):
        GR = GitRepository(self.commit.tag.project.project_path)

        parsed_lines = GR.parse_diff(self.diff)

        return parsed_lines

    def __print_text_in_lines__(self, text, result, type_symbol):
        for line in text:
            result = result + "\n" + str(line[0]) + ' ' + type_symbol + ' ' + line[1]
        return result

    def __cloc_uncommented__(self):
        diff_text = self.__diff_text__()
        added_text = self.__print_text_in_lines__(diff_text['added'], "", "")
        deleted_text = self.__print_text_in_lines__(diff_text['deleted'], "", "")
        added_uncommented_lines = count_uncommented_lines(added_text)
        deleted_uncommented_lines = count_uncommented_lines(deleted_text)
        return added_uncommented_lines + deleted_uncommented_lines
        # return 0

    @property
    def diff_added(self):
        parsed_lines = self.__diff_text__()
        added_text = parsed_lines['added']

        diff_text = None
        diff_text = '\n' + str(self.added) + ' lines added: \n'  # result: Added: [(4, 'log.debug("b")')]
        diff_text = self.__print_text_in_lines__(added_text, diff_text, '+')

        return diff_text

    @property
    def diff_removed(self):
        deleted_text = self.__diff_text__()['deleted']
        diff_text = '\n' + str(self.removed) + ' lines removed:  \n'
        diff_text = self.__print_text_in_lines__(deleted_text, diff_text, '-')

        return diff_text

    @property
    def file(self):
        index = self.path.rfind("/")
        if index > -1:
            return self.path[index + 1:]
        return self.path

    @property
    def is_java_file(self):
        return CommitUtils.modification_is_java_file(self.path)

    def save(self, *args, **kwargs):

        self.path = CommitUtils.true_path(self)

        if self.is_java_file:
            self.u_cloc = self.__cloc_uncommented__()

            # If cloc = 0 do not save file neither commit
            if self.u_cloc > 0:

                if self.commit.pk is None:
                    self.commit.save()

                index = self.path.rfind("/")
                directory_str = ""
                if index > -1:
                    directory_str = self.path[:index]
                else:
                    directory_str = "/"

                directory = Directory.objects.filter(name=directory_str)
                if directory.count() == 0:
                    directory = Directory(name=directory_str, project=self.commit.tag.project,
                                          initial_commit=self.commit)
                    directory.save()
                    self.directory = directory
                else:
                    self.directory = directory[0]

                self.cloc = self.added + self.removed
                self.commit.cloc_activity += self.u_cloc
                self.commit.save()

                super(Modification, self).save(*args, **kwargs)  # Call the "real" save() method.


# TODO: Change to a heritage relation. Distinct Types: Project and Directory
class ProjectIndividualContribution(models.Model):
    author = models.ForeignKey(Developer, on_delete=models.CASCADE)
    project_report = models.ForeignKey('ProjectReport', on_delete=models.CASCADE)
    previous_individual_contribution = models.ForeignKey('ProjectIndividualContribution', on_delete=models.SET_NULL,
                                                         null=True, default=None)
    cloc = models.IntegerField(null=True, default=0)
    files = models.IntegerField(null=True, default=0)
    commits = models.IntegerField(null=True, default=0)
    cloc_exp = models.FloatField(null=True, default=0.0)
    file_exp = models.FloatField(null=True, default=0.0)
    commit_exp = models.FloatField(null=True, default=0.0)
    experience = models.FloatField(null=True, default=0.0)
    experience_bf = models.FloatField(null=True, default=0.0)
    bf_commit = models.FloatField(null=True, default=0.0)
    bf_file = models.FloatField(null=True, default=0.0)
    bf_cloc = models.FloatField(null=True, default=0.0)

    def __str__(self):
        return "Author: " + self.author.name + " - Experience: " + str(
            self.experience) + " - Tag: " + self.project_report.tag.description

    # Duplicated code
    ####
    def ownership(self, metric):
        try:
            total_metric = getattr(self.project_report, "total_" + metric)
            count = getattr(self, metric)
            return count / total_metric
        except ZeroDivisionError:
            return 0.0

    @property
    def ownership_commits(self):
        return self.ownership('commits')

    @property
    def ownership_files(self):
        return self.ownership('files')

    @property
    def ownership_cloc(self):
        return self.ownership('cloc')

    def ownership_in_this_tag(self, metric):
        try:
            first_project_report = ProjectReport.objects.filter(tag__project=self.project_report.tag.project).order_by(
                "pk").first()
            total_metric = "total_" + metric
            commit_in_this_tag = getattr(self, metric)
            total_commit_in_this_tag = 0
            if self.previous_individual_contribution:
                commit_in_this_tag -= getattr(self.previous_individual_contribution, metric)
                total_commit_in_this_tag = getattr(self.project_report, total_metric) - getattr(
                    self.previous_individual_contribution.project_report, total_metric)
            elif self.project_report.tag.id > first_project_report.tag.id:
                total_commit_in_this_tag = getattr(self.project_report, total_metric) - getattr(first_project_report,
                                                                                                total_metric)
            else:
                return getattr(self, 'ownership_' + metric)
            return commit_in_this_tag / total_commit_in_this_tag
        except ZeroDivisionError:
            return 0.0

    @property
    def ownership_commits_in_this_tag(self):
        return self.ownership_in_this_tag("commits")

    @property
    def ownership_files_in_this_tag(self):
        return self.ownership_in_this_tag("files")

    @property
    def ownership_cloc_in_this_tag(self):
        return self.ownership_in_this_tag("cloc")

    def __all_previous_contributions__(self):
        contributions = []
        previous_contribution = self.previous_individual_contribution
        while previous_contribution is not None:
            contributions.append(previous_contribution)
            previous_contribution = previous_contribution.previous_individual_contribution
        if len(contributions) > 0:
            contributions.sort(key=lambda x: x.id, reverse=False)
        return contributions

    def metric_activity(self, metric):
        attribute_ = 'ownership_' + metric + '_in_this_tag'
        contributions = self.__all_previous_contributions__()
        extra_values = []
        # whether there is any contribution in this directory from other authors
        # It means that is not a new directory, so we have to count all period
        # if len(contributions) > 0:
        first_tag_in_this_project = ProjectReport.objects.filter(
            tag__project_id=self.project_report.tag.project.id).order_by("pk").first().tag.id
        right_length = self.project_report.tag.id - first_tag_in_this_project + 1 - len(contributions)
        for i in range(1, right_length):
            extra_values.append(0.0)
        metric_actitivy_array = [getattr(i, attribute_) for i in contributions]
        metric_actitivy_array = metric_actitivy_array + extra_values
        metric_actitivy_array.append(getattr(self, attribute_))
        return metric_actitivy_array

    @property
    def commit_activity(self):
        return self.metric_activity('commits')

    @property
    def file_activity(self):
        return self.metric_activity('files')

    @property
    def cloc_activity(self):
        return self.metric_activity('cloc')

    ### End duplicaded code

    def calculate_boosting_factor(self, activity_array):
        if not activity_array or len(activity_array) == 1:
            return 0.0
        mean_value = np.mean(activity_array)
        min_value = np.min(activity_array)
        max_value = np.max(activity_array)

        numerator = (mean_value - min_value)

        if numerator == 0.0:
            return 0.0
        try:
            return numerator / (max_value - min_value)
        except ZeroDivisionError:
            return 0.0

    def save(self, *args, **kwargs):
        if self.project_report.tag.previous_tag:
            previous_individual_contribution = ProjectIndividualContribution.objects.filter(
                project_report__tag_id__lte=self.project_report.tag.previous_tag.id, author_id=self.author.id).order_by(
                "-project_report__tag_id")
            if previous_individual_contribution.count() > 0:
                previous_individual_contribution = previous_individual_contribution[0]
                self.previous_individual_contribution = previous_individual_contribution

        denominator = 1
        first_tag_id = ProjectReport.objects.filter(tag__project_id=self.project_report.tag.project.id).first().tag.id
        current_tag_id = self.project_report.tag.id
        if current_tag_id == first_tag_id:
            self.commit_exp = self.ownership_commits
            self.file_exp = self.ownership_files
            self.cloc_exp = self.ownership_cloc
            self.experience_bf = 0.2 * self.commit_exp + 0.4 * self.file_exp + 0.4 * self.cloc_exp
            self.experience = self.experience_bf
        else:
            commit_activity = self.metric_activity("commits")
            file_activity = self.metric_activity("files")
            cloc_activity = self.metric_activity("cloc")

            # commit activity
            self.bf_commit = self.calculate_boosting_factor(commit_activity)
            # file activity
            self.bf_file = self.calculate_boosting_factor(file_activity)
            # cloc_activity
            self.bf_cloc = self.calculate_boosting_factor(cloc_activity)

            denominator = len(commit_activity)
            self.commit_exp = (self.bf_commit + 1) * (sum(commit_activity) / denominator)
            # self.commit_exp = (self.bf_commit + 1) * self.ownership_commits/denominator
            self.file_exp = (self.bf_file + 1) * (sum(file_activity) / denominator)
            self.cloc_exp = (self.bf_cloc + 1) * (sum(cloc_activity) / denominator)
            self.experience_bf = 0.2 * self.commit_exp + 0.4 * self.file_exp + 0.4 * self.cloc_exp
            self.experience = 0.2 * (sum(commit_activity) / denominator) + 0.4 * (
                    sum(file_activity) / denominator) + 0.4 * (sum(cloc_activity) / denominator)

        super().save(*args, **kwargs)  # Call the "real" save() method.


class ProjectReport(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='project_reports')
    authors = models.ManyToManyField(Developer, through=ProjectIndividualContribution)
    total_cloc = models.IntegerField(null=True, default=0)
    total_files = models.IntegerField(null=True, default=0)
    total_commits = models.IntegerField(null=True, default=0)
    cloc_threshold = models.FloatField(null=True, default=0.0)
    file_threshold = models.FloatField(null=True, default=0.0)
    commit_threshold = models.FloatField(null=True, default=0.0)
    experience_threshold = models.FloatField(null=True, default=0.0)
    standard_deviation = models.FloatField(null=True, default=0)
    mean = models.FloatField(null=True, default=0)
    median = models.FloatField(null=True, default=0)

    def __str__(self):
        return "Project tag: " + self.tag.description

    @classmethod
    def first_project_report(cls):
        return ProjectReport.objects.filter(tag__project_id=cls.tag.project.id).order_by("id").first()

    def calculate_statistical_metrics(self):
        experiences = [c.experience_bf for c in list(
            ProjectIndividualContribution.objects.filter(project_report_id=self.id).order_by("-experience_bf"))]
        interval = np.array(experiences)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if interval.any():
                self.experience_threshold = np.percentile(interval, 80)
            self.standard_deviation = np.std(experiences, ddof=1)
            self.mean = np.mean(experiences)
            self.median = np.median(experiences)
            self.save()

    @property
    def core_developers_experience(self):
        core_developers = []
        contributions = list(
            ProjectIndividualContribution.objects.filter(project_report_id=self.id).order_by("-experience_bf"))
        for contributor in contributions:
            #     # TODO: check if it makes sense
            if len(contributions) == 1:
                return [contributor.author]
            if contributor.experience_bf > self.experience_threshold:
                core_developers.append(contributor.author)
        return core_developers

    @property
    def peripheral_developers_experience(self):
        peripheral_developers = []
        contributions = list(
            ProjectIndividualContribution.objects.filter(project_report_id=self.id).order_by("-experience_bf"))
        if len(contributions) == 1:
            return peripheral_developers
        for contributor in contributions:
            if contributor.experience_bf <= self.experience_threshold:
                peripheral_developers.append(contributor.author)
        return peripheral_developers

    # Experience with boosting factor
    @property
    def experience(self):
        contributions = list(
            ProjectIndividualContribution.objects.filter(project_report_id=self.id).order_by("-experience_bf"))
        return contributions[0].experience_bf if len(contributions) > 0 else 0

    @property
    def ownership(self):
        higher_value = -1.0
        contributions = list(ProjectIndividualContribution.objects.filter(project_report_id=self.id))
        for contributor in contributions:
            if contributor.ownership_commits >= higher_value:
                higher_value = contributor.ownership_commits
        return higher_value

    @property
    def minor(self):
        minor = 0
        contributions = list(ProjectIndividualContribution.objects.filter(project_report_id=self.id))
        for contributor in contributions:
            if contributor.ownership_commits <= 0.05:
                minor = minor + 1
        return minor

    @property
    def major(self):
        major = 0
        contributions = list(ProjectIndividualContribution.objects.filter(project_report_id=self.id))
        for contributor in contributions:
            if contributor.ownership_commits > 0.05:
                major = major + 1
        return major


# FIXME Tests and model removing ownership. Similar to ProjectIndividualContribution
class IndividualContribution(models.Model):
    author = models.ForeignKey(Developer, on_delete=models.CASCADE)
    directory_report = models.ForeignKey('DirectoryReport', on_delete=models.CASCADE)
    previous_individual_contribution = models.ForeignKey('IndividualContribution', on_delete=models.SET_NULL, null=True,
                                                         default=None)
    cloc = models.IntegerField(null=True, default=0)
    files = models.IntegerField(null=True, default=0)
    commits = models.IntegerField(null=True, default=0)
    ownership_cloc = models.FloatField(null=True, default=0.0)
    cloc_exp = models.FloatField(null=True, default=0.0)
    ownership_files = models.FloatField(null=True, default=0.0)
    file_exp = models.FloatField(null=True, default=0.0)
    ownership_commits = models.FloatField(null=True, default=0.0)
    commit_exp = models.FloatField(null=True, default=0.0)
    experience = models.FloatField(null=True, default=0.0)
    experience_bf = models.FloatField(null=True, default=0.0)
    bf_commit = models.FloatField(null=True, default=0.0)
    bf_file = models.FloatField(null=True, default=0.0)
    bf_cloc = models.FloatField(null=True, default=0.0)

    def __str__(self):
        return "Author: " + self.author.name + " - Directory: " + \
               self.directory_report.directory.name + " - Experience: " + \
               str(self.experience) + " - Tag: " + self.directory_report.tag.description

    def ownership_in_this_tag(self, metric):
        try:
            first_directory_report = DirectoryReport.objects.filter(tag__project=self.directory_report.tag.project,
                                                                    directory=self.directory_report.directory). \
                order_by("pk").first()
            total_metric = "total_" + metric
            commit_in_this_tag = getattr(self, metric)
            total_commit_in_this_tag = 0
            if self.previous_individual_contribution:
                commit_in_this_tag -= getattr(self.previous_individual_contribution, metric)
                total_commit_in_this_tag = getattr(self.directory_report, total_metric) - getattr(
                    self.previous_individual_contribution.directory_report, total_metric)
            elif self.directory_report.tag.id > first_directory_report.tag.id:
                total_commit_in_this_tag = getattr(self.directory_report, total_metric) - getattr(
                    first_directory_report,
                    total_metric)
            else:
                return getattr(self, 'ownership_' + metric)
            return commit_in_this_tag / total_commit_in_this_tag
        except ZeroDivisionError:
            return 0.0

    @property
    def ownership_commits_in_this_tag(self):
        return self.ownership_in_this_tag("commits")

    @property
    def ownership_files_in_this_tag(self):
        return self.ownership_in_this_tag("files")

    @property
    def ownership_cloc_in_this_tag(self):
        return self.ownership_in_this_tag("cloc")

    def __all_previous_contributions__(self):
        contributions = []
        previous_contribution = self.previous_individual_contribution
        while previous_contribution is not None:
            contributions.append(previous_contribution)
            previous_contribution = previous_contribution.previous_individual_contribution
        if len(contributions) > 0:
            contributions.sort(key=lambda x: x.id, reverse=False)
        return contributions

    def metric_activity(self, metric):
        attribute_ = 'ownership_' + metric + '_in_this_tag'
        contributions = self.__all_previous_contributions__()
        extra_values = []
        # whether there is any contribution in this directory from other authors
        # It means that is not a new directory, so we have to count all period
        first_tag_in_this_project = DirectoryReport.objects.filter(tag__project_id=self.directory_report.tag.project.id,
                                                                   directory_id=self.directory_report.directory.id).order_by(
            "pk").first().tag.id
        right_length = self.directory_report.tag.id - first_tag_in_this_project + 1 - len(contributions)
        for i in range(1, right_length):
            extra_values.append(0.0)
        metric_actitivy_array = [getattr(i, attribute_) for i in contributions]
        metric_actitivy_array = metric_actitivy_array + extra_values
        metric_actitivy_array.append(getattr(self, attribute_))
        return metric_actitivy_array

    @property
    def commit_activity(self):
        return self.metric_activity('commits')

    @property
    def file_activity(self):
        return self.metric_activity('files')

    @property
    def cloc_activity(self):
        return self.metric_activity('cloc')

    def calculate_boosting_factor(self, activity_array):
        if not activity_array or len(activity_array) == 1:
            return 0.0
        mean_value = np.mean(activity_array)
        min_value = np.min(activity_array)
        max_value = np.max(activity_array)

        numerator = (mean_value - min_value)

        if numerator == 0.0:
            return 0.0
        try:
            return numerator / (max_value - min_value)
        except ZeroDivisionError:
            return 0.0

    def save(self, *args, **kwargs):
        if self.directory_report.tag.previous_tag:
            previous_individual_contribution = IndividualContribution.objects.filter(
                directory_report__directory_id=self.directory_report.directory.id,
                directory_report__tag_id__lte=self.directory_report.tag.previous_tag.id,
                author_id=self.author.id).order_by("-directory_report__tag_id")
            if previous_individual_contribution.count() > 0:
                previous_individual_contribution = previous_individual_contribution[0]
                self.previous_individual_contribution = previous_individual_contribution

        # Verify
        # ProjectReport.objects.filter(tag__project_id=self.project_report.tag.project.id).first().tag.id
        first_tag_id = Tag.objects.filter(project_id=self.directory_report.tag.project.id).first().id
        current_tag_id = self.directory_report.tag.id
        if current_tag_id == first_tag_id:
            self.commit_exp = self.ownership_commits
            self.file_exp = self.ownership_files
            self.cloc_exp = self.ownership_cloc
            self.experience_bf = 0.4 * self.commit_exp + 0.4 * self.file_exp + 0.2 * self.cloc_exp
            self.experience = self.experience_bf
        else:
            commit_activity = self.metric_activity("commits")
            file_activity = self.metric_activity("files")
            cloc_activity = self.metric_activity("cloc")

            # commit activity
            self.bf_commit = self.calculate_boosting_factor(commit_activity)
            # file activity
            self.bf_file = self.calculate_boosting_factor(file_activity)
            # cloc_activity
            self.bf_cloc = self.calculate_boosting_factor(cloc_activity)

            denominator = len(commit_activity)
            self.commit_exp = (self.bf_commit + 1) * (sum(commit_activity) / denominator)
            # self.commit_exp = (self.bf_commit + 1) * self.ownership_commits/denominator
            self.file_exp = (self.bf_file + 1) * (sum(file_activity) / denominator)
            self.cloc_exp = (self.bf_cloc + 1) * (sum(cloc_activity) / denominator)
            self.experience_bf = 0.4 * self.commit_exp + 0.4 * self.file_exp + 0.2 * self.cloc_exp
            self.experience = 0.4 * (sum(commit_activity) / denominator) + 0.4 * (
                        sum(file_activity) / denominator) + 0.2 * (sum(cloc_activity) / denominator)

        # self.directory_report.experience_threshold
        super().save(*args, **kwargs)  # Call the "real" save() method.


class DirectoryReport(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='directory_reports')
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='directory_reports')
    authors = models.ManyToManyField(Developer, through=IndividualContribution)
    total_cloc = models.IntegerField(null=True, default=0)
    total_files = models.IntegerField(null=True, default=0)
    total_commits = models.IntegerField(null=True, default=0)
    cloc_threshold = models.FloatField(null=True, default=0.0)
    file_threshold = models.FloatField(null=True, default=0.0)
    commit_threshold = models.FloatField(null=True, default=0.0)
    experience_threshold = models.FloatField(null=True, default=0.0)
    standard_deviation = models.FloatField(null=True, default=0)
    mean = models.FloatField(null=True, default=0)
    median = models.FloatField(null=True, default=0)

    def __str__(self):
        return "Tag: " + self.tag.description + " - Directory: " + self.directory.name

    @classmethod
    def first_directory_report(cls):
        return DirectoryReport.objects.filter(tag__project_id=cls.tag.project.id,
                                              directory=cls.directory).order_by("id").first()

    def calculate_statistical_metrics(self):
        experiences = [c.experience_bf for c in
                       list(IndividualContribution.objects.filter(directory_report_id=self.id))]
        interval = np.array(experiences)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            if interval.any():
                self.experience_threshold = np.percentile(interval, 80)
            self.standard_deviation = np.std(experiences, ddof=1)
            self.mean = np.mean(experiences)
            self.median = np.median(experiences)
            self.save()

    # FIXME: experience_bf ? fix tests
    @property
    def core_developers_experience(self):
        core_developers = []
        contributions = list(
            IndividualContribution.objects.filter(directory_report_id=self.id).order_by("-experience_bf"))
        for contributor in contributions:
            #     # TODO: check if it makes sense
            if len(contributions) == 1:
                return [contributor.author]
            if contributor.experience_bf > self.experience_threshold:
                core_developers.append(contributor.author)
        return core_developers

    # FIXME: experience_bf ? fix tests
    @property
    def peripheral_developers_experience(self):
        peripheral_developers = []
        contributions = list(
            IndividualContribution.objects.filter(directory_report_id=self.id).order_by("-experience_bf"))
        if len(contributions) == 1:
            return peripheral_developers
        for contributor in contributions:
            if contributor.experience_bf <= self.experience_threshold:
                peripheral_developers.append(contributor.author)
        return peripheral_developers

    # FIXME: experience_bf ? fix tests
    @property
    def experience(self):
        contributions = list(
            IndividualContribution.objects.filter(directory_report_id=self.id).order_by("-experience_bf"))
        return contributions[0].experience_bf if len(contributions) > 0 else 0

    @property
    def ownership(self):
        higher_value = -1.0
        contributions = list(
            IndividualContribution.objects.filter(directory_report_id=self.id).order_by("-ownership_commits"))
        for contributor in contributions:
            if contributor.ownership_commits >= higher_value:
                higher_value = contributor.ownership_commits
        return higher_value

    @property
    def minor(self):
        minor = 0
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
        for contributor in contributions:
            if contributor.ownership_commits <= 0.05:
                minor = minor + 1
        return minor

    @property
    def major(self):
        major = 0
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
        for contributor in contributions:
            if contributor.ownership_commits > 0.05:
                major = major + 1
        return major


# FIXME: Test technical debt
class TransientModel(models.Model):
    """Inherit from this class to use django constructors and serialization but no database management"""

    def save(*args, **kwargs):
        pass  # avoid exceptions if called

    class Meta:
        abstract = True  # no table for this class
        managed = False  # no database management


class Contributor(TransientModel):
    abstract = True  # no table for this class
    managed = False  # no database management

    def __init__(self, developer):
        self.developer = developer
        self.loc_count = 0
        self.file_count = 0
        self.commit_count = 0
        self.total_loc = 0
        self.total_file = 0
        self.total_commit = 0
        self.commits = []
        self.files = []
        self.bf_commit = 0.0
        self.bf_file = 0.0
        self.bf_cloc = 0.0

    @property
    def loc_percentage(self):
        try:
            return self.loc_count / self.total_loc
        except ZeroDivisionError:
            return 0.0

    @property
    def file_percentage(self):
        try:
            return self.file_count / self.total_file
        except ZeroDivisionError:
            return 0.0

    @property
    def commit_percentage(self):
        try:
            return self.commit_count / self.total_commit
        except ZeroDivisionError:
            return 0.0

    @property
    def experience(self):
        try:
            return 0.4 * self.commit_percentage + 0.4 * self.file_percentage + 0.2 * self.loc_percentage
        except ZeroDivisionError:
            return 0.0

    # FIXME:
    @property
    def experience_bf(self):
        try:
            return 0.4 * self.bf_commit + 0.4 * self.bf_file + 0.2 * self.bf_cloc
        except ZeroDivisionError:
            return 0.0


# FIXME: Test technical debt
class ContributionByAuthorReport(TransientModel):
    abstract = True  # no table for this class
    managed = False  # no database management

    def __init__(self):
        self._commits_by_author = {}
        self._total_commits = 0
        self._total_java_files = 0
        self._total_loc = 0
        self.peripheral_developers = []
        self._core_developers_threshold_loc = 0.0
        self._core_developers_threshold_file = 0.0
        self._core_developers_threshold_commit = 0.0
        self._core_developers_threshold_experience = 0.0
        self._minor = 0
        self._major = 0

    @property
    def is_Empty(self):
        return not bool(self._commits_by_author)

    @property
    def ownership(self):
        higher_value = -1.0
        for contributor in self._commits_by_author.items():
            if contributor[1].commit_percentage >= higher_value:
                higher_value = contributor[1].commit_percentage
        return higher_value

    @property
    def minor(self):
        for contributor in self._commits_by_author.items():
            if contributor[1].commit_percentage <= 0.05:
                self._minor = self._minor + 1
        return self._minor

    @property
    def major(self):
        for contributor in self._commits_by_author.items():
            if contributor[1].commit_percentage > 0.05:
                self._major = self._major + 1
        return self._major

    @property
    def core_developers_files(self):
        core_developers = []
        for contributor in self._commits_by_author.items():
            if contributor[1].file_percentage > self._core_developers_threshold_file:
                core_developers.append(contributor[0])
        return core_developers

    @property
    def core_developers_commits(self):
        core_developers = []
        for contributor in self._commits_by_author.items():
            # TODO: check if it makes sense
            if len(self._commits_by_author) == 1:
                return [contributor[0]]
            if contributor[1].commit_percentage > self._core_developers_threshold_commit:
                core_developers.append(contributor[0])
        return core_developers

    @property
    def peripheral_developers_files(self):
        peripheral_developers = []
        for contributor in self._commits_by_author.items():
            if contributor[1].file_percentage <= self._core_developers_threshold_file:
                peripheral_developers.append(contributor[0])
        return peripheral_developers

    @property
    def peripheral_developers_commits(self):
        peripheral_developers = []
        for contributor in self._commits_by_author.items():
            if contributor[1].commit_percentage <= self._core_developers_threshold_commit:
                peripheral_developers.append(contributor[0])
        return peripheral_developers

    @property
    def core_developers_experience(self):
        core_developers = []
        for contributor in self._commits_by_author.items():
            # TODO: check if it makes sense
            if len(self._commits_by_author) == 1:
                return [contributor[0]]
            if contributor[1].experience > self._core_developers_threshold_experience:
                core_developers.append(contributor[0])
        return core_developers

    @property
    def peripheral_developers_files(self):
        peripheral_developers = []
        for contributor in self._commits_by_author.items():
            if contributor[1].file_percentage <= self._core_developers_threshold_file:
                peripheral_developers.append(contributor[0])
        return peripheral_developers

    @property
    def peripheral_developers_experience(self):
        peripheral_developers = []
        for contributor in self._commits_by_author.items():
            if contributor[1].experience <= self._core_developers_threshold_experience:
                peripheral_developers.append(contributor[0])
        return peripheral_developers

    @property
    def core_developers_threshold_file(self):
        file_count_array = []
        for contributor in self._commits_by_author.items():
            file_count_array.append(contributor[1].file_percentage)
        interval = np.array(file_count_array)
        if interval.any():
            self._core_developers_threshold_file = np.percentile(interval, 80)
        return self._core_developers_threshold_file

    @core_developers_threshold_file.setter
    def core_developers_threshold_file(self, core_developers_threshold_file):
        self._core_developers_threshold_file = core_developers_threshold_file

    @property
    def core_developers_threshold_commit(self):
        array = []
        for contributor in self._commits_by_author.items():
            array.append(contributor[1].commit_percentage)
        interval = np.array(array)
        if interval.any():
            self._core_developers_threshold_commit = np.percentile(interval, 80)
        return self._core_developers_threshold_commit

    @core_developers_threshold_commit.setter
    def core_developers_threshold_commit(self, core_developers_threshold_commit):
        self._core_developers_threshold_commit = core_developers_threshold_commit

    @property
    def core_developers_threshold_experience(self):
        experience_count_array = []
        for contributor in self._commits_by_author.items():
            experience_count_array.append(contributor[1].experience)
        interval = np.array(experience_count_array)
        if interval.any():
            self._core_developers_threshold_experience = np.percentile(interval, 80)
        return self._core_developers_threshold_experience

    @core_developers_threshold_experience.setter
    def core_developers_threshold_experience(self, core_developers_threshold_experience):
        self._core_developers_threshold_experience = core_developers_threshold_experience

    @property
    def commits_by_author(self):
        return self._commits_by_author

    @commits_by_author.setter
    def commits_by_author(self, commits_by_author):
        self._commits_by_author = commits_by_author

    @property
    def total_commits(self):
        return self._total_commits

    @total_commits.setter
    def total_commits(self, total_commits):
        for contributor in self._commits_by_author.items():
            # set total_commits in every ocurrence of contributor inside commits_by_author dictionary
            contributor[1].total_commit = total_commits
        self._total_commits = total_commits

    @property
    def previous_total_commits(self):
        return self.previous_total_commits

    @property
    def total_java_files(self):
        return self._total_java_files

    @total_java_files.setter
    def total_java_files(self, total_java_files):
        for contributor in self._commits_by_author.items():
            contributor[1].total_file = total_java_files
        self._total_java_files = total_java_files

    @property
    def previous_total_files(self):
        return self.previous_total_files

    @property
    def total_loc(self):
        return self._total_loc

    @total_loc.setter
    def total_loc(self, total_loc):
        for contributor in self._commits_by_author.items():
            # set total_commits in every ocurrence of contributor inside commits_by_author dictionary
            contributor[1].total_loc = total_loc
        self._total_loc = total_loc

    @property
    def previous_total_cloc(self):
        return self.previous_total_cloc


# FIXME: Test technical debt
class MetricsReport(TransientModel):
    abstract = True  # no table for this class
    managed = False  # no database management

    def __init__(self, commit, file, cloc, bf_commit, bf_file, bf_cloc, commit_exp, file_exp, cloc_exp, metric_exp,
                 metric_exp_bf):
        self._commit = commit
        self.file = file
        self.cloc = cloc
        self.bf_commit = bf_commit
        self.bf_file = bf_file
        self.bf_cloc = bf_cloc
        self.commit_exp = commit_exp
        self.file_exp = file_exp
        self.cloc_exp = cloc_exp
        self.metric_exp = metric_exp
        self.metric_exp_bf = metric_exp_bf
        self._empty = False

    def __str__(self):
        return "oi"

    @property
    def commit(self):
        return self._commit

    @property
    def empty(self):
        return self._empty

    @empty.setter
    def empty(self, empty):
        self._empty = empty


# FIXME: Test technical debt
# method for updating
@receiver(post_save, sender=Commit, dispatch_uid="update_commit")
def update_commit(sender, instance, **kwargs):
    lista = instance.parents_str.split(",")
    for parent_hash in lista:
        parent = Commit.objects.filter(hash=parent_hash)
        if parent.count() > 0:
            parent = parent[0]
            parent.children_commit = instance
            instance.parent = parent
            parent.save(update_fields=['children_commit'])


# FIXME: Test technical debt
def count_uncommented_lines(code):
    total_lines = code.count('\n')
    commented_lines = 0
    blank_lines = 0
    uncommented_lines = 0
    if total_lines > 0:
        # FIXME: Put this part on loop below
        lines = code.split("\n")
        for line in lines:
            m = re.search(r"\u002F/.*", line)
            found = ''
            if m:
                found = m.group(0)
                if found:
                    line = re.sub(r'\u002F/.*', '', line)
                    line.replace(' ', '', 1)
                    if line.strip().isdigit():
                        commented_lines += 1
        uncommented_lines -= commented_lines

        comments = []

        comments = [x.group() for x in
                    re.finditer(r"(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n]))){0,100}\*+\/)|\/{0,1}\*[^;][^\r\n]*", code)]
        part_without_comment = code
        for comment in comments:
            part_without_comment = part_without_comment.replace(comment, '', 1)

        blank_lines += count_blank_lines(part_without_comment)
        uncommented_lines += part_without_comment.count('\n')
        uncommented_lines -= blank_lines
    return 0 if uncommented_lines < 0 else uncommented_lines


# FIXME: Test technical debt
def count_blank_lines(code):
    blank_lines = 0
    lines = code.split('\n')
    for line in lines[1:]:
        if not line.strip():
            blank_lines += 1
        elif line.replace(" ", "").isdigit():
            blank_lines += 1
    return blank_lines
