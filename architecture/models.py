# Django
import logging

from django.core.files import File
from django.db import models

# local Django
from common.constants import CommonsConstantsUtils, ExtensionsFile
from contributions.models import Tag, AUTHOR_FILTER, Developer, Commit

logger = logging.getLogger(__name__)


class FileCommits(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='files')
    metrics_calculated_at = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=200)
    directory = models.CharField(max_length=100)
    has_compileds = models.BooleanField(default=False)
    build_path = models.CharField(max_length=200)
    local_repository = models.CharField(max_length=200, default="G:/My Drive/MestradoUSP/programacao/projetos/git/ant")
    __file_sys__ = None

    @classmethod
    def create(cls, filename="", git_local_repository="", build_path="", directory="", tag=None):
        file = cls(name=filename, local_repository=git_local_repository, build_path=build_path, directory=directory,
                   tag=tag)
        return file

    def add_file_system(self, file):
        self.__file_sys__ = file

    @property
    def file_sys(self):
        return self.__file_sys__

    def __str__(self):
        return self.directory + CommonsConstantsUtils.PATH_SEPARATOR + self.name

    def create_file_with_commits(self, commits: list[Commit]) -> list:

        try:
            logger.info(f'[{__name__}] Starting to create files with commits []')

            files = []

            my_file = File(open(self.__str__(), 'w'))
            my_file.write(self.local_repository + CommonsConstantsUtils.END_STR)
            my_file.write(self.build_path + CommonsConstantsUtils.END_STR)

            tag_description = commits[0].tag.description

            i = 1
            for commit in commits:

                commit_tag = commit.tag.description.replace(CommonsConstantsUtils.PATH_SEPARATOR,
                                                            CommonsConstantsUtils.HYPHEN_SEPARATOR)

                if tag_description != commit_tag:
                    my_file.closed
                    self.save()

                    i = 1
                    tag_description = commit_tag
                    filename = 'commits-' + tag_description + ExtensionsFile.TXT

                    file = self.update_current_file(filename)
                    file.tag = commit.tag

                    my_file = File(open(file.__str__(), 'w'))

                    files.append(file)

                    my_file.write(self.local_repository + CommonsConstantsUtils.END_STR)
                    my_file.write(self.build_path + CommonsConstantsUtils.END_STR)

                if not commit.has_impact_loc and not commit.children_commit:
                    continue

                my_file.write(
                    str(i) + CommonsConstantsUtils.HYPHEN_SEPARATOR + commit.hash + CommonsConstantsUtils.END_STR)
                self.logger.info(f'{str(i) + CommonsConstantsUtils.HYPHEN_SEPARATOR + commit.hash} saved')
                i += 1

            my_file.closed
            file.save()

            logger.info(f'[{FileCommits.__name__}] - Done generating files of commits ...')

            return files
        except Exception as e:
            logger.exception(e.args[0])
            raise


class NoOutlierMetricManager(models.Manager):
    def get_queryset(self):
        ids = []
        for author in AUTHOR_FILTER:
            author_db = Developer.objects.get(name=author)
            if author_db:
                ids.append(author_db.id)
        return super().get_queryset().exclude(commit__author_id__in=ids)
