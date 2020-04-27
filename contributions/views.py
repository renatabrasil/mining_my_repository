# standard library
import csv
import json
import re
import time
from collections import OrderedDict

# third-party
import pandas as pd
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

# Django
from django.core.paginator import Paginator
from django.http import (Http404, HttpResponse)
from django.shortcuts import render
from django.template import loader
from django.template.loader import render_to_string

# local Django
from common.utils import CommitUtils, ViewUtils
from contributions.models import (
    Commit, ContributionByAuthorReport, Contributor, Developer, Directory,
    DirectoryReport, IndividualContribution, MetricsReport, Modification,
    Project, ProjectIndividualContribution, ProjectReport, Tag, ComponentCommit)

GR = GitRepository('https://github.com/apache/ant.git')
report_directories = None


# TODO: carregar algumas informações uma vez só. Por exemplo: nos relatorios eu carrego alguns valores varias vezes (toda vez que chamo)
def index(request):
    # tag_text = 'rel/1.2'
    start = time.time()

    project = Project.objects.get(id=request.session['project'])


    tag = ViewUtils.load_tag(request)
    tag_description = tag.description

    load_commits = request.POST.get('load_commits')
    if not load_commits:
        if request.GET.get('load') and request.GET.get('load') == 'true':
            load_commits = True

    if load_commits:
        hash = None

        if tag.previous_tag is not None:
            commit = Commit.objects.filter(tag_id__lte=tag.id, tag__project__id=request.session['project']).last()
            if commit is not None:
                hash = commit.hash

        #  git log --graph --oneline --decorate --tags *.java
        versions = __go_to_first_tag__(tag)[::-1]
        tag_aux = tag.description
        filter = {}
        filter.setdefault('only_in_branch', 'master')
        filter.setdefault('only_modifications_with_file_types', ['.java'])
        filter.setdefault('only_no_merge', True)
        filter.setdefault('from_commit', hash)
        filter.setdefault('to_tag', tag.description)
        if tag.previous_tag:
            filter.setdefault('from_tag', tag.previous_tag.description)
        tag_is_not_first_tag = True
        filter.pop('from_commit', None)
        # if hash is not None:

        if tag.minors:
            for minor in list([tag.description]+tag.minors):
                if minor.find('*') == 0:
                    filter['from_tag'] = minor.replace('*','')
                    continue
                filter['to_tag'] = minor
                # if hash is not None:
                #     filter['from_commit'] = commit.hash
                #     filter.pop('from_tag', None)

                for commit_repository in RepositoryMining(project.project_path, **filter).traverse_commits():
                    commit = __build_and_save_commit__(commit_repository, tag)

                filter['from_tag'] = minor

        else:
            for commit_repository in RepositoryMining(project.project_path,**filter).traverse_commits():
                __build_and_save_commit__(commit_repository, tag)
        __update_commit__(Commit.objects.filter(tag=tag))
        # else:
        #     for tag in versions:
        #         upper_tag = tag_aux.description if tag_aux.max_minor_version_description == '' else tag.max_minor_version_description
        #         filter['to_tag'] = upper_tag
        #         if tag_aux.previous_tag:
        #             filter.setdefault('from_tag', tag_aux.previous_tag.description)
        #             filter.pop('from_commit', None)
        #
        #         for commit_repository in RepositoryMining(project.project_path,**filter).traverse_commits():
        #             __build_and_save_commit__(commit_repository, tag_aux)
        #
        #         if tag_aux.previous_tag:
        #             tag_aux = tag_aux.previous_tag
        #         else:
        #             tag_is_not_first_tag = False

    url_path = 'contributions/index.html'
    current_developer = None
    current_tag_filter = None
    developer_id = request.POST.get("developer_filter_id")
    tag_id = request.POST.get("tag_filter_id")
    if request.GET.get('commits'):
        url_path = 'developers/detail.html'
    elif request.GET.get('directories'):
        latest_commit_list = process_commits_by_directories(request,load_commits_from_tags(tag))
        url_path = 'contributions/detail_by_directories.html'
    elif request.GET.get('project'):
        latest_commit_list = process_commits_by_project(request, load_commits_from_tags(tag))

        url_path = 'contributions/detail_by_project.html'
    elif request.GET.get('author'):
        developer_id = request.POST.get("developer_id")
        if not developer_id:
            developer_id = Developer.objects.all().order_by("name").first().id
        current_developer = Developer.objects.get(pk=developer_id)
        latest_commit_list = process_commits_by_author(developer_id)

        url_path = 'contributions/detail_by_author.html'
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
                    latest_commit_list= Commit.objects.filter(tag_id=current_tag_filter.id)
            latest_commit_list=latest_commit_list.order_by("tag_id", "author__name")
        elif tag:
            latest_commit_list = load_commits_from_tags(tag)
        else:
            latest_commit_list = Commit.objects.all().order_by("id","author__name", "committer_date")
        paginator = Paginator(latest_commit_list, 100)

        page = request.GET.get('page')
        latest_commit_list = paginator.get_page(page)

    # list_commits(request)

    template = loader.get_template(url_path)
    context = {
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


def __build_and_save_commit__(commit_repository, tag):
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

        if author_name == 'jkf' or author_name == 'Martijn Kruithof' or author_name == 'J.M.Martijn Kruithof':
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
                        committer_date=commit_repository.committer_date)
        total_modification = 0
        for modification_repo in commit_repository.modifications:
            path = CommitUtils.true_path(modification_repo)
            directory_str = CommitUtils.directory_to_str(path)
            # Save only commits with java file and not in test directory
            if CommitUtils.modification_is_java_file(path) and str.lower(directory_str).find('test') == -1\
                    and str.lower(directory_str).find('proposal') == -1 and str.lower(directory_str).startswith('lucene/core'):
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

