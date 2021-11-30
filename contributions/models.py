# standard library
import logging
import re

# third-party
# Django
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from pydriller import GitRepository

# local Django
from common.utils import CommitUtils

AUTHOR_FILTER = ["Peter Donald"]
HASH_FILTER = ["550a4ef1afd7651dc20110c0b079fb03665ca9da", "8f3a71443bd538c96207db05d8616ba14d7ef23b",
               "390398d38e4fd0d195c91a384f6198a1528bb317", "8ca32df08e5021d144ebfa8b85da7879143c01ae",
               "e2da258a16359a7112669ef27c8510cde3d860c7", "c0c176e89263cfc34705b1c7423aa0528b421959",
               "7002aa3c760699ccac9f90d63fbbbf912a033b0b", "6b3f22f56b81ba6471a9405b78600b3bb7cfcf1f",
               "c07bd866840a1757f03ed57c5e376b9c5af4ed52", "21de7add9a935c4ae61716cce269f58db26e949a",
               "538b7c9ffee7a18064f7726c8b20faf681adb218", "7a6d765e011398468e4b755b4b5acba0fc6ef41f",
               "1de4dfa58f198e1590294951183ff61210d48549", "0c4f5b1b629f96ffda3d4aca672e10c40b55bf0b",
               "ba9a8832d043d876fd18b2027cc933fc6689ca9c", "2e84be2474b10adb04c13fc622483be04ee3be4d",
               "6fcbf9b848c63465d26a40387a9be212e708f80b"]
ANT = 1
LUCENE = 2
MAVEN = 3
OPENJPA = 4
CASSANDRA = 5
HADOOP = 6

filter_outliers = {"author": AUTHOR_FILTER, "hash": HASH_FILTER}

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


class Developer(models.Model):
    name = models.CharField(max_length=200)
    login = models.CharField(max_length=60, default='')
    email = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.name} (login: {self.login}, email: {self.email})'


class Project(models.Model):
    project_name = models.CharField(max_length=200)
    project_path = models.CharField(max_length=200)
    main_branch = models.CharField(max_length=80, default='master')

    def __str__(self):
        return self.project_name

    @property
    def first_tag(self):
        return self.tags.all().first()


class Tag(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tags')
    description = models.CharField(max_length=100)
    real_tag_description = models.CharField(max_length=100, default='')
    # or stable
    major = models.BooleanField(default=True)
    max_minor_version_description = models.TextField(default='')
    previous_tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True, blank=True)
    delta_rmd_components = models.FloatField(null=True, default=0.0)
    build_command = models.CharField(max_length=399, default='ant compile')
    prepare_build_command = models.CharField(max_length=800, null=True)
    core_component = models.CharField(max_length=280, default='')
    main_directory = models.CharField(max_length=280, default='')
    v1_1 = 1

    @property
    def minors(self):
        return [x.strip() for x in
                self.max_minor_version_description.split(',')] if self.max_minor_version_description != '' else []

    @staticmethod
    def line_major_versions(project_id):
        return Tag.objects.filter(major=True, project_id=project_id).values_list('id', flat=True)

    @staticmethod
    def line_base():
        line1_9_x = Tag.objects.get(description='rel/1.9.x').pk
        line1_10_0 = Tag.objects.get(description='rel/1.10.0').pk
        return [i for i in Tag.line_major_versions() if i != line1_9_x and i != line1_10_0]

    @staticmethod
    def line_1_10_x():
        return Tag.line_base().append(Tag.objects.get(description='rel/1.10.0').pk)

    @staticmethod
    def line_1_9_x():
        return Tag.line_base().append(Tag.objects.get(description='rel/1.9.x').pk)

    @property
    def main_directory_prefix(self):
        return self.main_directory + '/'

    def __str__(self):
        return f'{self.project.project_name}: {self.description}'

    @property
    def pre_build_commands(self):
        commands = self.prepare_build_command.split(',')
        return [c.strip() for c in commands]


class Directory(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='directories')
    visible = models.BooleanField(default=False)
    initial_commit = models.ForeignKey('Commit', on_delete=models.CASCADE, related_name='starter_directories',
                                       null=True)

    def __str__(self):
        return self.name + " - Visible: " + str(self.visible)

    def belongs_to_component(self, path):
        return self.name == path or (path.startswith(self.name) and not Directory.objects.filter(name__exact=self.name,
                                                                                                 visible=True).exists())


