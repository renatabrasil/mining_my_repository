# standard library
import logging
import os
import re
import subprocess

import numpy as np
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from pydriller import GitRepository

from common.constants import CommonsConstantsUtils
from common.utils import CommitUtils
# local Django
from contributions.constants import RegexConstants
from contributions.helpers.models_helper import detect_impact_loc, count_loc

# third-party
# Django

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

filter_outliers = {"author": AUTHOR_FILTER, "hash": HASH_FILTER}

logger = logging.getLogger(__name__)
logger.setLevel(level=logging.INFO)


class Developer(models.Model):
    name = models.CharField(max_length=200)
    login = models.CharField(max_length=60, default='')
    email = models.CharField(max_length=200)

    @classmethod
    def create(cls, name="", email="", login=""):
        developer = cls(name=CommitUtils.strip_accents(name).strip(), email=email.lower(), login=login.lower())
        return developer

    def __str__(self):
        return f'{self.name} (login: {self.login}, email: {self.email})'

    def format_data(self, message: str, is_consider_submitted_by: bool = False):
        author_name = self.name

        if is_consider_submitted_by:
            match = re.search(RegexConstants.SUBMITTED_BY__PARTICLE_REGEX, message, re.IGNORECASE)
            if match:
                found = match.group(0)
                if found:
                    author_and_email = re.sub(RegexConstants.SUBMITTED_BY_SIMPLE__REGEX, '', found)
                    author_name = re.sub(RegexConstants.NAME_PATTERN__REGEX, '', author_and_email)

                    email_pattern = re.search(RegexConstants.EMAIL_PATTERN_REGEX, author_and_email, re.IGNORECASE)
                    full_email_pattern = re.search(RegexConstants.FULL_EMAIL_PATTERN_REGEX, author_and_email,
                                                   re.IGNORECASE)
                    if email_pattern:
                        email_found = email_pattern.group(0)
                        if email_found:
                            self.email = email_found.lower()
                    elif full_email_pattern:
                        # Full email
                        email_found = full_email_pattern.group(0)
                        if email_found:
                            self.email = CommitUtils.get_email(email_found)

        author_name = author_name.replace("\"", "")
        author_name = CommitUtils.strip_accents(author_name)
        author_name = author_name.strip()

        self.login = self.email.split("@")[0].lower()
        self.name = author_name.strip()

    def update_existing_developer(self, developer):
        if self.login == developer.login:  # Atualiza tudo menos o login
            self.email = developer.email
            self.name = developer.name
        else:
            self.email = developer.email  # Atualiza tudo menos o nome
            self.login = developer.login
        return self


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

    @property
    def minors(self):
        return [x.strip() for x in
                self.max_minor_version_description.split(',')] if self.max_minor_version_description != '' else []

    @staticmethod
    def line_major_versions(project_id):
        return Tag.objects.filter(major=True, project_id=project_id).values_list('id', flat=True)

    @property
    def main_directory_prefix(self):
        return self.main_directory + CommonsConstantsUtils.PATH_SEPARATOR

    def __str__(self):
        return f'{self.project.project_name}: {self.description}'

    @property
    def pre_build_commands(self):
        commands = self.prepare_build_command.split(',')
        return [c.strip() for c in commands]


