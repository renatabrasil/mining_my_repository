import csv
from django.db import transaction
from collections import OrderedDict
from django.db.models import Sum
from django.http import HttpResponse, Http404, StreamingHttpResponse
import numpy as np

# Create your views here.
from django.shortcuts import render
from django.template import loader
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

from contributions.models import Commit, Project, Developer, Modification, ContributionByAuthorReport, Contributor

GR = GitRepository('https://github.com/apache/ant.git')



def index(request):
    # latest_commit_list = Commit.objects.all()[:10]
    # output = ", ".join([c.msg for c in latest_commit_list])
    # return HttpResponse(output)

    project = Project.objects.get(project_name="Apache Ant")

    save_commits = False
    if request.GET.get('load') and request.GET.get('load') == 'true':
        save_commits = True

    if save_commits:
        if not project.commits.all():
            for commit_repository in RepositoryMining("https://github.com/apache/ant.git", only_in_branch='master',
                                                      to_tag="rel/1.3", only_modifications_with_file_types=['.java'],
                                                      only_no_merge=True).traverse_commits():
        #             # Commit.save(commit)
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
                            committer = Developer(name=commit_repository.committer.name, email=commit_repository.committer.email)
                            committer.save()
                        else:
                            committer = committer[0]
                    commit = Commit.objects.create(project=project, hash=commit_repository.hash, msg=commit_repository.msg,
                                    author=author, author_date = commit_repository.author_date, committer=committer,
                                    committer_date=commit_repository.committer_date)
                    for modification_repo in commit_repository.modifications:
                        if hasattr(modification_repo, 'token_count'):
                            token_count = modification_repo.token_count
                        else:
                            token_count = None
                        if hasattr(modification_repo, 'nloc'):
                            nloc = modification_repo.nloc
                        else:
                            nloc = None
                        # diff = GitRepository.parse_diff(modification.diff)
                        try:
                            print("nLoc: " + str(modification_repo.nloc))
                            modification = Modification(commit=commit, old_path=modification_repo.old_path,
                                                        new_path=modification_repo.new_path, change_type=modification_repo.change_type,
                                                        diff=modification_repo.diff, source_code=modification_repo.source_code,
                                                        source_code_before=modification_repo.source_code_before,
                                                        added=modification_repo.added, removed=modification_repo.removed,
                                                        nloc=nloc,
                                                        complexity=modification_repo.complexity,
                                                        token_count=token_count)
                            modification.save()
                        except Exception as e:
                            # raise  # reraises the exceptio
                            print(str(e))

    url_path = 'contributions/index.html'
    if request.GET.get('commits'):

        latest_commit_list = process_commits(project.commits.all())
        url_path = 'developers/detail.html'
    elif request.GET.get('directories'):
        latest_commit_list = process_commits_by_directories(Commit.objects.filter(modifications__in=
                                                                                  Modification.objects.filter(path__contains=".java")).distinct())
        url_path = 'contributions/detail_by_directories.html'
    elif request.GET.get('author'):
        latest_commit_list = process_commits_by_author(Commit.objects.order_by("author__name"))
        # request.session['commits'] = latest_commit_list

        url_path = 'contributions/detail_by_authors.html'
    else:
        latest_commit_list = Commit.objects.all().order_by("author__name", "committer_date").order_by("author__name",
                                                                                                      "committer_date")

    template = loader.get_template(url_path)
    context = {
        'latest_commit_list': latest_commit_list,
        # 'latest_commit_list': processed_commits,
        'project': project,

    }
    return HttpResponse(template.render(context, request))

def detail(request, commit_id):
    try:
        diff = ""

        commit = Commit.objects.get(pk=commit_id)
        # TODO: implement diff to show in commit details page
        # for modification in commit.modifications.all():
        #     parsed_lines = GR.parse_diff(modification.diff)
        #
        #     added = parsed_lines['added']
        #     deleted = parsed_lines['deleted']
        #
        #     print('Added: {}'.format(added))  # result: Added: [(4, 'log.debug("b")')]
        #     print('Deleted: {}'.format(deleted))  # result: Deleted: [(3, 'cc')]
    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/detail.html', {'commit': commit})