class NoOutlierCommitManager(models.Manager):
    def get_queryset(self):
        ids = []
        commit_ids = []
        # FIXME: Generalize for all projects
        # ANT
        for author in AUTHOR_FILTER:
            author_db = Developer.objects.get(name=author)
            if author_db:
                ids.append(author_db.id)
        for hash in HASH_FILTER:
            try:
                hash_db = Commit.objects.get(hash=hash)
                if hash_db:
                    commit_ids.append(hash_db.id)
            except Commit.DoesNotExist:
                pass
        return super().get_queryset().exclude(author_id__in=ids).exclude(id__in=commit_ids)


class Commit(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='commits')
    real_tag_description = models.CharField(max_length=300, default="", blank=True, null=True)
    children_commit = models.ForeignKey('Commit', on_delete=models.SET_NULL, related_name='parent_rel', null=True,
                                        default=None)
    previous_impactful_commit = models.ForeignKey('Commit', on_delete=models.SET_NULL,
                                                  related_name='previous_impactful_commit_rel', null=True,
                                                  default=None, blank=True)
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
    has_submitted_by = models.BooleanField(default=False)

    # key: tag_id, value: sum of u_cloc of all commits by this author in this tag
    changed_architecture = models.BooleanField(default=False)
    cloc_activity = models.IntegerField(default=0)
    compilable = models.BooleanField(default=False)
    _parents = []
    # mean rmd
    mean_rmd_components = models.FloatField(null=True, default=0.0)
    # standard deviation rmd
    std_rmd_components = models.FloatField(null=True, default=0.0)
    # delta
    delta_rmd_components = models.FloatField(null=True, default=0.0)
    # normalized_delta
    normalized_delta = models.FloatField(null=True, default=0.0)

    objects = models.Manager()  # The default manager.
    no_outliers_objects = NoOutlierCommitManager()  # The specific manager.

    def __str__(self):
        return str(
            self.pk) + " - hash: " + self.hash + " - Author: " + self.author.name + " - Tag: " + self.tag.description

    @property
    def has_impact_loc(self):
        for mod in self.modifications.all():
            if mod.has_impact_loc:
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
        for metric in self.component_commits.all():
            delta += metric.delta_rmd
        return delta

    @property
    def is_author_newcomer(self):
        return (self.author_seniority / 365) <= 1 or self.has_submitted_by

    def non_blank_cloc(self, directory):
        cloc = 0
        for mod in self.modifications.all():
            # if mod.directory == directory:
            if directory.belongs_to_component(mod.directory.name):
                cloc += mod.u_cloc
        return cloc

    @property
    def delta_rmd(self):
        return self.delta_rmd_components

    def update_component_commits(self):
        for component in self.component_commits.all():
            component.calculate_experience()

    def save(self, *args, **kwargs):
        self.author.save()
        self.committer.save()

        for hash in self.parents:
            parent = Commit.objects.filter(hash=hash)
            if parent.count() > 0:
                self.parent = parent[0]

        if self.pk is None:

            m = re.search(
                r'\Submitted\s*([bB][yY])[:]*\s*[\s\S][^\r\n]*[a-zA-Z0-9_.+-]+((\[|\(|\<)|(\s*(a|A)(t|T)\s*|@)[a-zA-Z0-9-]+(\s*(d|D)(O|o)(t|T)\s*|\.)[a-zA-Z0-9-.]+|(\)|\>|\]))',
                self.msg, re.IGNORECASE)
            found = ''
            if m:
                found = m.group(0)
                if found:
                    self.has_submitted_by = True

            previous_commit = Commit.objects.filter(author=self.author, tag_id__lte=self.tag.id,
                                                    tag__project=self.tag.project).last()

            first_commit = Commit.objects.filter(author=self.author, has_submitted_by=False, tag_id__lte=self.tag.id,
                                                 tag__project=self.tag.project).first()

            self.total_commits = previous_commit.total_commits if previous_commit is not None else 0

            self.cloc_activity = 0
            if previous_commit is not None:
                self.cloc_activity = previous_commit.cloc_activity

            if first_commit is not None:
                self.author_seniority = self.author_date - first_commit.author_date
                self.author_seniority = abs(self.author_seniority.days)

            self.author_experience = 0.0

            file_by_authors = Modification.objects.none()
            if self.total_commits > 0:
                file_by_authors = Modification.objects.filter(commit__author=self.author,
                                                              commit__tag_id__lte=self.tag.id,
                                                              commit__tag__project=self.tag.project,
                                                              commit_id__lte=previous_commit.id)

            files = file_by_authors.values("path").distinct().count()

            self.author_experience = 0.2 * self.total_commits + 0.4 * files + 0.4 * self.cloc_activity
            self.total_commits += 1

            logger.info("###")
            logger.info(f'Cadastrando commit: {self.hash}')
            logger.info(f'Versao: {self.tag.__str__()}')
            logger.info(f'Autor: {self.author.name}')

        super(Commit, self).save(*args, **kwargs)  # Call the "real" save() method.

    class Meta:
        ordering = ['tag_id', 'id']


