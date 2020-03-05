from itertools import groupby

# third-party
import numpy as np
import pandas as pd
from django.contrib import messages

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.template import loader
from django.urls import reverse

from architecture.models import ArchitecturalMetricsByCommit
from contributions.models import Commit


def index(request):
    template = loader.get_template('data_analysis/index.html')

    if request.method == 'POST':
        print("oi")
    

    context = {
        'title': 'Estatística Descritiva',
    }
    return HttpResponse(template.render(context, request))

def population_means(request):
    commits = Commit.objects.exclude(delta_rmd_components=0)
    # values = set(map(lambda x: x.author, commits))
    metric_by_dev = {}
    population_means_list = []

    try:
        for commit in commits:
            if commit.author not in metric_by_dev:
                metric_by_dev.setdefault(commit.author, [[], []])
            metric_by_dev[commit.author][0].append(commit.author_experience)
            metric_by_dev[commit.author][1].append(commit.delta_rmd_components)

        for exp_arr, degrad_arr in metric_by_dev.values():
            population_means_list.append([np.mean(exp_arr), np.mean(degrad_arr)])

        my_df = pd.DataFrame(population_means_list, columns=['x', 'y'])
        my_df.to_csv('population_means.csv', index=False,
                     header=True)

        messages.success(request, 'Files successfully created!')
    except Exception as e:
        print(e)
        messages.error(request, 'Could not create file! ('+e+')')

    # for i, g in groupby(sorted(commits), key=lambda x: x):
    #     metric_by_dev.append(0)



    return HttpResponseRedirect(reverse('analysis:index', ))
