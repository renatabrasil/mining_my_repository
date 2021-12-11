import logging

from django.core.paginator import Paginator
from injector import inject
from pydriller import RepositoryMining

from common.utils import ViewUtils, CommitUtils
from contributions.constants import ProjectsConstants, ConstantsUtils
from contributions.models import Tag, Modification, Commit, Developer
from contributions.repositories.commit_repository import CommitRepository
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.project_repository import ProjectRepository
from contributions.repositories.tag_repository import TagRepository


class ContributionsService:
    @inject
    def __init__(self, tag_repository: TagRepository, commit_repository: CommitRepository,
                 developer_repository: DeveloperRepository, project_repository: ProjectRepository):
        self.tag_repository = tag_repository
        self.commit_repository = commit_repository
        self.developer_repository = developer_repository
        self.project_repository = project_repository
        self.logger = logging.getLogger(__name__)

    def process(self, request):
        tag = ViewUtils.load_tag(request)

        if request.POST.get('load_commits'):
            filter_ = {}
            project = self.project_repository.find_by_primary_key(pk=request.session['project'])

            if tag.previous_tag:
                last_commit_saved = self.commit_repository.find_all_commit_from_all_previous_tag(tag_id=tag.id,
                                                                                                 project_id=
                                                                                                 request.session[
                                                                                                     'project']).last()
                filter_['from_tag'] = tag.previous_tag.description
                if last_commit_saved:
                    filter_['from_commit'] = last_commit_saved.hash
                    filter_.pop('from_tag', None)

            filter_['only_in_branch'] = project.main_branch
            self.__set_filter_parameters(filter_)

            self.__load_commits_from_repo_by_tag(tag, filter_)

        return request

    def index(self, request) -> dict:
        
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

        return context

    def __set_filter_parameters(self, filter_: dict):
        filter_.pop('from_commit', None)
        filter_.pop('from_tag', None)
        filter_.pop('to_tag', None)
        filter_['only_modifications_with_file_types'] = ['.java']
        filter_['only_no_merge'] = True

    def __load_commits_from_repo_by_tag(self, tag: Tag, filter_: dict) -> None:
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
                    if minor.find(ConstantsUtils.TAG_DELIMITER) == 0 and 'from_commit' not in filter_.keys():
                        filter_['from_tag'] = minor.replace(ConstantsUtils.TAG_DELIMITER, '')
                        continue
                    filter_['to_tag'] = minor

                    self.logger.info(" \n************ VERSAO: " + filter_['to_tag'] + ' ***************\n\n')

                    self.__load_commits_from_repo_and_save_in_db(current_tag, filter_)

                    filter_['from_tag'] = minor
                    filter_.pop('from_commit', None)

            elif current_tag.previous_tag and 'from_tag' in filter_:
                filter_['from_tag'] = current_tag.previous_tag.description

    def __load_commits_from_repo_and_save_in_db(self, current_tag: Tag, filter_: dict) -> Commit:
        try:
            commits = []
            for commit_from_repository in RepositoryMining(current_tag.project.project_path,
                                                           **filter_).traverse_commits():
                commit = self.commit_repository.find_all_commits_by_hash(hash=commit_from_repository.hash)
                if not commit.exists():
                    author, committer = self.__configure_author_and_committer(commit_from_repository)

                    commit = Commit.objects.create(hash=commit_from_repository.hash, tag=current_tag,
                                                   parents_str=str(commit_from_repository.parents)[1:-1].replace(" ",
                                                                                                                 "").replace(
                                                       "'", ""),
                                                   msg=commit_from_repository.msg,
                                                   author=author,
                                                   author_date=commit_from_repository.author_date,
                                                   committer=committer,
                                                   committer_date=commit_from_repository.committer_date,
                                                   real_tag_description=filter_['to_tag'])

                    for modification_repo in commit_from_repository.modifications:
                        # Save only commits with java file and not in test directory
                        if self.__has_no_constraints(modification_repo, current_tag):
                            modification = Modification.objects.create(commit=commit,
                                                                       old_path=modification_repo.old_path,
                                                                       new_path=modification_repo.new_path,
                                                                       change_type=modification_repo.change_type,
                                                                       diff=modification_repo.diff,
                                                                       added=modification_repo.added,
                                                                       removed=modification_repo.removed)

                            self.logger.info(modification.__str__())
                    if commit.pk:
                        commit.update_component_commits()

                    commits.append(commit)
            return commits
        except Exception as err:
            self.logger.exception(f'Erro ao salvar arquivo.')
            self.logger.exception(err)
            raise

    def __configure_author_and_committer(self, commit_from_repo):
        author = Developer.create(name=commit_from_repo.author.name, email=commit_from_repo.author.email,
                                  login=commit_from_repo.author.email.split("@")[0])
        author.format_data(commit_from_repo.msg)

        author_db = self.developer_repository.find_all_developer_by_iexact_name(name=author.name).first()
        if author_db:
            author.update_existing_developer(author_db)
        else:
            author_db = self.developer_repository.find_all_developer_by_login(login=author.login).first()
            if author_db:
                author.update_existing_developer(author_db)

        committer = Developer.create(name=commit_from_repo.committer.name,
                                     email=commit_from_repo.committer.email,
                                     login=commit_from_repo.committer.email.split("@")[0])
        committer.format_data(commit_from_repo.msg)

        committer_db = self.developer_repository.find_all_developer_by_iexact_name(name=committer.name).first()
        if committer_db:
            committer.update_existing_developer(committer_db)
        else:
            committer_db = self.developer_repository.find_all_developer_by_login(login=committer.login).first()
            if committer_db:
                committer.update_existing_developer(committer_db)

        return author, committer

    def __has_no_constraints(self, modification, tag):
        path = CommitUtils.true_path(modification)
        directory_str = CommitUtils.extract_directory_name_from_full_file_name(path)

        ant_conditions = True
        lucene_conditions = True
        maven_conditions = True
        openjpa_conditions = True
        hadoop_conditions = True
        cassandra_conditions = True
        shiro_conditions = True

        if tag.project.id == ProjectsConstants.ANT:
            ant_conditions = str.lower(directory_str).find('proposal') == -1
        if tag.project.id == ProjectsConstants.LUCENE:
            lucene_conditions = str.lower(directory_str).find('/demo/') == -1
            lucene_conditions = lucene_conditions and (str.lower(directory_str).startswith('src/java') or (
                    str.lower(directory_str).startswith('lucene') and str.lower(directory_str).find(
                'src/java') > -1)) and str.lower(directory_str).find('solr') == -1
            # or str.lower(directory_str).startswith('lucene/core')) and str.lower(directory_str).find('solr') == -1
        if tag.project.id == ProjectsConstants.MAVEN:
            maven_conditions = str.lower(directory_str).startswith('maven-core') and str.lower(directory_str).find(
                'maven-core-') == -1
        if tag.project.id == ProjectsConstants.OPENJPA:
            openjpa_conditions = str.lower(directory_str).startswith('openjpa-kernel/')

        if tag.project.id == ProjectsConstants.CASSANDRA:
            cassandra_conditions = str.lower(directory_str).startswith(tag.main_directory)
        if tag.project.id == ProjectsConstants.HADOOP:
            dirs = [x.strip() for x in tag.core_component.split(',')]
            hadoop_conditions = False
            for dir in dirs:
                hadoop_conditions = hadoop_conditions or str.lower(directory_str).find(dir) > -1

        return CommitUtils.is_java_file(path) and str.lower(directory_str).find('test') == -1 and \
               ant_conditions and lucene_conditions and maven_conditions and openjpa_conditions and cassandra_conditions and \
               hadoop_conditions and shiro_conditions

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
