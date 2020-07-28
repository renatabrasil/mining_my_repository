# standard library
import json
import re
import time

# third-party
# Django
from django.core.paginator import Paginator
from django.http import (Http404, HttpResponse)
from django.shortcuts import render
from django.template import loader
from django.template.loader import render_to_string
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

# local Django
from common.utils import CommitUtils, ViewUtils
from contributions.models import (
    Commit, Developer, Directory, Modification,
    Project, Tag, ANT, LUCENE, MAVEN, OPENJPA, HADOOP,
    CASSANDRA, has_impact_loc_calculation_static_method)

GR = GitRepository('https://github.com/apache/ant.git')
report_directories = None

# Evolution path
# git log --no-walk --tags --pretty="%h %d %s" --decorate=full --reverse

# TODO: carregar algumas informações uma vez só. Por exemplo: nos relatorios eu carrego alguns valores varias vezes (toda vez que chamo)
def index(request):
    start = time.time()

    title_description = 'Contribuições - Commits'

    project = Project.objects.get(id=request.session['project'])

    tag = ViewUtils.load_tag(request)
    tag_description = tag.description

    load_commits = request.POST.get('load_commits')
    if not load_commits:
        if request.GET.get('load') and request.GET.get('load') == 'true':
            load_commits = True

    if load_commits:
        hash = None
        filter = {}
        if tag.previous_tag is not None:
            commit = Commit.objects.filter(tag_id__lte=tag.id, tag__project__id=request.session['project']).last()
            filter.setdefault('from_tag', tag.previous_tag.description)
            if commit is not None:
                hash = commit.hash
                filter.setdefault('from_commit', hash)
                filter.pop('from_tag', None)

        #  git log --graph --oneline --decorate --tags *.java
        tag_aux = tag.description

        # filter.setdefault('only_in_branch', 'master')
        filter.setdefault('only_in_branch', project.main_branch)
        filter.setdefault('only_modifications_with_file_types', ['.java'])
        filter.setdefault('only_no_merge', True)
        i = 0
        if tag.real_tag_description.find('*'):
            tag_aux = tag
            i += 1
        filter.setdefault('to_tag', tag.real_tag_description)

        # if tag.previous_tag:
        #     filter.setdefault('from_tag', tag.previous_tag.description)
        tag_is_not_first_tag = True
        # filter.pop('from_commit', None)
        # if hash:
        #     filter.setdefault('from_commit', hash)
        #     filter.pop('from_tag', None)

        filter.pop('from_commit', None)
        filter.pop('from_tag', None)
        filter.pop('to_tag', None)
        tags = [x for x in list(Tag.objects.filter(project_id=project.id, id__gte=tag.id, major=True)) if x.id != 16]
        for tag1 in tags:
            # tag1 = Tag.objects.get(id=tag1)
            if tag1.minors:
                if tag1.previous_tag is not None:
                    if 'from_commit' not in filter:
                        if 'from_tag' in filter:
                            filter['from_tag'] = tag1.previous_tag.description
                        else:
                            filter.setdefault('from_tag', tag1.previous_tag.description)
                for minor in list([tag1.real_tag_description] + tag1.minors):
                    # if minor.find('*') == 0 and 'from_commit' not in filter.keys():
                    if minor.find('*') == 0 and 'from_commit' not in filter.keys():
                        filter['from_tag'] = minor.replace('*', '')
                        continue
                    filter['to_tag'] = minor
                    # if hash is not None:
                    #     filter['from_commit'] = commit.hash
                    #     filter.pop('from_tag', None)
                    print(" \n************ VERSAO: " + filter['to_tag'] + ' ***************\n\n')
                    for commit_repository in RepositoryMining(project.project_path, **filter).traverse_commits():
                        commit = __build_and_save_commit__(commit_repository, tag1, filter['to_tag'])

                    # if 'from_tag' in filter.keys():
                    filter['from_tag'] = minor
                    filter.pop('from_commit', None)

            else:
                if tag1.previous_tag is not None:
                    if 'from_tag' in filter:
                        filter['from_tag'] = tag1.previous_tag.description
                    else:
                        filter.setdefault('from_tag', tag1.previous_tag.description)
                if 'to_tag' in filter:
                    filter['to_tag'] = tag1.real_tag_description
                else:
                    filter.setdefault('to_tag', tag1.real_tag_description)
                for commit_repository in RepositoryMining(project.project_path, **filter).traverse_commits():
                    __build_and_save_commit__(commit_repository, tag1, filter['to_tag'])
            __update_commit__(Commit.objects.filter(tag=tag1))

    url_path = 'contributions/index.html'
    current_developer = None
    current_tag_filter = None
    developer_id = request.POST.get("developer_filter_id")
    tag_id = request.POST.get("tag_filter_id")
    if request.GET.get('commits'):
        title_description = 'Contributions - Detalhes do commit'
        url_path = 'developers/detail.html'
    elif request.GET.get('directory_data'):
        latest_commit_list = Directory.objects.filter(visible=True).order_by("id")
        url_path = 'contributions/directories.html'
    else:
        if developer_id or tag_id:
            latest_commit_list = Commit.objects.none()
            if developer_id:
                current_developer = Developer.objects.get(pk=int(developer_id))
                latest_commit_list = latest_commit_list | Commit.objects.filter(author_id=current_developer.id)
            if tag_id:
                current_tag_filter = Tag.objects.get(pk=int(tag_id))
                if latest_commit_list:
                    latest_commit_list = latest_commit_list & Commit.objects.filter(tag_id=current_tag_filter.id)
                else:
                    latest_commit_list = Commit.objects.filter(tag_id=current_tag_filter.id)
            latest_commit_list = latest_commit_list.order_by("tag_id", "author__name")
        elif tag:
            latest_commit_list = load_commits_from_tags(tag)
        else:
            latest_commit_list = Commit.objects.all().order_by("tag_id", "author__name", "committer_date")
        paginator = Paginator(latest_commit_list, 100)

        page = request.GET.get('page')
        latest_commit_list = paginator.get_page(page)

    # list_commits(request)

    template = loader.get_template(url_path)
    context = {
        'title': title_description,
        'latest_commit_list': latest_commit_list,
        'tag': tag_description,
        'current_developer': current_developer,
        'current_tag_filter': current_tag_filter,
    }
    json_response = []
    if request.is_ajax():
        result = {'html': render_to_string(url_path, {'latest_commit_list': latest_commit_list})}
        return HttpResponse(json.dumps(result, ensure_ascii=False),
                            content_type='application/json')
        # return HttpResponse(json.dumps(json_response),
        #                     content_type='application/json')
    end = time.time()

    print("Tempo total: " + str(end - start))

    return HttpResponse(template.render(context, request))


