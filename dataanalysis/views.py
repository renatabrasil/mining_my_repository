import math
from collections import OrderedDict
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
from contributions.models import Commit, Tag

POPULATION_MEANS = 1
CORRELATION_BY_VERSION = 2
CORRELATION_BY_DEV = 3
MEANS_BY_DEV_AND_VERSION = 4
OVERVIEW_BY_DEV = 5
MEANS_BY_COMMITS_FREQUENCY = 6

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
            deltas = [len(exp_arr[0]) for exp_arr in metric_by_dev.values()]
            threshold = np.percentile(deltas, 80)
            # metrics = {k: metric_by_dev[k] for k in metric_by_dev.keys() - {'orange'}}
            # devs = [[dev_contributions, np.mean(metric_by_dev[dev_contributions][0]),
            #          np.mean(metric_by_dev[dev_contributions][1])] for dev_contributions in metric_by_dev.keys() if
            #         len(metric_by_dev[dev_contributions][0]) >= threshold]
            devs =[]
            for dev, arrays in metric_by_dev.items():
                exp_arr = arrays[0]
                degrad_arr = arrays[1]
                population_means_list.append([dev.name,np.mean(exp_arr), np.mean(degrad_arr), Commit.objects.filter(author=dev).count(), len(exp_arr)])
                if len(exp_arr) >= threshold:
                    devs.append([dev.name,np.mean(exp_arr), np.mean(degrad_arr), Commit.objects.filter(author=dev).count(), len(exp_arr)])
                # population_means_list.append(
                #     [np.mean(exp_arr), np.mean(degrad_arr), Commit.objects.filter(author=dev).count(),
                #      len(exp_arr)])

            my_df = pd.DataFrame(population_means_list, columns=['author','x', 'y','commits','deltas'])
            my_df.to_csv(file_name, index=False, header=True)
            if len(devs) > 0:
                my_df = pd.DataFrame(devs, columns=['dev', 'x', 'y', 'commits', 'deltas'])
                my_df.to_csv('dev_media.csv', index=False, header=True)
            # my_df = pd.DataFrame(population_means_list, columns=['x', 'y', 'commits', 'deltas'])


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

        elif type == MEANS_BY_COMMITS_FREQUENCY:
            file_name = 'by_commit_frequency.csv'
            frequencies = OrderedDict({'100':[[],[]],'200':[[],[]],'300':[[],[]],'400':[[],[]],'500':[[],[]],'600':[[],[]],'700':[[],[]],'> 800':[[],[]]})
            last_key = '> 800'

            deltas = [len(author_exp) for author_exp in metric_by_dev.values()]
            threshold = np.percentile(deltas, 80)

            # Sem Peter Donald, ele mexeu bastante em um componente que pode nao fazer parte do core do software
            # devs = [dev_contributions for dev_contributions in metric_by_dev.keys() if len(metric_by_dev[dev_contributions]) >= threshold and dev_contributions.id != 41]
            devs = [dev_contributions for dev_contributions in metric_by_dev.keys() if len(metric_by_dev[dev_contributions]) >= threshold]

            means = []

            # Sem Peter Donald, ele mexeu bastante em um componente que pode nao fazer parte do core do software
            commits = Commit.objects.exclude(delta_rmd_components=0).exclude(author_id=41).filter(tag_id__in=Tag.line_1_10_x())
            # Com todos
            # commits = Commit.objects.exclude(delta_rmd_components=0).filter(tag_id__in=Tag.line_1_10_x())

            for commit in commits:
                if any(commit.author == c for c in devs):
                    find = False

                    for freq,exp_degrad_arr in frequencies.items():
                        exp_arr = exp_degrad_arr[0]
                        degrad_arr = exp_degrad_arr[1]
                        if freq.isdigit() and commit.total_commits <= int(freq):
                            exp_arr.append(commit.author_experience)
                            degrad_arr.append(commit.delta_rmd_components)
                            find = True
                            break;
                    if not find:
                        frequencies[last_key][0].append(commit.author_experience)
                        frequencies[last_key][1].append(commit.delta_rmd_components)


            # devs = [[dev_contributions.name, metric_by_dev[dev_contributions][0], metric_by_dev[dev_contributions][1], metric_by_dev[dev_contributions][2]] for
            #         dev_contributions in metric_by_dev.keys() if len(metric_by_dev[dev_contributions]) >= threshold]

            mean_list = []
            for freq, means in frequencies.items():
                mean_list.append([freq,np.mean(means[0]),np.mean(means[1])])

            my_df = pd.DataFrame(mean_list, columns=['commits', 'x', 'y'])

            print("by_commit_frequency.csv")

        my_df.to_csv(file_name, index=False, header=True)
        messages.success(request, 'Files successfully created! File: '+file_name)
    except Exception as e:
        print(e)
        messages.error(request, 'Could not create file! (motive: '+e.args[0]+')')

    return HttpResponseRedirect(reverse('analysis:index', ))

# def __get_frequency__(commits, frequencies):
#

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

            elif type == CORRELATION_BY_DEV or type == MEANS_BY_COMMITS_FREQUENCY:
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