class Directory(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='directories')
    visible = models.BooleanField(default=True)
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

    def clean_metrics(self):
        self.compilable = False
        self.mean_rmd_components = 0.0
        self.std_rmd_components = 0.0
        self.delta_rmd_components = 0.0
        self.normalized_delta = 0.0

    def set_compilable(self, status: bool):
        self.compilable = status

    def update_component_commits(self):
        for component in self.component_commits.all():
            component.calculate_author_experience_for_component()

    def __has_submitted_by_in_the_commit_msg__(self):
        m = re.search(RegexConstants.SUBMITTED_BY__PARTICLE_REGEX, self.msg, re.IGNORECASE)
        return (m and m.group(0)) is not None

    def save(self, *args, **kwargs):
        self.author.save()
        self.committer.save()

        self.get_parent_commit()

        if not self.pk:
            logger.info(f'Commit: {self}')

            self.has_submitted_by = self.__has_submitted_by_in_the_commit_msg__()

            self.refresh_measures_diff()

            self.author_experience = self.determine_author_experience()
            self.total_commits += 1

            logger.info("###")
            logger.info(f'Cadastrando commit: {self.hash}')
            logger.info(f'Versao: {self.tag.__str__()}')
            logger.info(f'Autor: {self.author.name}')

        super(Commit, self).save(*args, **kwargs)  # Call the "real" save() method.

    def get_parent_commit(self):
        for hash in self.parents:
            self.parent = Commit.objects.filter(hash=hash).first()
            break

    def refresh_measures_diff(self) -> None:
        authors_previous_commit = Commit.objects.filter(author=self.author, tag_id__lte=self.tag.id,
                                                        tag__project=self.tag.project).last()
        authors_first_commit = Commit.objects.filter(author=self.author, tag_id__lte=self.tag.id,
                                                     tag__project=self.tag.project).first()

        if authors_previous_commit:
            self.total_commits = authors_previous_commit.total_commits
            self.cloc_activity = authors_previous_commit.cloc_activity
            self.author_seniority = self.author_date - authors_first_commit.author_date
            self.author_seniority = abs(self.author_seniority.days)

    def determine_author_experience(self) -> float:

        # Formula weights for each measure
        c_weight = 0.2  # commits
        f_weight = 0.4  # files
        cloc_weight = 0.4  # lines of code

        files = 0
        authors_previous_commit = Commit.objects.filter(author=self.author, tag_id__lte=self.tag.id,
                                                        tag__project=self.tag.project).last()
        if authors_previous_commit:
            file_by_authors = Modification.objects.filter(commit__author=self.author,
                                                          commit__tag_id__lte=self.tag.id,
                                                          commit__tag__project=self.tag.project,
                                                          commit_id__lte=authors_previous_commit.id)

            files = file_by_authors.values("path").distinct().count()

        return c_weight * self.total_commits + f_weight * files + cloc_weight * self.cloc_activity

    #
    def prepare_build(self, validation_skip_error: bool = False) -> bool:
        JAVA_HOME = os.environ.get('JAVA_HOME')
        if not JAVA_HOME:
            raise RuntimeError(
                'There is no JAVA_HOME environment variable defined. Please install a valid version of JDK.')
        print(JAVA_HOME)

        ANT_HOME = os.environ.get('ANT_HOME')
        if not ANT_HOME:
            raise RuntimeError('There is no ANT_HOME environment variable defined. Please install ANT')
        print(ANT_HOME)

        M2_HOME = os.environ.get('M2_HOME')
        if not M2_HOME:
            raise RuntimeError('There is no M2_HOME environment variable defined. Please install Maven')
        print(M2_HOME)

        if self.tag.prepare_build_command:
            for command in self.tag.prepare_build_command:
                rc = os.system(command)
                if rc != 0:
                    self.logger.error('Error on compile')
                    if not validation_skip_error:
                        return False
        return True

    def build(self) -> bool:
        rc = os.system(self.tag.build_command)
        if rc != 0:
            logger.error('Error on compile')
            return False
        return True

    def compile(self, jar_name: str, build_path: str, repository: str) -> None:
        logger.info(f'comando: jar -cf {jar_name} {build_path}')
        process = subprocess.Popen(f'jar -cf {jar_name} {build_path}', cwd=repository,
                                   shell=False)
        process.wait()

    def h1_calculate_commit_degradation(self, commit_rmds):
        '''Invoked by __read_PM_file__'''
        if len(commit_rmds) > 0:
            self.mean_rmd_components = np.mean([c[0] for c in commit_rmds])
            self.std_rmd_components = np.std([c[0] for c in commit_rmds], ddof=1)
            self.delta_rmd_components = self.mean_rmd_components

        # Delta calculation
        self.previous_impactful_commit = self.__retrieve_previous_commit()

        if self.has_impact_loc and (
                self.previous_impactful_commit and self.previous_impactful_commit.compilable and self.previous_impactful_commit.tag == self.tag):
            self.delta_rmd_components -= self.previous_impactful_commit.mean_rmd_components
        # elif commit.previous_impactful_commit is not None and not commit.previous_impactful_commit.compilable:
        else:
            self.delta_rmd_components = 0.0

        # Delta normalization by LOC changed
        if self.u_cloc > 0:
            self.normalized_delta = self.delta_rmd_components / self.u_cloc
        else:
            self.normalized_delta = self.delta_rmd_components
            logger.error(
                "****** CASO ESPECIAL: commit sem linha de impacto (LOC=0) com delta diferentee de zero ******")

        self.compilable = True
        self.save()

    class Meta:
        ordering = ['tag_id', 'id']

    def __retrieve_previous_commit(self):
        if len(self.parents) > 0:
            return self.parents[0]
        return Commit.objects.filter(tag=self.tag, id__lt=self.id,
                                     tag__real_tag_description__iexact=self.tag.real_tag_description).last()

    def __retrieve_previous_component_commit(self, directory):
        component = ComponentCommit.objects.filter(component=directory, commit_id__lt=self.id,
                                                   commit__author=self.author, commit__tag=self.tag,
                                                   commit__tag__real_tag_description__iexact=self.tag.real_tag_description)
        if component.exists():
            return component.last()
        return None


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
        return self.component.name

    def calculate_author_experience_for_component(self):
        previous_component_commit = ComponentCommit.objects.filter(commit__author=self.commit.author,
                                                                   component=self.component,
                                                                   commit__id__lt=self.commit.id,
                                                                   commit__tag__project=self.commit.tag.project).last()
        file_by_authors = Modification.objects.none()

        # because components are saved directly
        if previous_component_commit:
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
    ADDED_ = 'ADD'
    DELETED = 'DEL'
    MODIFIED = 'MOD'
    RENAMED = 'REN'
    CHANGE_TYPES_CHOICES = [
        (ADDED_, 'Added'),
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
    added = models.IntegerField(default=0)
    removed = models.IntegerField(default=0)
    cloc = models.IntegerField(default=0)
    u_cloc = models.IntegerField(default=0)
    has_impact_loc = models.BooleanField(default=False)

    def __str__(self):
        return f"Commit: {self.commit.hash}, Path: {self.path}"

    def __diff_text(self):
        GR = GitRepository(self.commit.tag.project.project_path)

        parsed_lines = GR.parse_diff(self.diff)

        return parsed_lines

    def __print_text_in_lines(self, text, result, type_symbol):
        for line in text:
            result = result + CommonsConstantsUtils.END_STR + str(line[0]) + ' ' + type_symbol + ' ' + line[1]
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

        diff_text = f'\n{str(self.added)} lines added: \n'  # result: Added: [(4, 'log.debug("b")')]
        diff_text = self.__print_text_in_lines(added_text, diff_text, '+')

        return diff_text

    @property
    def diff_removed(self):
        deleted_text = self.__diff_text()['deleted']
        diff_text = f'\n{str(self.removed)} lines removed:  \n'
        diff_text = self.__print_text_in_lines(deleted_text, diff_text, '-')

        return diff_text

    @property
    def file(self):
        index = self.path.rfind(CommonsConstantsUtils.PATH_SEPARATOR)
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

            if not self.commit.pk:
                self.commit.save()

            self.directory = self.__prepare_directory()
            self.component_commit = self.__prepare_component_commit()

            self.cloc = self.added + self.removed
            self.__update_commit_cloc_activity()

            super(Modification, self).save(*args, **kwargs)  # Call the "real" save() method.

    def __prepare_directory(self) -> Directory:
        index = self.path.rfind(CommonsConstantsUtils.PATH_SEPARATOR)
        if index > -1:
            directory_str = self.path[:index]
        else:
            directory_str = CommonsConstantsUtils.PATH_SEPARATOR
        directory = Directory.objects.filter(name__iexact=directory_str)
        if directory.exists():
            return directory[0]

        return Directory.objects.create(name=directory_str, project=self.commit.tag.project,
                                        initial_commit=self.commit)

    def __prepare_component_commit(self) -> ComponentCommit:
        component_commit_repo = ComponentCommit.objects.filter(component=self.directory, commit=self.commit)
        if component_commit_repo.exists():
            return component_commit_repo[0]

        return ComponentCommit.objects.create(component=self.directory, commit=self.commit)

    def __update_commit_cloc_activity(self) -> None:
        self.commit.cloc_activity += self.u_cloc
        self.commit.save()


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
