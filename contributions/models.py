from django.db import models
import numpy as np

# Create your models here.
from pydriller import GitRepository


class Developer(models.Model):
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)

    def __str__(self):
        return self.name + '('+self.email+')'

class Project(models.Model):
    project_name = models.CharField(max_length=200)
    project_path = models.CharField(max_length=200)

    def __str__(self):
        return self.project_name

class Tag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tags')
    description = models.CharField(max_length=100)
    # previous_tag = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, default=None)
    previous_tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True, default=None)

    def __str__(self):
        return self.description

class Directory(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='directories')
    # parent_tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='directories')
    visible = models.BooleanField(default=True)


    def __str__(self):
        return self.name + " - Visible: " + str(self.visible)

class Commit(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='commits')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='commits')
    hash = models.CharField(max_length=300)
    msg = models.CharField(max_length=300)
    author = models.ForeignKey(Developer, related_name='author_id', on_delete=models.CASCADE)
    author_date = models.DateField()
    committer = models.ForeignKey(Developer, related_name='committer_id', on_delete=models.CASCADE)
    committer_date = models.DateField()
    # pub_date = models.DateTimeField('date published')

    # def __eq__(self, other):
    # 	return isinstance(other, self.__class__) and self.hash == other.hash

    @property
    def number_of_java_files(self):
        total_java_files = 0
        for modification in self.modifications.all():
            if modification.is_java_file:
                total_java_files = total_java_files + 1
        return total_java_files


    def directories2(self):

        directoriesD =list()

        for modification in self.modifications.all():
            if modification.is_java_file:
                if modification.directory not in directoriesD:
                    directoriesD.append(modification.directory)
        return directoriesD


class Method(models.Model):
    name = models.CharField(max_length=150)

class Modification(models.Model):
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='modifications')
    old_path = models.CharField(max_length=200, null=True)
    new_path = models.CharField(max_length=200, null=True)
    path = models.CharField(max_length=200, null=True, default="-")
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='modifications')
    # directory = models.CharField(max_length=200, null=True, default="-")
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
    diff = models.TextField()
    source_code = models.TextField(null=True)
    source_code_before = models.TextField(null=True)
    added = models.IntegerField(null=True)
    removed = models.IntegerField(null=True)
    cloc = models.IntegerField(default=0)
    nloc = models.IntegerField(null=True)
    complexity = models.IntegerField(null=True)
    # token_count = models.CharField(max_length=200,null=True)

    # def __eq__(self, other):
    # 	return isinstance(other, self.__class__) and (self.commit.hash == other.commit.hash and self.file == other.file)

    def __diff_text__(self):
        GR = GitRepository(self.commit.project.project_path)

        parsed_lines = GR.parse_diff(self.diff)

        return parsed_lines

    def __print_text_in_lines__(self, text, result, type_symbol):
        for line in text:
            result = result + "\n" + str(line[0]) + ' ' + type_symbol + ' ' + line[1]
        return result

    @property
    def diff_added(self):

        parsed_lines = self.__diff_text__()

        added_text = parsed_lines['added']

        diff_text = None

        diff_text = '\n' + str(self.added) + ' lines added: \n'  # result: Added: [(4, 'log.debug("b")')]
        # diff_text = str(self.added) + ' + | {}'.format(added_text)  # result: Added: [(4, 'log.debug("b")')]
        diff_text = self.__print_text_in_lines__(added_text,diff_text, '+')

        return diff_text

    @property
    def diff_removed(self):

        deleted_text = self.__diff_text__()['deleted']
        diff_text = '\n' + str(self.removed) + ' lines removed:  \n'
        diff_text = self.__print_text_in_lines__(deleted_text,diff_text, '-')

        return diff_text

    @property
    def file(self):
        index = self.path.rfind("/")
        if index > -1:
            return self.path[index+1:]
        return self.path

    @property
    def is_java_file(self):
        if self.path:
            index = self.path.rfind(".")
            if index > -1:
                return self.path[index:] == ".java"
        return False


    def save(self, *args, **kwargs):
        if self.old_path:
            self.old_path = self.old_path.replace("\\","/")
        if self.new_path:
            self.new_path = self.new_path.replace("\\", "/")
        if self.change_type.name == 'DELETE':
            self.path = self.old_path
        else:
            self.path = self.new_path


        index = self.path.rfind("/")
        directory_str = ""
        if index > -1:
            directory_str = self.path[:index]
        else:
            directory_str = "/"

        # directory = Directory.objects.filter(name=directory_str)
        # if directory.count() == 0:
        # 	author = Directory(name=directory_str, email=commit_repository.author.email)
        # 	author.save()
        # else:
        # 	author = directory[0]

        # self.delta = abs(self.added-self.removed)
        self.cloc = self.added + self.removed
        super().save(*args, **kwargs)  # Call the "real" save() method.