class NoOutlierMetricManager(models.Manager):
    def get_queryset(self):
        ids = []
        for author in AUTHOR_FILTER:
            author_db = Developer.objects.get(name=author)
            if author_db:
                ids.append(author_db.id)
        return super().get_queryset().exclude(commit__author_id__in=ids)


class ComponentCommit(models.Model):
    component = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='component_commits')
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='component_commits')
    author_experience = models.FloatField(null=True, default=0.0)
    cloc_accumulation = models.IntegerField(default=0)
    commits_accumulation = models.IntegerField(default=0)
    commit_str = models.CharField(max_length=200, default="", blank=True, null=True)
    # mean rmd
    rmd = models.FloatField(null=True, default=0.0)
    # delta
    delta_rmd = models.FloatField(null=True, default=0.0)

    objects = models.Manager()  # The default manager.
    no_outliers_objects = NoOutlierMetricManager()  # The specific manager.

    def __str__(self):
        return self.component.name + ', Commit id: ' + str(self.commit.id) + ', Autor: ' + self.commit.author.name

    def calculate_experience(self):
        previous_component_commit = ComponentCommit.objects.filter(commit__author=self.commit.author,
                                                                   component=self.component,
                                                                   commit__id__lt=self.commit.id,
                                                                   commit__tag__project=self.commit.tag.project).last()
        file_by_authors = Modification.objects.none()

        # because components are saved directly
        if previous_component_commit is not None:
            self.commits_accumulation = previous_component_commit.commits_accumulation
            self.cloc_accumulation = previous_component_commit.cloc_accumulation
            # because Modification model imply any directory whether they are components or not
            file_by_authors = Modification.objects.filter(commit__author=self.commit.author,
                                                          commit__tag_id__lte=self.commit.tag.id,
                                                          commit_id__lt=self.commit.id,
                                                          commit__tag__project=self.commit.tag.project,
                                                          directory=self.component)
        files = file_by_authors.values("path").distinct().count()

        self.author_experience = 0.2 * self.commits_accumulation + \
                                 0.4 * files + \
                                 0.4 * self.cloc_accumulation

        self.commits_accumulation += 1
        self.cloc_accumulation += self.commit.non_blank_cloc(self.component)
        self.save()