def __build_and_save_commit__(commit_repository, tag, real_tag):
    # posso pegar a quantidade de commits até a tag atual e ja procurar a partir daí. pra ele nao ter que ficar
    # buscndo coisa que ja buscou. Posso olhar o id do ultimo commit salvo tbm
    commit = Commit.objects.filter(hash=commit_repository.hash)
    if not commit.exists():
        author_name = CommitUtils.strip_accents(commit_repository.author.name)
        committer_name = CommitUtils.strip_accents(commit_repository.committer.name)
        email = commit_repository.author.email.lower()
        login = commit_repository.author.email.split("@")[0].lower()
        m = re.search(
            r'\Submitted\s*([bB][yY])[:]*\s*[\s\S][^\r\n]*[a-zA-Z0-9_.+-]+((\[|\(|\<)|(\s*(a|A)(t|T)\s*|@)[a-zA-Z0-9-]+(\s*(d|D)(O|o)(t|T)\s*|\.)[a-zA-Z0-9-.]+|(\)|\>|\]))',
            commit_repository.msg, re.IGNORECASE)
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
                email_pattern = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", author_and_email,
                                          re.IGNORECASE)
                full_email_pattern = re.search(
                    r'[\sa-zA-Z0-9_.+-]+(\s*(a|A)(t|T)\s*)[a-zA-Z0-9-]+((\s*(d|D)(O|o)(t|T)\s*)[a-zA-Z0-9-. ]+)+',
                    # r'[\sa-zA-Z0-9_.+-]+(\s*(a|A)(t|T)\s*)[a-zA-Z0-9-]+((\s*(d|D)(O|o)(t|T)|.\s*)[a-zA-Z0-9-. ]+)+',
                    author_and_email, re.IGNORECASE)
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

        if author_name == 'Mike McCandless':
            if commit_repository.committer.name == 'Mike McCandless':
                committer_name = 'Michael McCandless'
            author_name = 'Michael McCandless'
        elif author_name == 'jkf' or author_name == 'Martijn Kruithof' or author_name == 'J.M.Martijn Kruithof':
            if commit_repository.committer.name == 'jkf' or commit_repository.committer.name == 'Martijn Kruithof' or commit_repository.committer.name == 'J.M.Martijn Kruithof':
                committer_name = 'Jacobus Martinus Kruithof'
            author_name = 'Jacobus Martinus Kruithof'
        elif author_name == 'Steve Cohen':
            if commit_repository.committer.name == 'Steve Cohen':
                committer_name = 'Steven M. Cohen'
            author_name = 'Steven M. Cohen'
        elif author_name == 'Jesse Glick':
            if commit_repository.committer.name == 'Jesse Glick':
                committer_name = 'Jesse N. Glick'
            author_name = 'Jesse N. Glick'
        elif author_name == 'Gintas Grigelionis':
            if commit_repository.committer.name == 'Gintas Grigelionis':
                committer_name = 'twogee'
            author_name = 'twogee'
        elif author_name == 'Jan Matrne':
            if commit_repository.committer.name == 'Jan Matrne':
                committer_name = 'Jan Materne'
            author_name = 'Jan Materne'
        elif author_name == 'cmanolache':
            if commit_repository.committer.name == 'cmanolache':
                committer_name = 'Costin Manolache'
            author_name == 'Costin Manolache'
        author = Developer.objects.filter(name__iexact=author_name)
        if author.count() == 0:
            if login != 'dev-null' and login != 'ant-dev':
                author = Developer.objects.filter(login=login)
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

        if author.name == commit_repository.committer.name:
            committer = author
        else:
            committer = Developer.objects.filter(name__iexact=committer_name)
            if committer.count() == 0:
                email = commit_repository.committer.email.lower()
                login = email.split("@")[0].lower()
                committer = Developer.objects.filter(login=login)
                if committer.count() > 0:
                    committer = committer[0]
                else:
                    committer = Developer(name=CommitUtils.strip_accents(commit_repository.committer.name),
                                          email=email, login=login)
            else:
                committer = committer[0]

        commit = Commit(hash=commit_repository.hash, tag=tag,
                        parents_str=str(commit_repository.parents)[1:-1].replace(" ", "").replace("'", ""),
                        msg=commit_repository.msg,
                        author=author, author_date=commit_repository.author_date,
                        committer=committer,
                        committer_date=commit_repository.committer_date, real_tag_description=real_tag)
        total_modification = 0
        for modification_repo in commit_repository.modifications:
            # Save only commits with java file and not in test directory
            if __no_commits_constraints__(modification_repo, tag):
                total_modification = total_modification + 1
                if hasattr(modification_repo, 'nloc'):
                    nloc = modification_repo.nloc
                else:
                    nloc = None
                # diff = GitRepository.parse_diff(modification.diff)
                try:
                    # if total_modification == 1:
                    #     commit.save()
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
                    # To prevent redundat action
                    # time.sleep(.200)
                    modification.save()
                except Exception as e:
                    # raise  # reraises the exceptio
                    print(str(e))
        # else:
        #     # for mod in commit[0].modifications.all():
        #     #     mod.save()
        #     commit[0].save()
        if commit.pk is not None:
            commit.update_component_commits()
    return commit