def data_by_directory(request, directory_id):
    response = HttpResponse(content_type='text/csv')

    directory = Directory.objects.filter(id=directory_id)[0]
    directories_report = DirectoryReport.objects.filter(directory_id=directory_id).order_by('tag__id')

    response['Content-Disposition'] = 'attachment; filename='+ directory.name +'.csv'
    writer = csv.writer(response)

    writer.writerow(['Version', 'Experience', 'Mean', 'Median','Standard deviation'])
    for report in directories_report:

        writer.writerow([report.tag.description, report.experience, report.mean, report.median, report.standard_deviation])
    return response

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
    return render(request, 'contributions/detail.html', {'commit': commit, 'current_commit_hash': hash})

def detail(request, commit_id):
    try:
        commit = Commit.objects.get(pk=commit_id)
        commit.u_cloc
        print(commit.u_cloc)

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
                                                        modifications__in=Modification.objects.filter(directory_id=int(path))).distinct())
        context = {
            'latest_commit_list': latest_commit_list,
            'project': project,
        }
    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/index.html', context)


def export_to_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    project = Project.objects.get(project_name="Apache Ant")
    tag = ViewUtils.load_tag(request)

    # Making data frame from the csv file
    df = pd.read_csv("directory_ownership_metrics - rel_1.1.csv")
    df[:10]
    p = df.corr(method='pearson')
    p.style.background_gradient(cmap='coolwarm')
    # plt.matshow(p)
    # plt.show()


    file_name = "directory_ownership_metrics - " + tag.description
    response['Content-Disposition'] = 'attachment; filename='+file_name+'.csv'

    writer = csv.writer(response)

    commits_by_directory = {}
    if tag:
        commits_by_directory = process_commits_by_directories(request,load_commits_from_tags(tag))
        writer.writerow(["Tag:", tag.description])
    for directory, infos in commits_by_directory.items():
        i = 1

        writer.writerow(
            ["##################################################################################", "", "", "", "", ""])
        writer.writerow([directory.directory.name, "", "", "", "", ""])
        writer.writerow(["","    Bird metrics", "", "", "", ""])
        writer.writerow(["","    Minor contributors:", directory.minor, "", "", ""])
        writer.writerow(["","    Major contributors:", directory.major, "", "", ""])
        writer.writerow(["","    Ownership:", directory.ownership, "", "", ""])
        writer.writerow(["--", "", "", "", ""])
        writer.writerow(["","    Metricas usadas para classificar tipos de desenvolvedores (JOBLIN et al., 2017)", "", "", "", ""])
        writer.writerow(["","    Threshold (experience): ", directory.experience_threshold])

        writer.writerow(["---------------------------------------------------------------------------------"])
        writer.writerow(["","Classificacao de desenvolvedores por experiencia"])
        writer.writerow([""])
        writer.writerow(["","Core developers"])
        i = 1
        for core_dev in directory.core_developers_experience:
            row = [i]
            row.append(core_dev.name)
            writer.writerow(row)
            i = i + 1
        writer.writerow([""])
        writer.writerow(["","Peripheral developers"])
        i = 1
        for author in directory.peripheral_developers_experience:
            row = [i]
            row.append(author.name)
            writer.writerow(row)
            i = i + 1

        writer.writerow([""])
        writer.writerow(['#', 'Author', 'Commit count', 'File count', 'LOC count',
                         'Ownership (commits)', 'Ownership (files)', 'Ownership (loc)', 'Experience', " ",
                         "Mean", "Median", "Standard deviation"])
        i = 1
        for info_contribution in infos:
            row = [i]
            row.append(info_contribution.author.name)
            row.append(info_contribution.commits)
            row.append(info_contribution.files)
            row.append(info_contribution.cloc)
            row.append(info_contribution.ownership_commits)
            row.append(info_contribution.ownership_files)
            row.append(info_contribution.ownership_cloc)
            row.append(info_contribution.experience)
            if i == 1:
                row.append(" ")
                row.append(directory.mean)
                row.append(directory.median)
                row.append(directory.standard_deviation)
            writer.writerow(row)
            i = i + 1
        writer.writerow(
            ["", "Total", directory.total_commits, directory.total_files, directory.total_cloc,
             1, 1, 1, 1])

    return response

