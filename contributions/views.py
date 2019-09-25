from django.http import HttpResponse, Http404

# Create your views here.
from django.shortcuts import render
from django.template import loader

from contributions.models import Commit


def index(request):
    # latest_commit_list = Commit.objects.all()[:10]
    # output = ", ".join([c.msg for c in latest_commit_list])
    # return HttpResponse(output)
    latest_commit_list = Commit.objects.all()[:10]
    template = loader.get_template('contributions/index.html')
    context = {
        'latest_commit_list': latest_commit_list,
    }
    return HttpResponse(template.render(context, request))

def detail(request, question_id):
    try:
        question = Commit.objects.get(pk=question_id)
    except Commit.DoesNotExist:
        raise Http404("Question does not exist")
    return render(request, 'contributions/detail.html', {'question': question})