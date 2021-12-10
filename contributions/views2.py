# standard library
import json
import logging
import re
import time

# third-party
# Django
from django.core.paginator import Paginator
from django.http import (Http404, HttpResponse)
from django.shortcuts import render
from django.template import loader
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_http_methods
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

# local Django
from common.utils import CommitUtils, ViewUtils
from contributions.constants import ProjectsConstants
from contributions.models import (
    Commit, Developer, Modification, __has_impact_loc_calculation_static_method)
from contributions.repositories.commit_repository import CommitRepository
from contributions.repositories.developer_repository import DeveloperRepository
from contributions.repositories.directory_repository import DirectoryRepository
from contributions.repositories.modification_repository import ModificationRepository
from contributions.repositories.project_repository import ProjectRepository
from contributions.repositories.tag_repository import TagRepository

FULL_EMAIL_PATTERN_REGEX = r'[\sa-zA-Z0-9_.+-]+(\s*(a|A)(t|T)\s*)[a-zA-Z0-9-]+((\s*(d|D)(O|o)(t|T)\s*)[a-zA-Z0-9-. ]+)+'

EMAIL_PATTERN_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

SUBMITTED_BY_PARTICLE_REGEX = r'\Submitted\s*([bB][yY])[:]*\s*[\s\S][^\r\n]*[a-zA-Z0-9_.+-]+((\[|\(|\<)|(\s*(a|A)(t|T)\s*|@)[a-zA-Z0-9-]+(\s*(d|D)(O|o)(t|T)\s*|\.)[a-zA-Z0-9-.]+|(\)|\>|\]))'

GR = GitRepository('https://github.com/apache/ant.git')
report_directories = None

logger = logging.getLogger(__name__)

commit_repository = CommitRepository()
directory_repository = DirectoryRepository()
developer_repository = DeveloperRepository()
project_repository = ProjectRepository()
tag_repository = TagRepository()
modification_repository = ModificationRepository()


@require_http_methods(["GET", "POST"])
def index(request):
    try:
        start = time.time()

        title_description = 'Contribuições - Commits'

        tag = ViewUtils.load_tag(request)

        __load_commits_by_request_and_tag(request, tag)

        url_path = 'contributions/index.html'
        current_developer = None
        current_tag_filter = None
        developer_id = request.POST.get("developer_filter_id")
        tag_id = request.POST.get("tag_filter_id")
        if request.GET.get('commits'):
            title_description = 'Contributions - Detalhes do commit'
            url_path = 'developers/detail.html'
        else:
            if developer_id or tag_id:
                latest_commit_list = Commit.objects.none()
                if developer_id:
                    current_developer = developer_repository.find_by_primary_key(pk=int(developer_id))
                    latest_commit_list = latest_commit_list | commit_repository.find_all_commits_by_author_id(
                        author_id=current_developer.id)
                if tag_id:
                    current_tag_filter = tag_repository.find_by_primary_key(pk=int(tag_id))
                    if latest_commit_list:
                        latest_commit_list = latest_commit_list & commit_repository.find_all_commits_by_tag(
                            tag_id=current_tag_filter.id)
                    else:
                        latest_commit_list = commit_repository.find_all_commits_by_tag(tag_id=current_tag_filter.id)
                latest_commit_list = latest_commit_list.order_by("tag_id", "author__name")
            elif tag:
                latest_commit_list = load_commits_from_tags(tag)
            else:
                latest_commit_list = commit_repository.find_all().order_by("tag_id", "author__name", "committer_date")
            paginator = Paginator(latest_commit_list, 100)

            page = request.GET.get('page')
            latest_commit_list = paginator.get_page(page)

        template = loader.get_template(url_path)
        context = {
            'title': title_description,
            'latest_commit_list': latest_commit_list,
            'tag': tag.description,
            'current_developer': current_developer,
            'current_tag_filter': current_tag_filter,
        }
        if request.is_ajax():
            result = {'html': render_to_string(url_path, {'latest_commit_list': latest_commit_list})}
            return HttpResponse(json.dumps(result, ensure_ascii=False),
                                content_type='application/json')
        end = time.time()

        logger.info("Tempo total: " + str(end - start))

        return HttpResponse(template.render(context, request))
    except Exception as err:
        logger.exception(err.args[0])
        raise