def export_to_csv_commit_by_author(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estatisticas_projeto.csv"'
    writer = csv.writer(response)

    project = Project.objects.get(project_name="Apache Ant")
    tag = ViewUtils.load_tag(request)

    commits_by_author = {}
    if tag:
        commits_by_author = process_commits_by_project(request, load_commits_from_tags(tag))
        writer.writerow(["Tag:", tag.description])
    # commits_by_author = request.session['commits']




    writer.writerow(["Parametros", "", "", "", "", ""])
    writer.writerow([" | Threshold (file): ", commits_by_author.core_developers_threshold_file, " | Threshold (commit):",
                     commits_by_author.core_developers_threshold_commit, " | Threshold (experience): ",
                     commits_by_author.core_developers_threshold_experience , ""])
    writer.writerow(["Classificacao de desenvolvedores por experiencia"])
    writer.writerow([""])
    writer.writerow(["Core developers"])
    i = 1
    for author in commits_by_author.core_developers_experience:
        row = [i]
        row.append(author.name)
        writer.writerow(row)
        i = i + 1
    writer.writerow([""])
    writer.writerow(["Peripheral developers"])
    i = 1
    for author in commits_by_author.peripheral_developers_experience:
        row = [i]
        row.append(author.name)
        writer.writerow(row)
        i = i + 1

    writer.writerow([""])

    writer.writerow(['#', 'Author', 'Commit count', 'File count', 'LOC count',
                     'Ownership (commits)', 'Ownership (files)', 'Ownership (loc)', 'Experience'])
    i = 1
    for commits in commits_by_author.commits_by_author.items():
        row = [i]
        row.append(commits[0].name)
        row.append(commits[1].commit_count)
        row.append(commits[1].file_count)
        row.append(commits[1].loc_count)
        row.append(commits[1].commit_percentage)
        row.append(commits[1].file_percentage)
        row.append(commits[1].loc_percentage)
        row.append(commits[1].experience)
        writer.writerow(row)
        i = i + 1
    writer.writerow(
        ["", "Total", commits_by_author.total_java_files, commits_by_author.total_commits, commits_by_author.total_loc,
         1, 1, 1, 1])

    return response


""" Load all commits including all previous tag of current tag
param: current tag
return all commits up to current tag """
def load_commits_from_tags(tag):
   commits = Commit.objects.filter(tag__description=tag.description).distinct().order_by("id")
   if len(commits) == 0:
       return commits
   tag = tag.previous_tag
   while tag:
       commits = commits | (Commit.objects.filter(tag__description=tag.description).distinct().order_by("id"))
       # (Commit.objects.filter(tag__description=tag.description, modifications__in=
       # Modification.objects.filter(
       #     path__contains=".java")).distinct())
       tag = tag.previous_tag
   return commits


# Other methods (most auxiliary)
# returns: dictionary = key: directory
#               ContributionByAuthorReport
#                     - dict: commits_by_author(Developer, Contributor)
#                     - integer: total_commits
#                     - integer: total_java_files
#                     - list: peripheral_developers
#                     - list: core_developers_commits
#                     - float: core_developers_threshold_loc
#                     - float: core_developers_threshold_file
#                     - float: core_developers_threshold_commit
def process_commits_by_directories(request,commits):
   report = OrderedDict()
   answer = OrderedDict()
   directories_report = list()
   review_modification = []

   forced_refresh = request.POST.get("refresh") if request.POST.get("refresh") else False

   tag=ViewUtils.load_tag(request)

   directories = Directory.objects.filter(visible=True).order_by("id")
   if forced_refresh:
       IndividualContribution.objects.filter(
           directory_report__in=DirectoryReport.objects.filter(tag_id=tag.id)).delete()
       DirectoryReport.objects.filter(tag_id=tag.id).delete()

   for directory in directories:
       directory_report = DirectoryReport.objects.filter(directory_id=directory.pk, tag_id=tag.pk)
       if len(directory_report) == 0:
           report.setdefault(directory, ContributionByAuthorReport())
       else:
           directories_report.append(directory_report[0])

   if forced_refresh or report:
       files = []
       for commit in commits:
           if commit.u_cloc > 0:
               for modification in commit.modifications.all():
                   if modification.u_cloc > 0 and modification.is_java_file:
                       if modification.directory in report:
                           # Second hierarchy
                           if commit.author not in report[modification.directory].commits_by_author:
                               report[modification.directory].commits_by_author.setdefault(commit.author,
                                                                                           Contributor(commit.author))
                           if commit not in report[modification.directory].commits_by_author[commit.author].commits:
                               report[modification.directory].commits_by_author[commit.author].commits.append(commit)
                               report[modification.directory].commits_by_author[commit.author].commit_count += 1
                               report[modification.directory].commits_by_author[commit.author].total_commit += 1
                           # to avoid duplicate (should be fixed soon)
                           if modification not in review_modification:
                               if modification.file not in report[modification.directory].commits_by_author[commit.author].files:
                                   report[modification.directory].commits_by_author[commit.author].file_count += 1
                                   report[modification.directory].commits_by_author[commit.author].files.append(
                                       modification.file)
                                   report[modification.directory].commits_by_author[commit.author].total_file += 1
                               if modification.file not in files:
                                   # report[modification.directory].commits_by_author[commit.author].total_file += 1
                                   files.append(modification.file)
                               report[modification.directory].commits_by_author[commit.author].loc_count += modification.u_cloc
                               report[modification.directory].commits_by_author[commit.author].total_loc += modification.u_cloc

                           review_modification.append(modification)

   for directory,author_report in report.items():
       total_commit = 0
       total_file = 0
       total_loc = 0
       for developer, contributor in author_report.commits_by_author.items():
           total_file += contributor.total_file
           total_commit += contributor.total_commit
           total_loc += contributor.total_loc
       author_report.total_java_files += total_file
       author_report.total_commits += total_commit
       author_report.total_loc += total_loc
       print(author_report.core_developers_threshold_commit)

   for directory, contributions in report.items():
       report_repo = []
       if len(contributions.commits_by_author) > 0:
           directory_report = DirectoryReport(tag=tag, directory=directory, total_cloc=contributions.total_loc,
                                          total_files=contributions.total_java_files, total_commits=contributions.total_commits,
                                          cloc_threshold=0.0, file_threshold=contributions.core_developers_threshold_file,
                                          commit_threshold=contributions.core_developers_threshold_commit,
                                          experience_threshold=contributions.core_developers_threshold_experience)
           directory_report.save()


           for author, contribution in contributions.commits_by_author.items():
               contribution_repo = IndividualContribution.objects.filter(author_id=author.pk,
                                                                         directory_report_id=directory_report.pk)
               if not contribution_repo:
                   contribution_repo = IndividualContribution(author=author, directory_report=directory_report,
                                                     cloc=contribution.loc_count, files=contribution.file_count,
                                                    commits=contribution.commit_count,
                                                    ownership_cloc=contribution.loc_percentage,
                                                    ownership_files = contribution.file_percentage,
                                                    ownership_commits=contribution.commit_percentage,
                                                    experience=contribution.experience)
                   contribution_repo.save()
               report_repo.append(contribution_repo)
           directory_report.calculate_statistical_metrics()
           if len(report_repo) > 0:
               report_repo = sorted(report_repo, key=lambda x: x.experience_bf, reverse=True)
               answer.setdefault(directory_report, report_repo)

   for directory_report in directories_report:
       report_repo = []
       for author in directory_report.authors.all():
           report_repo.append(IndividualContribution.objects.filter(author_id=author.pk,
                                                                         directory_report_id=directory_report.pk)[0])
       report_repo = sorted(report_repo, key=lambda x: x.experience_bf, reverse=True)
       if len(report_repo) > 0:
           answer.setdefault(directory_report, report_repo)

   return answer

# TODO: Create ProjectReport model to save its state
# returns: ContributionByAuthorReport
#                     - dict: commits_by_author(Developer, Contributor)
#                     - integer: total_commits
#                     - integer: total_java_files
#                     - list: peripheral_developers
#                     - list: core_developers_commits
#                     - float: core_developers_threshold_loc
#                     - float: core_developers_threshold_file
#                     - float: core_developers_threshold_commit
def process_commits_by_project(request, commits):
   answer_report = list()
   report = ContributionByAuthorReport()
   project_reports = list()

   forced_refresh = request.POST.get("refresh") if request.POST.get("refresh") else False
   tag = ViewUtils.load_tag(request)

   if forced_refresh:
       ProjectIndividualContribution.objects.filter(
           project_report__in=ProjectReport.objects.filter(tag_id=tag.id)).delete()
       ProjectReport.objects.filter(tag_id=tag.id).delete()

   project_report = ProjectReport.objects.filter(tag_id=tag.pk)
   contributions = ProjectIndividualContribution.objects.filter(project_report__in=ProjectReport.objects.filter(tag_id=tag.id))

   for developer in contributions:
       report.commits_by_author.setdefault(developer.author, None)

   total_commits = 0
   total_java_files = 0
   total_loc = 0
   for commit in commits:
       if commit.u_cloc > 0 and commit.number_of_java_files > 0:
           if not __author_is_in_project_report__(report, commit.author):
               if commit.author not in report.commits_by_author:
                   report.commits_by_author.setdefault(commit.author, Contributor(commit.author))
               report.commits_by_author[commit.author].commit_count += 1
               for modification in commit.modifications.all():
                   if modification.u_cloc > 0:
                       if modification.is_java_file:
                           if modification.file not in report.commits_by_author[commit.author].files:
                               report.commits_by_author[commit.author].file_count += 1
                               total_java_files += 1
                               report.commits_by_author[commit.author].files.append(modification.file)
                           report.commits_by_author[commit.author].loc_count += modification.u_cloc
                           total_loc += modification.u_cloc
               total_commits += 1
   if contributions.count() == 0:
       report.total_commits = total_commits
       report.total_java_files = total_java_files
       report.total_loc = total_loc
       report.commits_by_author = OrderedDict(sorted(report.commits_by_author.items(),
                                                     key=lambda x: x[1].experience, reverse=True))

   if project_report.count() > 0:
       project_report = project_report[0]
   if len(report.commits_by_author) > 0:
       if not project_report:
           project_report = ProjectReport(tag=tag, total_cloc=report.total_loc, total_files=report.total_java_files,
                                          total_commits=report.total_commits, commit_threshold=report.core_developers_threshold_commit,
                                                                 file_threshold=report.core_developers_threshold_file,
                                                                 cloc_threshold=0.0,
                                                                experience_threshold=report.core_developers_threshold_experience)
           project_report.save()
       answer_report.append(project_report)
       report_repo = []
       for author, author_report in report.commits_by_author.items():
           contribution_repo = ProjectIndividualContribution.objects.filter(author_id=author.pk,
                                                                     project_report_id=project_report.pk)
           if not contribution_repo:
               contribution_repo = ProjectIndividualContribution(author=author, project_report=project_report,
                                                                 cloc=author_report.loc_count, files=author_report.file_count,
                                                                 commits=author_report.commit_count)
               contribution_repo.save()
           else:
               contribution_repo = contribution_repo[0]
           report_repo.append(contribution_repo)
       project_report.calculate_statistical_metrics()

       report_repo = sorted(report_repo, key=lambda x: x.experience_bf, reverse=True)

       answer_report.append(report_repo)

   return answer_report

def process_commits_by_author(developer_id):
    contributions = list(IndividualContribution.objects.filter(author_id=developer_id).order_by("directory_report__tag_id"))
    answer = OrderedDict()
    for contribution in contributions:
        if contribution not in answer:
            directory_report = contribution.directory_report
            first_report = None
            if contribution.directory_report.tag.previous_tag:
                first_report = DirectoryReport.objects.filter(tag_id__lte=contribution.directory_report.tag.previous_tag.id, directory_id=contribution.directory_report.directory.id).order_by(
                "tag_id").first()
            answer.setdefault(directory_report.directory, OrderedDict())
            if first_report:
                i = 1
                while i <= first_report.tag.id:
                    metrics = MetricsReport(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                    metrics.empty = True
                    answer[directory_report.directory].setdefault(Tag.objects.get(pk=i), metrics)
                    i = i + 1

        metrics = MetricsReport(contribution.ownership_commits_in_this_tag, contribution.ownership_files_in_this_tag,
                                                                    contribution.ownership_cloc_in_this_tag,
                                                                    contribution.bf_commit, contribution.bf_file,
                                                                    contribution.bf_cloc,
                                                                    contribution.commit_exp, contribution.file_exp,
                                                                    contribution.cloc_exp, contribution.experience,
                                                                    contribution.experience_bf)
        answer[directory_report.directory].setdefault(directory_report.tag, metrics)

    return answer


def __go_to_first_tag__(tag):
    if tag.previous_tag:
        return [tag.previous_tag]+__go_to_first_tag__(tag.previous_tag)
    else:
        return []

def __author_is_in_project_report__(report, developer):
    return developer in report.commits_by_author and report.commits_by_author[developer] is None

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