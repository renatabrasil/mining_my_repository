import csv
import json
import time

from django.core.paginator import Paginator
from django.db import transaction
from collections import OrderedDict
from django.http import HttpResponse, Http404, StreamingHttpResponse

# Create your views here.
from django.shortcuts import render
from django.template import loader
from django.template.loader import render_to_string
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

from contributions.models import Commit, Project, Developer, Modification, ContributionByAuthorReport, Contributor, Tag, \
    Directory, DirectoryReport, IndividualContribution

GR = GitRepository('https://github.com/apache/ant.git')
report_directories = None

def load_tag(request):
    tag_id = request.POST.get('tag')
    if not tag_id:
        try:
            tag_id = request.session['tag']
        except Exception as e:
            # raise  # reraises the exceptio
            print(str(e))
            tag_id = Tag.objects.all()[0].id
    query = Tag.objects.filter(pk=tag_id)
    if not tag_id:
        tag_description = request.GET.get('tag')
        query = Tag.objects.filter(description=tag_description)
    else:
        request.session['tag'] = tag_id
    tag = None
    if query.count() > 0:
        tag = query[0]
    return tag

# TODO: carregar algumas informações uma vez só. Por exemplo: nos relatorios eu carrego alguns valores varias vezes (toda vez que chamo)
def index(request):
    # tag_text = 'rel/1.2'
    project = Project.objects.get(project_name="Apache Ant")


    start = time.time()

    tag = load_tag(request)
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
                                                   msg=commit_repository.msg,
                                                   author=author, author_date=commit_repository.author_date,
                                                   committer=committer,
                                                   committer_date=commit_repository.committer_date)
                    total_modification = 0
                    for modification_repo in commit_repository.modifications:
                        path = __true_path__(modification_repo)
                        if __modification_is_java_file__(path):
                            total_modification = total_modification + 1
                            directory_str = __directory_str__(path)
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
    if request.GET.get('commits'):

        # latest_commit_list = process_commits(project.commits.all())
        url_path = 'developers/detail.html'
    elif request.GET.get('directories'):
        # latest_commit_list = process_commits_by_directories(Commit.objects.filter(tag__description=tag_description,
        #                                                                           modifications__in=
        #                                                                           Modification.objects.filter(
        #                                                                               path__contains=".java")).distinct())
        latest_commit_list = process_commits_by_directories(request,load_commits_from_tags(tag))
        url_path = 'contributions/detail_by_directories.html'
    elif request.GET.get('author'):
        latest_commit_list = process_commits_by_author(load_commits_from_tags(tag))
        # request.session['commits'] = latest_commit_list

        url_path = 'contributions/detail_by_authors.html'
    else:
        if tag:
            latest_commit_list = load_commits_from_tags(tag)
        else:
            latest_commit_list = Commit.objects.all().order_by("author__name", "committer_date").order_by("author__name",
                                                                                                      "committer_date")
        paginator = Paginator(latest_commit_list, 100)

        page = request.GET.get('page')
        latest_commit_list = paginator.get_page(page)



    template = loader.get_template(url_path)
    context = {
        'latest_commit_list': latest_commit_list,
        'project': project,
        'tag': tag_description,

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
        project = Project.objects.get(project_name="Apache Ant")
        # latest_commit_list = list(Commit.objects.raw('SELECT * FROM contributions_modification m JOIN contributions_commit c '
        #                                         'ON (c.id = m.commit_id) JOIN contributions_developer d ON (d.id = c.committer_id)'
        #                                              'WHERE d.id = '+str(committer_id)).prefetch_related('modifications'))

        path = ""
        if request.GET.get('path'):
            path = request.GET.get('path')

        latest_commit_list = list(Commit.objects.filter(committer__id=committer_id,
                                                        modifications__in=Modification.objects.filter(directory__name=path,
                                                                                                      path__contains=".java"))
                                  .distinct())
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
    tag = load_tag(request)

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
    tag = load_tag(request)

    commits_by_author = {}
    if tag:
        commits_by_author = process_commits_by_author(load_commits_from_tags(tag))
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

   tag=load_tag(request)

   # directories = list(Directory.objects.filter(visible=True)[:3])
   directories = list(Directory.objects.filter(visible=True).order_by("id"))
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

   for author_report in report.items():
       total_commit = 0
       total_file = 0
       total_loc = 0
       for contributor in author_report[1].commits_by_author.items():
           total_file = total_file + contributor[1].total_file
           total_commit = total_commit + contributor[1].total_commit
           total_loc = total_loc + contributor[1].total_loc
       author_report[1].total_java_files = author_report[1].total_java_files + total_file
       author_report[1].total_commits = author_report[1].total_commits + total_commit
       author_report[1].total_loc = author_report[1].total_loc + total_loc
       print(author_report[1].core_developers_threshold_commit)
       author_report[1].commits_by_author = OrderedDict(sorted(author_report[1].commits_by_author.items(),
                                                               key=lambda x: x[1].experience, reverse=True))

   for directory, contributions in report.items():
       report_repo = []
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
           answer.setdefault(directory_report, report_repo)

   for directory_report in directories_report:
       report_repo = []
       for author in directory_report.authors.all():
           report_repo.append(IndividualContribution.objects.filter(author_id=author.pk,
                                                                         directory_report_id=directory_report.pk)[0])
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
def process_commits_by_author(commits):
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


def __true_path__(modification):
    if modification.old_path:
        old_path = modification.old_path.replace("\\", "/")
    if modification.new_path:
        new_path = modification.new_path.replace("\\", "/")
    if modification.change_type.name == 'DELETE':
        path = old_path
    else:
        path = new_path

    return path


def __directory_str__(path):
    index = path.rfind("/")
    directory_str = ""
    if index > -1:
        directory_str = path[:index]
    else:
        directory_str = "/"

    return directory_str


def __modification_is_java_file__(path):
    if path:
        index = path.rfind(".")
        if index > -1:
            return path[index:] == ".java"
    return False