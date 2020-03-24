import math
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

POPULATION_MEANS = 1
CORRELATION_BY_VERSION = 2
CORRELATION_BY_DEV = 3
MEANS_BY_DEV_AND_VERSION = 4
OVERVIEW_BY_DEV = 5

def index(request):
    template = loader.get_template('data_analysis/index.html')

    if request.method == 'POST':
        print("oi")
    

    context = {
        'title': 'Estatística Descritiva',
    }
    return HttpResponse(template.render(context, request))

def descriptive_statistics(request, type):
    metric_by_dev = __process_metrics__(type)
    file_name = 'undefined'
    try:
        if type == POPULATION_MEANS:

            file_name = 'population_means.csv'
            population_means_list = []
            for exp_arr, degrad_arr in metric_by_dev.values():
                population_means_list.append([np.mean(exp_arr), np.mean(degrad_arr)])

            my_df = pd.DataFrame(population_means_list, columns=['x', 'y'])
            my_df.to_csv(file_name, index=False, header=True)
        elif type == CORRELATION_BY_VERSION:

            file_name = 'correlation_version.csv'
            correlation_list = []
            for tag in metric_by_dev:
                my_df = pd.DataFrame(metric_by_dev[tag], columns=['x', 'y'])
                r = my_df.corr(method='spearman').values[0][1]
                correlation_list.append([tag.description, r])

            my_df = pd.DataFrame(correlation_list, columns=['x', 'y'])
            writer = pd.ExcelWriter('correlation_version.xlsx')
            my_df.to_excel(writer, 'Sheet1', index=None, header=True)
            my_df.to_csv(file_name, index=None, header=True)
            # my_df.to_excel(writer, 'Sheet2')
            writer.save()
            print('Correlation by version')
        elif type == CORRELATION_BY_DEV:

            file_name = 'correlation_dev.csv'
            correlation_list = []
            for dev in metric_by_dev:
                my_df = pd.DataFrame(metric_by_dev[dev], columns=['x', 'y'])
                r = my_df.corr(method='spearman').values[0][1]
                if not math.isnan(r):
                    correlation_list.append([dev.name, r])

            my_df = pd.DataFrame(correlation_list, columns=['x', 'y'])
            my_df.to_csv(file_name, index=None, header=True)
            # my_df.to_excel(file_name, sheet_name='correlacao', engine='xlsxwriter', index=None, header=True)
            print('Correlation by dev')
        elif type == MEANS_BY_DEV_AND_VERSION:
            print('means')
        elif type == OVERVIEW_BY_DEV:
            commits_by_dev = []
            file_name = 'overview_by_dev.csv'
            for dev in metric_by_dev:
                commits_by_dev.append([dev.name, Commit.objects.filter(author=dev).count(), metric_by_dev[dev]])
            my_df = pd.DataFrame(commits_by_dev, columns=['dev', 'total_commits', 'contributions'])
            my_df.to_csv(file_name, index=None, header=True)
            print('overview by dev')

        my_df.to_csv(file_name, index=False, header=True)
        messages.success(request, 'Files successfully created! File: '+file_name)
    except Exception as e:
        print(e)
        messages.error(request, 'Could not create file! (motive: '+e.args[0]+')')

    return HttpResponseRedirect(reverse('analysis:index', ))

def __process_metrics__(type):
    commits = Commit.objects.exclude(delta_rmd_components=0)
    # values = set(map(lambda x: x.author, commits))
    metric_by_dev = {}

    try:
        for commit in commits:

            if type == POPULATION_MEANS:
                key = commit.author

                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, [[], []])
                metric_by_dev[key][0].append(commit.author_experience)
                metric_by_dev[key][1].append(commit.delta_rmd_components)

            elif type == CORRELATION_BY_DEV:
                key = commit.author
                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, [])

                metric_by_dev[key].append([commit.author_experience, commit.delta_rmd_components])

            elif type == CORRELATION_BY_VERSION:
                key = commit.tag

                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, [])
                metric_by_dev[key].append([commit.author_experience, commit.delta_rmd_components])
            elif type == OVERVIEW_BY_DEV:

                key = commit.author
                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, 0)
                metric_by_dev[key] += 1

            # if key not in metric_by_dev:
            #     metric_by_dev.setdefault(key, [[], []])
            # metric_by_dev[key][0].append(commit.author_experience)
            # metric_by_dev[key][1].append(commit.delta_rmd_components)

    except Exception as e:
        raise e

    return metric_by_dev