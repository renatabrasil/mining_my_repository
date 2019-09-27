from django.db import transaction
from django.http import HttpResponse, Http404

# Create your views here.
from django.shortcuts import render
from django.template import loader
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

from contributions.models import Commit, Project, Developer, Modification
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
                        diff = GitRepository.parse_diff(modification.diff)
                        modification = Modification(commit=commit, old_path=modification_repo.old_path,
                                                    new_path=modification_repo.new_path, change_type=modification_repo.change_type,
                                                    diff=modification_repo.diff, source_code=modification_repo.source_code,
                                                    source_code_before=modification_repo.source_code_before,
                                                    added=modification_repo.added, removed=modification_repo.removed,
                                                    nloc=modification_repo.nloc, complexity=modification_repo.complexity,
                                                    token_count=token_count)
                        modification.save()

    if request.GET.get('commits'):
        latest_commit_list = Commit.objects.all().order_by("author__name", "committer_date").order_by("author__name",
                                                                                                      "committer_date")
    else:
        latest_commit_list = process_commits(project.commits.all())

    # latest_commit_list = Commit.objects.all()[:10]
    # commits_by_author = Commit.objects.raw("SELECT * FROM contributions_Commit GROUP BY author_id")
    template = loader.get_template('contributions/index.html')
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
        committer = Developer.objects.get(pk=committer_id)
    except Developer.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'developers/detail.html', {'committer': committer})

def strip_end(text, suffix):
    if text:
        index = text.rfind(suffix)
        if index > -1:
            return text[:index]
    return text

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
            if strip_end(modification.path, "/") == "src/main/org/apache/tools/ant/taskdefs/optional/depend":
                print("proposal/anteater/source/coretasks/buildtarget/org/apache/ant/buildtarget")
        commit_by_committer[commit.committer][0].append(commit)
        commit_by_committer[commit.committer][1] = commit_by_committer[commit.committer][1] + delta_by_commit
        total_delta = total_delta + delta_by_commit
        total_commits = total_commits + 1

    # percorrer o mapa e calcular a contribuicao em % ja com o 'total_delta'
    for key, value in commit_by_committer.items():
        weight = commit_by_committer[key][1]
        number_of_commits = len(commit_by_committer[key][0])
        commit_by_committer[key][2] = (weight*number_of_commits)/(total_delta*total_commits)
    return commit_by_committer

def process_commits_by_directories(commits):
    commits_by_directory = {}

    return commits_by_directory