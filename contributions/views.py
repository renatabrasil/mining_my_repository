from django.db import transaction
from django.http import HttpResponse, Http404

# Create your views here.
from django.shortcuts import render
from django.template import loader
from pydriller import RepositoryMining
from pydriller.git_repository import GitRepository

from contributions.models import Commit, Project, Developer, Modification


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
            for commit_repository in RepositoryMining("https://github.com/apache/ant.git", only_in_branch='master', to_tag="rel/1.3").traverse_commits():
        #             # Commit.save(commit)
                with transaction.atomic():
                    author = Developer.objects.filter(name=commit_repository.author.name)
                    if author.count() == 0:
                        author = Developer(name=commit_repository.author.name, email=commit_repository.author.email)
                        author.save()
                    committer = Developer.objects.filter(name=commit_repository.committer.name)
                    if committer.count() == 0:
                        committer = Developer(name=commit_repository.committer.name, email=commit_repository.committer.email)
                        committer.save()
                    commit = Commit.objects.create(project=project, hash=commit_repository.hash, msg=commit_repository.msg,
                                    author=author, author_date = commit_repository.author_date, committer=committer,
                                    committer_date=commit_repository.committer_date)
                    for modification_repo in commit_repository.modifications:
                        modification = Modification(commit=commit, old_path=modification_repo.old_path,
                                                    new_path=modification_repo.new_path, change_type=modification_repo.change_type,
                                                    diff=modification_repo.diff, source_code=modification_repo.source_code,
                                                    source_code_before=modification_repo.source_code_before,
                                                    added=modification_repo.added, removed=modification_repo.removed,
                                                    nloc=modification_repo.nloc, complexity=modification_repo.complexity,
                                                    token_count=modification_repo.token_count)
                        modification.save()




    # latest_commit_list = Commit.objects.all()[:10]
    commits_by_author = Commit.objects.raw("SELECT * FROM contributions_Commit GROUP BY author_id")
    latest_commit_list = Commit.objects.all().order_by("author__name", "committer_date").order_by("author__name", "committer_date")
    template = loader.get_template('contributions/index.html')
    context = {
        'latest_commit_list': latest_commit_list,
        'project': project,

    }
    return HttpResponse(template.render(context, request))

def detail(request, commit_id):
    try:
        commit = Commit.objects.get(pk=commit_id)
    except Commit.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/detail.html', {'commit': commit})