def __load_commits_by_request_and_tag(request, tag):
    load_commits = request.POST.get('load_commits')
    if not load_commits and (request.GET.get('load') and request.GET.get('load') == 'true'):
        load_commits = True

    if load_commits:
        filter_ = {}
        project = __get_project_by_request(request)

        if tag.previous_tag is not None:
            commit = commit_repository.find_all_commit_from_all_previous_tag(tag_id=tag.id, project_id=request.session[
                'project']).last()
            filter_.setdefault('from_tag', tag.previous_tag.description)
            if commit is not None:
                hash_commit = commit.hash
                filter_.setdefault('from_commit', hash_commit)
                filter_.pop('from_tag', None)
        filter_.setdefault('only_in_branch', project.main_branch)
        filter_.setdefault('only_modifications_with_file_types', ['.java'])
        filter_.setdefault('only_no_merge', True)
        filter_.setdefault('to_tag', tag.real_tag_description)
        filter_.pop('from_commit', None)
        filter_.pop('from_tag', None)
        filter_.pop('to_tag', None)
        tags = [x for x in list(tag_repository.find_all_major_tags_by_project(project_id=project.id, tag_id=tag.id)) if
                x.id != 16]
        for current_tag in tags:
            if current_tag.minors:
                if current_tag.previous_tag is not None and 'from_commit' not in filter_:
                    if 'from_tag' in filter_:
                        filter_['from_tag'] = current_tag.previous_tag.description
                    else:
                        filter_.setdefault('from_tag', current_tag.previous_tag.description)
                for minor in list([current_tag.real_tag_description] + current_tag.minors):
                    if minor.find('*') == 0 and 'from_commit' not in filter_.keys():
                        filter_['from_tag'] = minor.replace('*', '')
                        continue
                    filter_['to_tag'] = minor
                    print(" \n************ VERSAO: " + filter_['to_tag'] + ' ***************\n\n')
                    for commit_from_repository in RepositoryMining(project.project_path, **filter_).traverse_commits():
                        __build_and_save_commit(commit_from_repository, current_tag, filter_['to_tag'])

                    filter_['from_tag'] = minor
                    filter_.pop('from_commit', None)

            else:
                if current_tag.previous_tag is not None:
                    if 'from_tag' in filter_:
                        filter_['from_tag'] = current_tag.previous_tag.description
                    else:
                        filter_.setdefault('from_tag', current_tag.previous_tag.description)
                if 'to_tag' in filter_:
                    filter_['to_tag'] = current_tag.real_tag_description
                else:
                    filter_.setdefault('to_tag', current_tag.real_tag_description)
                for commit_from_repository in RepositoryMining(project.project_path, **filter_).traverse_commits():
                    __build_and_save_commit(commit_from_repository, current_tag, filter_['to_tag'])
            __update_commit(commit_repository.find_all_commits_by_tag(tag_id=current_tag))


def __get_project_by_request(request):
    logger.info(f'project_id: {request.session["project"]}')
    return project_repository.find_by_primary_key(pk=request.session['project'])