def visible_directory(request, directory_id):
    directory = Directory.objects.filter(pk=directory_id)
    directory.update(visible=False)
    latest_commit_list = Directory.objects.filter(visible=True).order_by("id")
    url_path = 'contributions/directories.html'
    if request.is_ajax():
        result = {'html': render_to_string(url_path, {'latest_commit_list': latest_commit_list})}
        return HttpResponse(json.dumps(result, ensure_ascii=False),
                            content_type='application/json')

    # return HttpResponseRedirect(reverse("?directory_data=true"))
    request.GET = request.GET.copy()
    request.GET['directory_data'] = True
    return index(request)


def detail_by_hash(request):
    hash = request.POST.get('hash')
    if hash:
        request.session['hash'] = hash
    else:
        if 'hash' in request.session:
            hash = request.session['hash']
        else:
            hash = None

    commit = Commit.objects.filter(hash=hash)
    if commit.count() > 0:
        commit = commit[0]
    else:
        commit = None
    return render(request, 'contributions/detail.html',
                  {'commit': commit, 'current_commit_hash': hash, 'title': 'Detalhes do commit'})


def detail(request, commit_id):
    try:
        commit = Commit.objects.get(pk=commit_id)
        commit.u_cloc
        print(commit.u_cloc)
        print(commit.committer_date)
        for mod in commit.modifications.all():
            GR = GitRepository(commit.tag.project.project_path)

            parsed_lines = GR.parse_diff(mod.diff)
            has_impact_loc_calculation_static_method(parsed_lines)

    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/detail.html', {'commit': commit})