class IndividualContribution(models.Model):
    author = models.ForeignKey(Developer, on_delete=models.DO_NOTHING)
    directory_report = models.ForeignKey('DirectoryReport', on_delete=models.DO_NOTHING)
    cloc = models.IntegerField(null=True, default=0)
    files = models.IntegerField(null=True, default=0)
    commits = models.IntegerField(null=True, default=0)
    # previous_total_commits = models.IntegerField(null=True, default=0)
    ownership_cloc = models.FloatField(null=True, default=0.0)
    ownership_cloc_in_this_tag = models.FloatField(null=True, default=0.0)
    cloc_exp = models.FloatField(null=True, default=0.0)
    ownership_files = models.FloatField(null=True, default=0.0)
    ownership_files_in_this_tag = models.FloatField(null=True, default=0.0)
    file_exp = models.FloatField(null=True, default=0.0)
    ownership_commits = models.FloatField(null=True, default=0.0)
    ownership_commits_in_this_tag = models.FloatField(null=True, default=0.0)
    commit_exp = models.FloatField(null=True, default=0.0)
    experience = models.FloatField(null=True, default=0.0)
    experience_bf = models.FloatField(null=True, default=0.0)
    abs_experience = models.FloatField(null=True, default=0.0)
    bf_commit = models.FloatField(null=True, default=0.0)
    bf_file = models.FloatField(null=True, default=0.0)
    bf_cloc = models.FloatField(null=True, default=0.0)

    def calculate_boosting_factor(self,activity_array):
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
        self.ownership_commits_in_this_tag = self.ownership_commits
        self.ownership_files_in_this_tag = self.ownership_files
        self.ownership_cloc_in_this_tag = self.ownership_cloc
        total_commits = 0
        total_files = 0
        total_cloc = 0
        if self.directory_report.tag.previous_tag:
            previous_individual_contribution = IndividualContribution.objects.filter(directory_report__directory_id=self.directory_report.directory.id, directory_report__tag_id=self.directory_report.tag.previous_tag.id, author_id=self.author.id)
            commits_in_this_tag = self.commits
            files_in_this_tag = self.files
            cloc_in_this_tag = self.cloc
            if previous_individual_contribution.count() > 0:
                previous_individual_contribution = previous_individual_contribution[0]
                commits_in_this_tag = commits_in_this_tag - previous_individual_contribution.commits
                files_in_this_tag = files_in_this_tag - previous_individual_contribution.files
                cloc_in_this_tag = cloc_in_this_tag - previous_individual_contribution.cloc
                total_commits = previous_individual_contribution.directory_report.total_commits
                total_files = previous_individual_contribution.directory_report.total_files
                total_cloc = previous_individual_contribution.directory_report.total_cloc
            else:
                directory_report = DirectoryReport.objects.filter(directory_id=self.directory_report.directory.id,
                                               tag_id=self.directory_report.tag.previous_tag.id)
                if directory_report.count() > 0:
                    directory_report = directory_report[0]
                    total_commits = directory_report.total_commits
                    total_files = directory_report.total_files
                    total_cloc = directory_report.total_cloc

            total_commits_in_this_tag = self.directory_report.total_commits - total_commits
            total_files_in_this_tag = self.directory_report.total_files - total_files
            total_cloc_in_this_tag = self.directory_report.total_cloc - total_cloc
            try:
                self.ownership_commits_in_this_tag = commits_in_this_tag/total_commits_in_this_tag
                self.ownership_files_in_this_tag = files_in_this_tag/total_files_in_this_tag
                self.ownership_cloc_in_this_tag = cloc_in_this_tag/total_cloc_in_this_tag
            except ZeroDivisionError:
                self.ownership_commits_in_this_tag = 0.0
                self.ownership_files_in_this_tag = 0.0
                self.ownership_cloc_in_this_tag = 0.0

        first_tag_id = Tag.objects.filter(project_id=self.directory_report.directory.project.id).first().id
        current_tag_id = self.directory_report.tag.id
        if current_tag_id == first_tag_id:
            self.commit_exp = self.ownership_commits
            self.file_exp = self.ownership_files
            self.cloc_exp = self.ownership_cloc
            self.experience_bf = 0.4 * self.commit_exp + 0.4 * self.file_exp + 0.2 * self.cloc_exp
            self.experience = self.experience_bf
        else:
            tag_ids = list(range(first_tag_id,current_tag_id))

            contributions = IndividualContribution.objects.filter(directory_report__directory_id=self.directory_report.directory.id, directory_report__tag_id__in=tag_ids, author_id=self.author.id)

            first_tag__in_contributions_id = contributions.first().directory_report.tag.id if contributions else current_tag_id

            extra_values = []
            # whether there is any contribution in this directory from other authors
            # It means that is not a new directory, so we have to count all period
            first_report = DirectoryReport.objects.filter(tag_id__lt=current_tag_id, directory_id=self.directory_report.directory.id).order_by("tag_id").first()
            if first_report:
                i=len(contributions)
                if current_tag_id-i>1:
                    for i in range(0,current_tag_id-(first_report.tag.id+len(contributions))):
                        extra_values.append(0.0)

            contributions = list(contributions)
            contributions.append(self)

            commit_activity = [i.ownership_commits_in_this_tag for i in contributions]
            commit_activity = commit_activity + extra_values

            file_activity = [i.ownership_files_in_this_tag for i in contributions]
            file_activity = file_activity + extra_values
            # file_activity.append(self.ownership_files)
            #
            cloc_activity = [i.ownership_cloc_in_this_tag for i in contributions]
            cloc_activity = cloc_activity + extra_values
            # cloc_activity.append(self.ownership_cloc)


            # commit activity
            self.bf_commit = self.calculate_boosting_factor(commit_activity)
            # file activity
            self.bf_file = self.calculate_boosting_factor(file_activity)
            # cloc_activity
            self.bf_cloc = self.calculate_boosting_factor(cloc_activity)
            # denominator = len(contributions)+1 if len(contributions) != 0 else 1

            # denominator = current_tag_id-first_tag__in_contributions_id
            # denominator = denominator + 1
            denominator = len(contributions) + len(extra_values)
            self.commit_exp = (self.bf_commit + 1)*(sum(commit_activity)/denominator)
            # self.commit_exp = (self.bf_commit + 1) * self.ownership_commits
            self.file_exp = (self.bf_file + 1)*self.ownership_files
            self.cloc_exp = (self.bf_cloc + 1)*self.ownership_cloc
            self.experience_bf = 0.4*self.commit_exp + 0.4*self.file_exp + 0.2*self.cloc_exp
            self.experience = 0.4*self.ownership_commits + 0.4*self.ownership_files + 0.2*self.ownership_cloc

            # self.directory_report.experience_threshold
        super().save(*args, **kwargs)  # Call the "real" save() method.