def detail_in_committer(request, committer_id):
    try:

        # committer = Developer.objects.get(pk=committer_id)
        # template = loader.get_template(url_path)
        project = Project.objects.get(project_name="Apache Ant")
        # latest_commit_list = list(Commit.objects.raw('SELECT * FROM contributions_modification m JOIN contributions_commit c '
        #                                         'ON (c.id = m.commit_id) JOIN contributions_developer d ON (d.id = c.committer_id)'
        #                                              'WHERE d.id = '+str(committer_id)).prefetch_related('modifications'))

        path = ""
        if request.GET.get('path'):
            path = request.GET.get('path')


        latest_commit_list = list(Commit.objects.filter(committer__id=committer_id,
                                                   modifications__in=Modification.objects.filter(directory=path,
                                                                                                 path__contains=".java"))
                                                                                                .distinct())
        # latest_commit_list = []
        # for commit in objs:
        #     latest_commit_list.append(commit)
        context = {
            'latest_commit_list': latest_commit_list,
            # 'latest_commit_list': processed_commits,
            'project': project,
        }
    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/index.html', context)


def export_to_csv(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="directory_ownership_metrics.csv"'

    project = Project.objects.get(project_name="Apache Ant")
    # commits_by_directories= process_commits_by_directories(project.commits.all())
    commits_by_directory = process_commits_by_directories(Commit.objects.order_by("author__name")[:50])

    writer = csv.writer(response)
    writer.writerow(['#', 'Author', 'Commit count', 'File count', 'Ownership (commits)', 'Ownership (files)'])

    for directory, infos in commits_by_directory.items():
        i = 1

        writer.writerow(["##################################################################################", "", "", "", "", ""])
        writer.writerow([directory, "", "", "", "", ""])
        writer.writerow(["    Parametros do diretorio", "", "", "", ""])
        writer.writerow(["    Threshold (file):", infos.core_developers_threshold_file, "Threshold (file):",
                         infos.core_developers_threshold_commit, ""])

        writer.writerow(["---------------------------------------------------------------------------------"])
        writer.writerow(["Classificacao de desenvolvedores por commits"])
        writer.writerow([""])
        writer.writerow(["Core developers"])
        i = 1
        for core_dev in infos.core_developers_commits:

            row = [i]
            row.append(core_dev.name)
            writer.writerow(row)
            i = i + 1
        writer.writerow([""])
        writer.writerow(["Peripheral developers"])
        i = 1
        for author in infos.peripheral_developers_commits:
            row = [i]
            row.append(author.name)
            writer.writerow(row)
            i = i + 1

        writer.writerow([""])
        i=1
        for author, info_contribution in infos.commits_by_author.items():
            row = [i]
            row.append(author.name)
            row.append(info_contribution.commit_count)
            row.append(info_contribution.file_count)
            row.append(info_contribution.commit_percentage)
            row.append(info_contribution.file_percentage)
            writer.writerow(row)
            i = i + 1
        writer.writerow(
            ["", "Total", infos.total_java_files, infos.total_commits,
             1, 1])

    return response

def export_to_csv_commit_by_author(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="estatisticas_projeto.csv"'

    project = Project.objects.get(project_name="Apache Ant")
    commits_by_author = process_commits_by_author(Commit.objects.order_by("author__name"))
    # commits_by_author = request.session['commits']

    writer = csv.writer(response)

    writer.writerow(["Parametros", "", "", "", "", ""])
    writer.writerow(["Threshold (file): ", commits_by_author.core_developers_threshold_file, "Threshold (commit):",
                     commits_by_author.core_developers_threshold_commit, "", ""])
    writer.writerow(["Classificacao de desenvolvedores por commits"])
    writer.writerow([""])
    writer.writerow(["Core developers"])
    i = 1
    for author in commits_by_author.core_developers_commits:
        row = [i]
        row.append(author.name)
        writer.writerow(row)
        i = i + 1
    writer.writerow([""])
    writer.writerow(["Peripheral developers"])
    i = 1
    for author in commits_by_author.peripheral_developers_commits:
        row = [i]
        row.append(author.name)
        writer.writerow(row)
        i = i + 1

    writer.writerow([""])

    writer.writerow(['', 'Author', 'Commit count', 'File Count', 'Ownership (commit)', 'Ownership (file)'])
    i = 1
    for commits in commits_by_author.commits_by_author.items():
        row = [i]
        row.append(commits[0].name)
        row.append(commits[1].commit_count)
        row.append(commits[1].file_count)
        row.append(commits[1].commit_percentage)
        row.append(commits[1].file_percentage)
        writer.writerow(row)
        i = i +1
    writer.writerow(
            ["", "Total", commits_by_author.total_java_files, commits_by_author.total_commits,
             1, 1])

    return response

# Other methods (most auxiliary)
# dictionary = key: committer
#              value: info
# info:
#       [0] number of commits
#       [1] contribution
#       [2] % contribution
def process_commits(commits):
    commit_by_committer = {}
    total_delta = 0
    total_commits = 0
    for commit in commits:
        delta_by_commit = 0
        if commit.committer not in commit_by_committer:
            commit_by_committer.setdefault(commit.committer, [[], 0, 0.0])
        for modification in commit.modifications.all():
            delta_by_commit = delta_by_commit + modification.delta
        commit_by_committer[commit.committer][0].append(commit)
        commit_by_committer[commit.committer][1] = commit_by_committer[commit.committer][1] + delta_by_commit
        total_delta = total_delta + delta_by_commit
        total_commits = total_commits + 1

    # percorrer o mapa e calcular a contribuicao em % ja com o 'total_delta'
    for key, value in commit_by_committer.items():
        weight = commit_by_committer[key][1]
        number_of_commits = len(commit_by_committer[key][0])
        try:
            commit_by_committer[key][2] = (weight*number_of_commits)/(total_delta*total_commits)
        except ZeroDivisionError:
            commit_by_committer[key][2] = 0.0
    return commit_by_committer

# Other methods (most auxiliary)
# dictionary = key: directory
#               [0]: value: author dictionary
#               [1]: total number of commits
#               [2]: total number of java files committed
# dictionary author:
#       key: author
#       [0] list of commits
#       [1] total number of java files committed
#       [2] % contribution
#
# TODO: Create a model to embed this report (a transient object)
def process_commits_by_directories(commits):
    report = {}
    review_modification = []

    for commit in commits:
        number_of_files = 0

        for modification in commit.modifications.all():
            if modification.is_java_file:
                # First hierarchy
                if modification.directory not in report:
                    report.setdefault(modification.directory, ContributionByAuthorReport())
                # Second hierarchy
                if commit.author not in report[modification.directory].commits_by_author:
                    report[modification.directory].commits_by_author.setdefault(commit.author, Contributor(commit.author))
                if commit not in report[modification.directory].commits_by_author[commit.author].commits:
                    report[modification.directory].commits_by_author[commit.author].commits.append(commit)
                    report[modification.directory].commits_by_author[commit.author].commit_count = report[modification.directory].commits_by_author[commit.author].commit_count +1
                    report[modification.directory].commits_by_author[commit.author].total_commit = \
                    report[modification.directory].commits_by_author[commit.author].total_commit + 1
                # to avoid duplicate (should be fixed soon)
                if modification not in review_modification:
                    report[modification.directory].commits_by_author[commit.author].file_count = report[modification.directory].commits_by_author[commit.author].file_count + 1
                    report[modification.directory].commits_by_author[commit.author].total_file = report[modification.directory].commits_by_author[commit.author].total_file + 1
                    report[modification.directory].commits_by_author[commit.author].files.append(modification)
                review_modification.append(modification)


    for author_report in report.items():
        total_commit = 0
        total_file = 0
        author_report[1].commits_by_author = OrderedDict(sorted(author_report[1].commits_by_author.items(),
                                                      key=lambda x: x[1].commit_count, reverse=True))
        for contributor in author_report[1].commits_by_author.items():
            total_file = total_file + contributor[1].total_file
            total_commit = total_commit + contributor[1].total_commit
        author_report[1].total_java_files = author_report[1].total_java_files + total_file
        author_report[1].total_commits = author_report[1].total_commits + total_commit
        print(author_report[1].core_developers_threshold_commit)


    return report


# TODO: implementar as consultas usando django query
# Exemplo: Commit.objects.filter(committer__name="James Duncan Davidson")
def process_commits_by_author(commits):
    report = ContributionByAuthorReport()
    total_commits = 0
    total_java_files = 0
    list_java_files = []
    for commit in commits:
        if commit.author not in report.commits_by_author:
            report.commits_by_author.setdefault(commit.author, Contributor(commit.author))
        report.commits_by_author[commit.author].commit_count = report.commits_by_author[commit.author].commit_count + 1
        for modification in commit.modifications.all():
            if modification.is_java_file:
                report.commits_by_author[commit.author].file_count = report.commits_by_author[commit.author].file_count + 1
                total_java_files = total_java_files +1
        total_commits = total_commits +1
    report.total_commits = total_commits
    report.total_java_files = total_java_files
    report.commits_by_author = OrderedDict(sorted(report.commits_by_author.items(),
                                                        key=lambda x: x[1].commit_count, reverse=True))

    return report
