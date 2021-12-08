import logging
import time

from django.core.paginator import Paginator
from django.shortcuts import render
from django.views import View
from pydriller import RepositoryMining

from common.utils import ViewUtils, CommitUtils
from contributions.models import Commit, Tag, Developer, Modification, ANT, LUCENE, MAVEN, OPENJPA, CASSANDRA, HADOOP
from contributions.repositories.commit_repository import CommitRepository
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.project_repository import ProjectRepository
from contributions.repositories.tag_repository import TagRepository

logger = logging.getLogger(__name__)

TAG_DELIMITER = '*'


def set_default_filter_parameters(filter_: dict):
    filter_.pop('from_commit', None)
    filter_.pop('from_tag', None)
    filter_.pop('to_tag', None)
    filter_['only_modifications_with_file_types'] = ['.java']
    filter_['only_no_merge'] = True


class ContributionsView(View):
    model = Commit
    template_name = 'contributions/index.html'
    context_object_name = 'commit'

    tag_repository = TagRepository()
    commit_repository = CommitRepository()
    project_repository = ProjectRepository()
    developer_repository = DeveloperRepository()

    def get(self, request):
        start = time.time()

        tag = ViewUtils.load_tag(request)

        context = {
            'tag': tag.description
        }

        return render(request, self.template_name, context)

    def post(self, request):
        start = time.time()
        tag = ViewUtils.load_tag(request)

        # LOAD FROM PYDRILLER
        if request.POST.get('load_commits'):
            filter_ = {}
            project = self.project_repository.find_by_primary_key(pk=request.session['project'])

        if tag.previous_tag:
            last_commit_saved = self.commit_repository.find_all_commit_from_all_previous_tag(tag_id=tag.id,
                                                                                             project_id=request.session[
                                                                                                 'project']).last()
            filter_['from_tag'] = tag.previous_tag.description
            if last_commit_saved:
                filter_['from_commit'] = last_commit_saved.hash
                filter_.pop('from_tag', None)

        filter_['only_in_branch'] = project.main_branch
        set_default_filter_parameters(filter_)

        self.__load_commits_by_tag(tag, filter_)

        # LOAD

        tag = ViewUtils.load_tag(request)
        tag_id = request.POST.get('tag_filter_id')

        current_tag_filter = self.tag_repository.find_by_primary_key(pk=tag_id) if tag_id else None
        if not tag_id:
            latest_commit_list = self.commit_repository.find_all().order_by("tag_id", "author__name", "committer_date")

        paginator = Paginator(latest_commit_list, 100)

        page = request.GET.get('page')
        latest_commit_list = paginator.get_page(page)

        context = {
            'tag': tag.description,
            'current_tag_filter': current_tag_filter,
            'latest_commit_list': latest_commit_list,
        }

        end = time.time()
        self.logger.info("Tempo total: " + str(end - start))

        return render(request, self.template_name, context)

    def __load_commits_by_tag(self, tag: Tag, filter_: dict) -> None:
        tags = [x for x in
                list(self.tag_repository.find_all_major_tags_by_project(project_id=tag.project.id, tag_id=tag.id))
                if
                x.id != 16]
        for current_tag in tags:
            if current_tag.minors:
                if current_tag.previous_tag and 'from_commit' not in filter_ and 'from_tag' in filter_:
                    filter_['from_tag'] = current_tag.previous_tag.description

                current_tag_and_its_minor_tags = list([current_tag.real_tag_description] + current_tag.minors)
                for minor in current_tag_and_its_minor_tags:
                    if minor.find(TAG_DELIMITER) == 0 and 'from_commit' not in filter_.keys():
                        filter_['from_tag'] = minor.replace(TAG_DELIMITER, '')
                        continue
                    filter_['to_tag'] = minor

                    logger.info(" \n************ VERSAO: " + filter_['to_tag'] + ' ***************\n\n')

                    self.__load_commits_from_repository_and_save_in_db(current_tag, filter_)

                    filter_['from_tag'] = minor
                    filter_.pop('from_commit', None)

            elif current_tag.previous_tag and 'from_tag' in filter_:
                filter_['from_tag'] = current_tag.previous_tag.description

    def __load_commits_from_repository_and_save_in_db(self, current_tag: Tag, filter_: dict) -> Commit:
        for commit_from_repository in RepositoryMining(current_tag.project.project_path, **filter_).traverse_commits():
            commit = self.commit_repository.find_all_commits_by_hash(hash=commit_from_repository.hash)
            if not commit.exists():
                commit = self.__save_commit(commit_from_repository, current_tag, filter_['to_tag'])
        return commit

    def __save_commit(self, commit_from_repository, tag: Tag, real_tag: str):

        author, committer = self.__save_author_and_committer(commit_from_repository, tag)

        commit = Commit(hash=commit_from_repository.hash, tag=tag,
                        parents_str=str(commit_from_repository.parents)[1:-1].replace(" ", "").replace("'", ""),
                        msg=commit_from_repository.msg,
                        author=author, author_date=commit_from_repository.author_date,
                        committer=committer,
                        committer_date=commit_from_repository.committer_date, real_tag_description=real_tag)

        total_modification = len(self.__save_all_modifications_from_commit(commit_from_repository, commit))
        if commit.pk:
            commit.update_component_commits()

    def __save_author_and_committer(self, commit_from_repository, tag: Tag):

        author_name_from_repo = CommitUtils.strip_accents(commit_from_repository.author.name)
        committer_name = CommitUtils.strip_accents(commit_from_repository.committer.name)
        email = commit_from_repository.author.email.lower()
        login = commit_from_repository.author.email.split("@")[0].lower()

        author_name_from_repo = author_name_from_repo.strip()

        author = self.developer_repository.find_all_developer_by_iexact_name(name=author_name_from_repo)
        if author.count() == 0:
            author = self.__adjust_and_save_author(author_name_from_repo, login, email)

        if author.name == commit_from_repository.committer.name:
            committer = author
        else:
            committer = self.__adjust_and_save_committer(commit_from_repository.committer, committer_name)

        return author, committer

    def __adjust_and_save_author(self, author_name_from_repo, login: str, email: str):
        if login != 'dev-null' and login != 'ant-dev':
            author = self.developer_repository.find_all_developer_by_login(login=login)
        # If it is find by login, update fields
        if author.count() > 0:
            author = author[0]
            author.email = email
            if author_name_from_repo:
                author.name = author_name_from_repo
        elif not author_name_from_repo:
            author = Developer(name=login, email=email, login=login)
        else:
            author = Developer(name=author_name_from_repo, email=email, login=login)

        # If it is find by name, update fields
        author = author[0]
        author.email = email
        author.login = login

        return author

    def __adjust_and_save_committer(self, committer_from_repo, committer_name):
        committer = self.developer_repository.find_all_developer_by_iexact_name(name=committer_name)
        if committer.count() == 0:
            email = committer_from_repo.email.lower()
            login = email.split("@")[0].lower()
            committer = self.developer_repository.find_all_developer_by_login(login=login)
            if committer.count() > 0:
                committer = committer[0]
            else:
                committer = Developer(name=CommitUtils.strip_accents(committer_from_repo.name),
                                      email=email, login=login)
        else:
            committer = committer[0]
        return committer

    def __save_all_modifications_from_commit(self, commit_from_repo, commit: Commit):
        modifications = []
        for modification_repo in commit_from_repo.modifications:
            # Save only commits with java file and not in test directory
            if self.__no_commits_constraints(modification_repo, commit.tag):
                total_modification = total_modification + 1
                if hasattr(modification_repo, 'nloc'):
                    nloc = modification_repo.nloc
                else:
                    nloc = None
                modification = Modification(commit=commit, old_path=modification_repo.old_path,
                                            new_path=modification_repo.new_path,
                                            change_type=modification_repo.change_type,
                                            diff=modification_repo.diff,
                                            source_code=modification_repo.source_code,
                                            source_code_before=modification_repo.source_code_before,
                                            added=modification_repo.added,
                                            removed=modification_repo.removed,
                                            nloc=nloc,
                                            complexity=modification_repo.complexity)
                logger.info(modification.__str__())
                modification.save()
                modifications.append(modification)
        return modifications

    def __update_commit(self, commits):
        for commit in commits:
            lista = commit.parents_str.split(",")
            for parent_hash in lista:
                parent = self.commit_repository.find_all_commits_by_hash(hash=parent_hash)
                if parent.count() > 0:
                    parent = parent[0]
                    parent.children_commit = commit
                    commit.parent = parent
                    parent.save(update_fields=['children_commit'])

    def __no_commits_constraints(self, modification, tag):
        path = CommitUtils.true_path(modification)
        directory_str = CommitUtils.extract_directory_name_from_full_file_name(path)

        ant_conditions = True
        lucene_conditions = True
        maven_conditions = True
        openjpa_conditions = True
        hadoop_conditions = True
        cassandra_conditions = True
        shiro_conditions = True

        if tag.project.id == ANT:
            ant_conditions = str.lower(directory_str).find('proposal') == -1
        if tag.project.id == LUCENE:
            lucene_conditions = str.lower(directory_str).find('/demo/') == -1
            lucene_conditions = lucene_conditions and (str.lower(directory_str).startswith('src/java') or (
                    str.lower(directory_str).startswith('lucene') and str.lower(directory_str).find(
                'src/java') > -1)) and str.lower(directory_str).find('solr') == -1
            # or str.lower(directory_str).startswith('lucene/core')) and str.lower(directory_str).find('solr') == -1
        if tag.project.id == MAVEN:
            maven_conditions = str.lower(directory_str).startswith('maven-core') and str.lower(directory_str).find(
                'maven-core-') == -1
        if tag.project.id == OPENJPA:
            openjpa_conditions = str.lower(directory_str).startswith('openjpa-kernel/')

        if tag.project.id == CASSANDRA:
            cassandra_conditions = str.lower(directory_str).startswith(tag.main_directory)
        if tag.project.id == HADOOP:
            dirs = [x.strip() for x in tag.core_component.split(',')]
            hadoop_conditions = False
            for dir in dirs:
                hadoop_conditions = hadoop_conditions or str.lower(directory_str).find(dir) > -1

        return CommitUtils.is_java_file(path) and str.lower(directory_str).find('test') == -1 and \
               ant_conditions and lucene_conditions and maven_conditions and openjpa_conditions and cassandra_conditions and \
               hadoop_conditions and shiro_conditions
