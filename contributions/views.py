import csv
import json
import time
from io import StringIO
from zipfile import ZipFile

import matplotlib.pyplot as plt

import pandas as pd
from django.core.files import File
from django.core.paginator import Paginator
from django.db import transaction
from collections import OrderedDict
from django.http import HttpResponse, Http404, StreamingHttpResponse, HttpResponseRedirect

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.template import loader, RequestContext
from django.template.loader import render_to_string
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

from architecture.models import Compiled
from common.utils import CommitUtils, ViewUtils
from contributions.models import Commit, Project, Developer, Modification, ContributionByAuthorReport, Contributor, Tag, \
    Directory, DirectoryReport, IndividualContribution, MetricsReport

GR = GitRepository('https://github.com/apache/ant.git')
report_directories = None


# TODO: carregar algumas informações uma vez só. Por exemplo: nos relatorios eu carrego alguns valores varias vezes (toda vez que chamo)
def index(request):
    # tag_text = 'rel/1.2'
    project = Project.objects.get(project_name="Apache Ant")

    start = time.time()

    tag = ViewUtils.load_tag(request)
    tag_description = tag.description

    load_commits = request.POST.get('load_commits')
    if not load_commits:
        if request.GET.get('load') and request.GET.get('load') == 'true':
            load_commits = True

    if load_commits:
        # for commit_repository in RepositoryMining(project.project_path, only_in_branch='master', to_tag=tag_description,
        #                                           from_tag=tag.previous_tag.description if tag.previous_tag else None,
        #                                           only_modifications_with_file_types=['.java'],
        #                                           only_no_merge=True).traverse_commits():
        total_commits = Commit.objects.all().count() - 1
        if total_commits > 0:
            hash = Commit.objects.all()[total_commits].hash
        else:
            hash= None
        for commit_repository in RepositoryMining(project.project_path, only_in_branch='master',
                                                  to_tag=tag_description,
                                                  from_commit=hash,
                                                  only_modifications_with_file_types=['.java'],
                                                  only_no_merge=True).traverse_commits():
            # posso pegar a quantidade de commits até a tag atual e ja procurar a partir daí. pra ele nao ter que ficar
            # buscndo coisa que ja buscou. Posso olhar o id do ultimo commit salvo tbm
            commit = Commit.objects.filter(hash=commit_repository.hash)
            if not commit.exists():
                with transaction.atomic():
                    author = Developer.objects.filter(name=commit_repository.author.name)
                    if author.count() == 0:
                        author = Developer(name=commit_repository.author.name, email=commit_repository.author.email)
                        author.save()
                    else:
                        author = author[0]
                    if commit_repository.author.name == commit_repository.committer.name:
                        committer = author
                    else:
                        committer = Developer.objects.filter(name=commit_repository.committer.name)
                        if committer.count() == 0:
                            committer = Developer(name=commit_repository.committer.name,
                                                  email=commit_repository.committer.email)
                            committer.save()
                        else:
                            committer = committer[0]
                    commit = Commit(project=project, hash=commit_repository.hash, tag=tag,
                                                    parents_str=str(commit_repository.parents)[1:-1].replace(" ","").replace("'",""),
                                                   msg=commit_repository.msg,
                                                   author=author, author_date=commit_repository.author_date,
                                                   committer=committer,
                                                   committer_date=commit_repository.committer_date)
                    total_modification = 0
                    for modification_repo in commit_repository.modifications:
                        path = CommitUtils.true_path(modification_repo)
                        if CommitUtils.modification_is_java_file(path):
                            total_modification = total_modification + 1
                            directory_str = CommitUtils.directory_to_str(path)
                            directory = Directory.objects.filter(name=directory_str)
                            if directory.count() == 0:
                                # directory = Directory(name=directory_str, visible=True, project=project, parent_tag=tag)
                                directory = Directory(name=directory_str, visible=True, project=project)
                                directory.save()
                            else:
                                directory = directory[0]

                            if hasattr(modification_repo, 'nloc'):
                                nloc = modification_repo.nloc
                            else:
                                nloc = None
                            # diff = GitRepository.parse_diff(modification.diff)
                            try:
                                if total_modification == 1:
                                    commit.save()
                                modification = Modification(commit=commit, old_path=modification_repo.old_path,
                                                            new_path=modification_repo.new_path,
                                                            change_type=modification_repo.change_type,
                                                            diff=modification_repo.diff,
                                                            directory=directory,
                                                            source_code=modification_repo.source_code,
                                                            source_code_before=modification_repo.source_code_before,
                                                            added=modification_repo.added,
                                                            removed=modification_repo.removed,
                                                            nloc=nloc,
                                                            complexity=modification_repo.complexity)

                                modification.save()
                            except Exception as e:
                                # raise  # reraises the exceptio
                                print(str(e))


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
        latest_commit_list = process_commits_by_project(load_commits_from_tags(tag))

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
            latest_commit_list = Commit.objects.all().order_by("author__name", "committer_date").order_by("author__name",
                                                                                                      "committer_date")
        paginator = Paginator(latest_commit_list, 100)

        page = request.GET.get('page')
        latest_commit_list = paginator.get_page(page)

    # list_commits(request)

    template = loader.get_template(url_path)
    context = {
        'latest_commit_list': latest_commit_list,
        'project': project,
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

    writer.writerow(['Version', 'Experience', 'Abs Experience', 'Mean', 'Median','Standard deviation'])
    for report in directories_report:

        writer.writerow([report.tag.description, report.experience, report.abs_experience, report.mean, report.median, report.standard_deviation])
    return response



def detail(request, commit_id):
    try:
        diff = ""

        commit = Commit.objects.get(pk=commit_id)
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
        commits_by_author = process_commits_by_project(load_commits_from_tags(tag))
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
   commits = Commit.objects.filter(tag__description=tag.description).distinct()
   if len(commits) == 0:
       return commits
   tag = tag.previous_tag
   while tag:
       commits = commits | (Commit.objects.filter(tag__description=tag.description).distinct())
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
   report_repo = list()
   answer = OrderedDict()
   directories_report = list()
   review_modification = []

   forced_refresh = request.POST.get("refresh") if request.POST.get("refresh") else False

   tag=ViewUtils.load_tag(request)

   # directories = list(Directory.objects.filter(visible=True)[:3])
   directories = Directory.objects.filter(visible=True).order_by("id")
   if forced_refresh:
       IndividualContribution.objects.filter(
           directory_report__in=DirectoryReport.objects.filter(tag_id=tag.id)).delete()
       DirectoryReport.objects.filter(tag_id=tag.id).delete()
   # directories = list(Directory.objects.filter(visible=True, parent_tag__pk=tag.pk))
   for directory in directories:
       directory_report = DirectoryReport.objects.filter(directory_id=directory.pk, tag_id=tag.pk)
       if len(directory_report) == 0:
           report.setdefault(directory, ContributionByAuthorReport())
       else:
           directories_report.append(directory_report[0])
   # report = dict.fromkeys(directories, ContributionByAuthorReport())
   # report = dict.fromkeys([d.name for d in directories], ContributionByAuthorReport())

   if forced_refresh or report:
       # directories_id = [d.id for d in list(report.keys())]
       #
       # if len(directories_id) < 5:
       #     commits = Commit.objects.filter(modifications__in=Modification.objects.filter(directory_id__in=directories_id),
       #                                 tag_id__lte=tag.id)

       for commit in commits:
           number_of_files = 0

           for modification in commit.modifications.all():
               if modification.is_java_file:
                   if modification.directory in report:
                       # Second hierarchy
                       if commit.author not in report[modification.directory].commits_by_author:
                           report[modification.directory].commits_by_author.setdefault(commit.author,
                                                                                       Contributor(commit.author))
                       if commit not in report[modification.directory].commits_by_author[commit.author].commits:
                           report[modification.directory].commits_by_author[commit.author].commits.append(commit)
                           report[modification.directory].commits_by_author[commit.author].commit_count = \
                           report[modification.directory].commits_by_author[commit.author].commit_count + 1
                           report[modification.directory].commits_by_author[commit.author].total_commit = \
                               report[modification.directory].commits_by_author[commit.author].total_commit + 1
                       # to avoid duplicate (should be fixed soon)
                       if modification not in review_modification:
                           report[modification.directory].commits_by_author[commit.author].file_count = \
                           report[modification.directory].commits_by_author[commit.author].file_count + 1
                           report[modification.directory].commits_by_author[commit.author].total_file = \
                           report[modification.directory].commits_by_author[commit.author].total_file + 1
                           report[modification.directory].commits_by_author[commit.author].files.append(modification)
                           report[modification.directory].commits_by_author[commit.author].loc_count = \
                               report[modification.directory].commits_by_author[commit.author].loc_count + modification.cloc
                           report[modification.directory].commits_by_author[commit.author].total_loc = \
                               report[modification.directory].commits_by_author[commit.author].total_loc  + modification.cloc

                       review_modification.append(modification)

   for directory,author_report in report.items():
       total_commit = 0
       total_file = 0
       total_loc = 0
       for developer, contributor in author_report.commits_by_author.items():
           total_file = total_file + contributor.total_file
           total_commit = total_commit + contributor.total_commit
           total_loc = total_loc + contributor.total_loc
           # contributor.boosting_factors(tag.id,directory.id,current_commit_activity,curre)
       author_report.total_java_files = author_report.total_java_files + total_file
       author_report.total_commits = author_report.total_commits + total_commit
       author_report.total_loc = author_report.total_loc + total_loc
       print(author_report.core_developers_threshold_commit)
       # author_report.commits_by_author = OrderedDict(sorted(author_report.commits_by_author.items(),
       #                                                         key=lambda x: x[1].experience, reverse=True))

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
                                                    experience=contribution.experience,
                                                    abs_experience=contribution.abs_experience)
                   contribution_repo.save()
               report_repo.append(contribution_repo)
           directory_report.calculate_statistical_metrics()
           if len(report_repo) > 0:
               report_repo = sorted(report_repo, key=lambda x: x.experience, reverse=True)
               answer.setdefault(directory_report, report_repo)

   for directory_report in directories_report:
       report_repo = []
       for author in directory_report.authors.all():
           report_repo.append(IndividualContribution.objects.filter(author_id=author.pk,
                                                                         directory_report_id=directory_report.pk)[0])
       report_repo = sorted(report_repo, key=lambda x: x.experience, reverse=True)
       if len(report_repo) > 0:
           answer.setdefault(directory_report, report_repo)

    # if not report_directories:
    #     report_directories = report
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
def process_commits_by_project(commits):
   report = ContributionByAuthorReport()
   total_commits = 0
   total_java_files = 0
   total_loc = 0
   for commit in commits:
       if commit.author not in report.commits_by_author:
           report.commits_by_author.setdefault(commit.author, Contributor(commit.author))
       report.commits_by_author[commit.author].commit_count = report.commits_by_author[commit.author].commit_count + 1
       for modification in commit.modifications.all():
           if modification.is_java_file:
               report.commits_by_author[commit.author].file_count = report.commits_by_author[
                                                                        commit.author].file_count + 1
               total_java_files = total_java_files + 1
               report.commits_by_author[commit.author].loc_count = report.commits_by_author[
                                                                        commit.author].loc_count + modification.cloc
               total_loc = total_loc + modification.cloc
       total_commits = total_commits + 1
   report.total_commits = total_commits
   report.total_java_files = total_java_files
   report.total_loc = total_loc
   report.commits_by_author = OrderedDict(sorted(report.commits_by_author.items(),
                                                 key=lambda x: x[1].experience, reverse=True))

   return report

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

        metrics = MetricsReport(contribution.ownership_commits, contribution.ownership_files,
                                                                    contribution.ownership_cloc,
                                                                    contribution.bf_commit, contribution.bf_file,
                                                                    contribution.bf_cloc,
                                                                    contribution.commit_exp, contribution.file_exp,
                                                                    contribution.cloc_exp, contribution.experience,
                                                                    contribution.experience_bf)
        answer[directory_report.directory].setdefault(directory_report.tag, metrics)

    return answer