class Modification(models.Model):
    old_path = models.CharField(max_length=200, null=True)
    new_path = models.CharField(max_length=200, null=True)
    path = models.CharField(max_length=200, null=True, default="")
    commit = models.ForeignKey(Commit, on_delete=models.CASCADE, related_name='modifications')
    directory = models.ForeignKey(Directory, on_delete=models.CASCADE, related_name='modifications')
    component_commit = models.ForeignKey(ComponentCommit, on_delete=models.CASCADE, related_name='modifications')
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
    has_impact_loc = models.BooleanField(default=False)

    nloc = models.IntegerField(default=0, null=True)
    complexity = models.IntegerField(null=True)

    def __str__(self):
        return "Commit: " + self.commit.hash + " - Directory: " + self.directory.name + " - File name: " + self.file

    def __diff_text(self):
        GR = GitRepository(self.commit.tag.project.project_path)

        parsed_lines = GR.parse_diff(self.diff)

        return parsed_lines

    def __print_text_in_lines(self, text, result, type_symbol):
        for line in text:
            result = result + "\n" + str(line[0]) + ' ' + type_symbol + ' ' + line[1]
        return result

    def __cloc_uncommented__(self):
        diff_text = self.__diff_text()
        added_text = self.__print_text_in_lines(diff_text['added'], "", "")
        deleted_text = self.__print_text_in_lines(diff_text['deleted'], "", "")

        added_uncommented_lines = count_loc(added_text)
        deleted_uncommented_lines = count_loc(deleted_text)
        return added_uncommented_lines + deleted_uncommented_lines

    def has_impact_loc_calculation(self):
        diff_text = self.__diff_text()
        added_text = self.__print_text_in_lines(diff_text['added'], "", "")
        deleted_text = self.__print_text_in_lines(diff_text['deleted'], "", "")

        added_uncommented_lines = detect_impact_loc(added_text)
        deleted_uncommented_lines = detect_impact_loc(deleted_text)
        return added_uncommented_lines or deleted_uncommented_lines

    @property
    def diff_added(self):
        parsed_lines = self.__diff_text()
        added_text = parsed_lines['added']

        diff_text = None
        diff_text = '\n' + str(self.added) + ' lines added: \n'  # result: Added: [(4, 'log.debug("b")')]
        diff_text = self.__print_text_in_lines(added_text, diff_text, '+')

        return diff_text

    @property
    def diff_removed(self):
        deleted_text = self.__diff_text()['deleted']
        diff_text = '\n' + str(self.removed) + ' lines removed:  \n'
        diff_text = self.__print_text_in_lines(deleted_text, diff_text, '-')

        return diff_text

    @property
    def file(self):
        index = self.path.rfind("/")
        if index > -1:
            return self.path[index + 1:]
        return self.path

    @property
    def is_java_file(self):
        return CommitUtils.is_java_file(self.path)

    def save(self, *args, **kwargs):

        self.path = CommitUtils.true_path(self)
        self.has_impact_loc = self.has_impact_loc_calculation()

        if self.is_java_file:
            self.u_cloc = self.__cloc_uncommented__()

            if self.commit.pk is None:
                self.commit.save()

            index = self.path.rfind("/")
            directory_str = ""
            if index > -1:
                directory_str = self.path[:index]
            else:
                directory_str = "/"

            directory = Directory.objects.filter(name__iexact=directory_str)
            if directory.count() == 0:
                directory = Directory(name=directory_str, project=self.commit.tag.project,
                                      initial_commit=self.commit)
                directory.save()
                self.directory = directory
            else:
                self.directory = directory[0]

            component_commit_repo = ComponentCommit.objects.filter(component=self.directory, commit=self.commit)
            if component_commit_repo.exists():
                self.component_commit = component_commit_repo[0]
            else:
                self.component_commit = ComponentCommit(component=self.directory, commit=self.commit)
                self.component_commit.save()

            self.cloc = self.added + self.removed
            self.commit.cloc_activity += self.u_cloc
            self.commit.save()

            super(Modification, self).save(*args, **kwargs)  # Call the "real" save() method.


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


def detect_impact_loc(code):
    total_lines = code.count('\n')
    if total_lines > 0:
        commented_lines = 0
        # FIXME: Put this part on loop below
        lines = code.split("\n")
        # In case we should consider commented lines
        for line in lines:
            m = re.search(r"\u002F/.*", line)
            n = re.search(
                r'(\/\*([^*]|[\r\n]|(\*+([^*\/]|[\r\n]))){0,100}\*+\/)|\/{0,1}[^0-9][a-zA-Z]*\*[^;]([^0-9][a-zA-Z]+)[^\r\n]*',
                line)
            if m or n:
                if m:
                    found = m.group(0)
                    line = line.replace(found, '')
                    line.replace(' ', '', 1)
                    if line.strip().isdigit():
                        commented_lines += 1
                        continue
                    else:
                        return True
                elif n:
                    found = n.group(0)
                    line = line.replace(found, '')
                    line.replace(' ', '', 1)
                    if line.strip().isdigit():
                        commented_lines += 1
                    else:
                        return True
            elif not line.replace(" ", "").isdigit() and (line != '' and line != '\n'):
                return True

    return False


def count_loc(code):
    total_lines = code.count('\n')
    return total_lines - __count_blank_lines(code)


# FIXME: Test technical debt
def __count_blank_lines(code):
    blank_lines = 0
    lines = code.split('\n')
    for line in lines[1:]:
        if not line.strip():
            blank_lines += 1
        elif line.replace(" ", "").isdigit():
            blank_lines += 1
    return blank_lines


def __prepare_diff_text(text, result, type_symbol):
    for line in text:
        result = result + "\n" + str(line[0]) + ' ' + type_symbol + ' ' + line[1]
    return result


def __has_impact_loc_calculation_static_method(diff):
    added_text = __prepare_diff_text(diff['added'], "", "")
    deleted_text = __prepare_diff_text(diff['deleted'], "", "")
    return detect_impact_loc(added_text) or detect_impact_loc(deleted_text)