class DirectoryReport(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.DO_NOTHING, related_name='directory_reports')
    directory = models.ForeignKey(Directory, on_delete=models.DO_NOTHING, related_name='directory_reports')
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


    def calculate_statistical_metrics(self):
        experiences = [c.experience for c in list(IndividualContribution.objects.filter(directory_report_id=self.id))]
        interval = np.array(experiences)
        if interval.any():
            self.experience_threshold = np.percentile(interval, 80)
        self.standard_deviation = np.std(experiences, ddof=1)
        self.mean = np.mean(experiences)
        self.median = np.median(experiences)
        self.save()

    @property
    def core_developers_experience(self):
        core_developers = []
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
        for contributor in contributions:
        #     # TODO: check if it makes sense
            if len(contributions) == 1:
                return [contributor.author]
            if contributor.experience > self.experience_threshold:
                core_developers.append(contributor.author)
        return core_developers

    @property
    def peripheral_developers_experience(self):
        peripheral_developers = []
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
        for contributor in contributions:
            if contributor.experience <= self.experience_threshold:
                peripheral_developers.append(contributor.author)
        return peripheral_developers

    @property
    def experience(self):
        higher_value = -1.0
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
        for contributor in contributions:
            if contributor.experience >= higher_value:
                higher_value = contributor.experience
        return higher_value

    @property
    def abs_experience(self):
        higher_value = -1.0
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
        for contributor in contributions:
            if contributor.abs_experience >= higher_value:
                higher_value = contributor.abs_experience
        return higher_value

    @property
    def ownership(self):
        higher_value = -1.0
        contributions = list(IndividualContribution.objects.filter(directory_report_id=self.id))
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

    def __init__(self,developer):
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
            return self.loc_count/self.total_loc
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
            return 0.4*self.commit_percentage + 0.4 * self.file_percentage + 0.2*self.loc_percentage
        except ZeroDivisionError:
            return 0.0

    @property
    def abs_experience(self):
        try:
            return 0.4 * self.commit_count + 0.4 * self.total_loc + 0.2 * self.loc_count
        except ZeroDivisionError:
            return 0.0

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


class MetricsReport(TransientModel):
    abstract = True  # no table for this class
    managed = False  # no database management

    def __init__(self, commit, file, cloc, bf_commit, bf_file, bf_cloc, commit_exp, file_exp, cloc_exp, metric_exp, metric_exp_bf):
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