def detail_in_committer(request, committer_id):
    try:
        project = Project.objects.get(project_name="Apache Ant")
        path = ""
        if request.GET.get('path'):
            path = request.GET.get('path')

        tag = ViewUtils.load_tag(request)

        latest_commit_list = list(Commit.objects.filter(committer_id=committer_id, tag_id__lte=tag.id,
                                                        modifications__in=Modification.objects.filter(
                                                            directory_id=int(path))).distinct())
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
    commits = Commit.objects.filter(tag__description=tag.description).distinct()
    if len(commits) == 0:
        return commits
    tag = tag.previous_tag
    while tag:
        commits = commits | (Commit.objects.filter(tag__description=tag.description).distinct())
        tag = tag.previous_tag
    return commits


def __update_commit__(commits):
    for commit in commits:
        lista = commit.parents_str.split(",")
        for parent_hash in lista:
            parent = Commit.objects.filter(hash=parent_hash)
            if parent.count() > 0:
                parent = parent[0]
                parent.children_commit = commit
                commit.parent = parent
                parent.save(update_fields=['children_commit'])


def __no_commits_constraints__(modification, tag):
    path = CommitUtils.true_path(modification)
    directory_str = CommitUtils.directory_to_str(path)

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
        # version4 = Tag.objects.filter(description='releases/lucene-solr/4.0.0').first().id
        # if tag.id >= version4:
        #     lucene_conditions = lucene_conditions and str.lower(directory_str).startswith('lucene/core')

    if tag.project.id == CASSANDRA:
        cassandra_conditions = str.lower(directory_str).startswith(tag.main_directory)
    if tag.project.id == HADOOP:
        # hadoop_conditions = str.lower(directory_str).startswith('src/java')
        dirs = [x.strip() for x in tag.core_component.split(',')]
        hadoop_conditions = False
        for dir in dirs:
            hadoop_conditions = hadoop_conditions or str.lower(directory_str).find(dir) > -1

    # FIXME: Fix the others
    # shiro_conditions = str.lower(directory_str).startswith(tag.main_directory)

    return CommitUtils.modification_is_java_file(path) and str.lower(directory_str).find('test') == -1 and \
           ant_conditions and lucene_conditions and maven_conditions and openjpa_conditions and cassandra_conditions and \
           hadoop_conditions and shiro_conditions