def __build_and_save_commit(commit_from_repository, tag, real_tag):
    commit = commit_repository.find_all_commits_by_hash(hash=commit_from_repository.hash)
    if not commit.exists():
        author_name = CommitUtils.strip_accents(commit_from_repository.author.name)
        committer_name = CommitUtils.strip_accents(commit_from_repository.committer.name)
        email = commit_from_repository.author.email.lower()
        login = commit_from_repository.author.email.split("@")[0].lower()
        m = re.search(SUBMITTED_BY_PARTICLE_REGEX, commit_from_repository.msg, re.IGNORECASE)
        found = ''
        if m:
            found = m.group(0)
            if found:
                author_and_email = re.sub(r'\Submitted\s*([bB][yY])[:]*\s*', '', found)
                author_name = re.sub(
                    r'\s*(\[|\(|\<)|[\sa-zA-Z0-9_.+-]+(\s*(a|A)(t|T)\s*|@)[a-zA-Z0-9-]+((\s*(d|D)(O|o)(t|T)\s*|\.)[a-zA-Z0-9-. ]+)+|(\)|\>|\])',
                    '',
                    author_and_email)
                author_name = author_name.replace("\"", "")
                author_name = CommitUtils.strip_accents(author_name)
                author_name = author_name.strip()
                email_pattern = re.search(EMAIL_PATTERN_REGEX, author_and_email, re.IGNORECASE)
                full_email_pattern = re.search(FULL_EMAIL_PATTERN_REGEX, author_and_email, re.IGNORECASE)
                if email_pattern:
                    email_found = email_pattern.group(0)
                    if email_found:
                        email = email_found.lower()
                        commit.hasSubmittedBy = True
                elif full_email_pattern:
                    # Full email
                    email_found = full_email_pattern.group(0)
                    if email_found:
                        email = CommitUtils.get_email(email_found)
                        commit.hasSubmittedBy = True
                login = email.split("@")[0].lower()

        author_name = author_name.strip()

        author = developer_repository.find_all_developer_by_iexact_name(name=author_name)
        if author.count() == 0:
            if login != 'dev-null' and login != 'ant-dev':
                author = developer_repository.find_all_developer_by_login(login=login)
            # If it is find by login, update fields
            if author.count() > 0:
                author = author[0]
                author.email = email
                if author_name:
                    author.name = author_name
            else:
                if not author_name:
                    author = Developer(name=login, email=email, login=login)
                else:
                    author = Developer(name=author_name, email=email, login=login)
        else:
            # If it is find by name, update fields
            author = author[0]
            author.email = email
            author.login = login

        if author.name == commit_from_repository.committer.name:
            committer = author
        else:
            committer = developer_repository.find_all_developer_by_iexact_name(name=committer_name)
            if committer.count() == 0:
                email = commit_from_repository.committer.email.lower()
                login = email.split("@")[0].lower()
                committer = developer_repository.find_all_developer_by_login(login=login)
                if committer.count() > 0:
                    committer = committer[0]
                else:
                    committer = Developer(name=CommitUtils.strip_accents(commit_from_repository.committer.name),
                                          email=email, login=login)
            else:
                committer = committer[0]

        commit = Commit(hash=commit_from_repository.hash, tag=tag,
                        parents_str=str(commit_from_repository.parents)[1:-1].replace(" ", "").replace("'", ""),
                        msg=commit_from_repository.msg,
                        author=author, author_date=commit_from_repository.author_date,
                        committer=committer,
                        committer_date=commit_from_repository.committer_date, real_tag_description=real_tag)
        total_modification = 0
        for modification_repo in commit_from_repository.modifications:
            # Save only commits with java file and not in test directory
            if __no_commits_constraints(modification_repo, tag):
                total_modification = total_modification + 1
                if hasattr(modification_repo, 'nloc'):
                    nloc = modification_repo.nloc
                else:
                    nloc = None
                try:
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
                except Exception:
                    logger.exception(f'Erro ao salvar arquivo {modification.path}')
        if commit.pk is not None:
            commit.update_component_commits()
        logger.info(commit)
    return commit


@require_http_methods(["GET", "POST"])
def detail_by_hash(request):
    hash_commit = request.POST.get('hash')
    if hash_commit:
        request.session['hash'] = hash_commit
    else:
        if 'hash' in request.session:
            hash_commit = request.session['hash']
        else:
            hash_commit = None

    commit = commit_repository.find_all_commits_by_hash(hash=hash_commit)
    if commit.count() > 0:
        commit = commit[0]
    else:
        commit = None
    return render(request, 'contributions/detail.html',
                  {'commit': commit, 'current_commit_hash': hash_commit, 'title': 'Detalhes do commit'})


@require_GET
def detail(request, commit_id):
    try:
        commit = commit_repository.find_by_primary_key(pk=commit_id)
        commit.u_cloc
        print(commit.u_cloc)
        print(commit.committer_date)
        for mod in commit.modifications.all():
            GR = GitRepository(commit.tag.project.project_path)

            parsed_lines = GR.parse_diff(mod.diff)
            __has_impact_loc_calculation_static_method(parsed_lines)

    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/detail.html', {'commit': commit})


@require_GET
def detail_in_committer(request, committer_id):
    try:
        project = project_repository.find_project_by_name(name="Apache Ant")
        path = ""
        if request.GET.get('path'):
            path = request.GET.get('path')

        tag = ViewUtils.load_tag(request)

        latest_commit_list = list(
            commit_repository.find_all_distinct_commits_by_committer_and_modifications_for_specific_directory(
                committer_id=committer_id, tag_id=tag.id,
                modifications=modification_repository.find_all_modifications_by_path(
                    directory_id=int(path))))
        context = {
            'latest_commit_list': latest_commit_list,
            'project': project,
        }
    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/index.html', context)


''' Load all commits including all previous tag of current tag
param: current tag
return all commits up to current tag '''


def load_commits_from_tags(tag):
    commits = commit_repository.find_all_distinct_commits_by_tag_description(description=tag.description)
    if len(commits) == 0:
        return commits
    tag = tag.previous_tag
    while tag:
        commits = commits | (
            commit_repository.find_all_distinct_commits_by_tag_description(description=tag.description))
        tag = tag.previous_tag
    return commits


def __update_commit(commits):
    for commit in commits:
        lista = commit.parents_str.split(",")
        for parent_hash in lista:
            parent = commit_repository.find_all_commits_by_hash(hash=parent_hash)
            if parent.count() > 0:
                parent = parent[0]
                parent.children_commit = commit
                commit.parent = parent
                parent.save(update_fields=['children_commit'])


def __no_commits_constraints(modification, tag):
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
