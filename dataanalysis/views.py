import math

# third-party
import numpy as np
import pandas as pd
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from scipy.stats import spearmanr

from architecture.views import ROUDING_SCALE
from contributions.models import Tag

# OPERATIONS
POPULATION_MEANS = 1
CORRELATION_BY_VERSION = 2
CORRELATION_BY_DEV = 3
DELTAS_TREND = 4
OVERVIEW_BY_DEV = 5
MEANS_BY_COMMITS_FREQUENCY = 6
PROJECT_OVERVIEW = 7
CONTRIBUTIONS_BY_DEV = 8

# POPULATION = "tag"
POPULATION = "author"


# TYPE OF CONTRIBUTIONS
DECAY = 1
IMPROVEMENT = 2

def index(request):

    template = loader.get_template('data_analysis/index.html')

    if request.method == 'POST':
        print("oi")
    

    context = {
        'title': 'Estatística Descritiva',
    }
    return HttpResponse(template.render(context, request))

def descriptive_statistics(request, type):

    if type == DELTAS_TREND:
        commits, metric_by_dev, metric_by_dev_by_comp = __process_metrics__(type,request.commit_db,request)
    else:
        commits, metric_by_dev, metric_by_dev_by_comp = __process_metrics__(type,request.commit_db,request)
    file_name = 'undefined'

    try:
        if type == POPULATION_MEANS:
            if POPULATION == 'tag':
                by_author = False
            else:
                by_author = True

            devs, file_name, population_means_list = __exp_and_degradation_means__(file_name, metric_by_dev, request.commit_db, by_author)

            if by_author:
                my_df = pd.DataFrame(population_means_list, columns=['author', 'x', 'y', 'commits'])
            else:
                my_df = pd.DataFrame(population_means_list, columns=['versao', 'experiencia', 'delta_normalizado'])
            my_df.to_csv(file_name, index=False, header=True)
            if len(devs) > 0:
                my_df = pd.DataFrame(devs, columns=['dev', 'x', 'y', 'commits'])
                my_df.to_csv('dev_media.csv', index=False, header=True)
                file_name += '</strong> e <strong>dev_media.csv'

        elif type == CORRELATION_BY_VERSION:

            correlation_list, file_name = __correlation_version__(file_name, metric_by_dev)

            my_df = pd.DataFrame(correlation_list, columns=['versao', 'r', 'p-value'])
            # writer = pd.ExcelWriter('correlation_version.xlsx')
            # my_df.to_excel(writer, 'Sheet1', index=None, header=True)
            my_df.to_csv(file_name, index=None, header=True)
            # my_df.to_excel(writer, 'Sheet2')
            # writer.save()
            print('Correlation by version')

        elif type == CORRELATION_BY_DEV:

            correlation_list, file_name = __correlation_by_dev__(file_name, metric_by_dev, commits)

            my_df = pd.DataFrame(correlation_list, columns=['dev', 'r', 'p-value', 'r texto'])
            my_df.to_csv(file_name, index=None, header=True)



            correlation_list, file_name = __correlation_by_dev_by_component__(file_name, metric_by_dev_by_comp, commits)

            my_df = pd.DataFrame(correlation_list, columns=['dev', 'r', 'p-value', 'r texto'])
            my_df.to_csv(file_name, index=None, header=True)

            print('Correlation by dev')

        elif type == DELTAS_TREND:
            print('Geração de tendência dos deltas')
            file_name = 'delta_trend.csv'
            delta_list = []
            for tag in metric_by_dev:
                print(tag.description+': '+str(tag.delta_rmd_components))
                delta_list.append([tag.description.replace('rel/',''),metric_by_dev[tag][0],metric_by_dev[tag][1],tag.delta_rmd_components])

            my_df = pd.DataFrame(delta_list, columns=['versao', 'delta', 'delta normalizado','degradacao'])
            my_df.to_csv(file_name, index=False, header=True)
        elif type == CONTRIBUTIONS_BY_DEV:
            print("Piora e melhora da arquitetura por autor")
            file_name1 = 'worsening_contributions_by_author.csv'
            pioram_contributions_list = []
            melhoram_contributions_list = []
            all_commits = request.commit_db.filter(tag_id__in=Tag.line_major_versions(request.session['project']))
            for dev in metric_by_dev:
                loc = sum([x.u_cloc for x in all_commits if x.author == dev])
                if metric_by_dev[dev][0] != 0.0:
                    pioram_contributions_list.append([dev.name, metric_by_dev[dev][0]*ROUDING_SCALE/loc])
                if metric_by_dev[dev][1] != 0.0:
                    melhoram_contributions_list.append([dev.name,metric_by_dev[dev][1]*ROUDING_SCALE/loc])

            my_df = pd.DataFrame(pioram_contributions_list, columns=['autor', 'cum_delta'])
            my_df.index = np.arange(1, len(my_df)+1)
            my_df.to_csv(file_name1, index=True, header=True)

            file_name2 = 'contributions_that_improve_by_author.csv'

            my_df = pd.DataFrame(melhoram_contributions_list, columns=['autor', 'cum_delta'])
            my_df.to_csv(file_name2, index=False, header=True)

            file_name = '(1) '+file_name1+'</strong> e <strong>'+file_name2

        elif type == OVERVIEW_BY_DEV:
            commits_by_dev = []
            file_name = 'overview_by_dev.csv'
            for dev in metric_by_dev:
                commits_by_dev.append([dev.name, request.commit_db.filter(author=dev, tag_id__in=Tag.line_1_10_x()).count(), metric_by_dev[dev]])
            my_df = pd.DataFrame(commits_by_dev, columns=['dev', 'total_commits', 'contributions'])
            my_df.to_csv(file_name, index=None, header=True)
            print('overview by dev')

        elif type == MEANS_BY_COMMITS_FREQUENCY:
            file_name, mean_list = __exp_and_degradation_by_class__(file_name, metric_by_dev)

            my_df = pd.DataFrame(mean_list, columns=['commits', 'experiencia', 'degradacao'])

            print("by_commit_frequency.csv")
        elif type == PROJECT_OVERVIEW:
            stats = []

            # About commits
            file_name1 = 'general_commits_statistics.csv'
            all_commits = request.commit_db.filter(tag_id__in=Tag.line_major_versions(request.session['project']))
            total_commits = all_commits.count()

            relative_impactul_commits = len(commits)/total_commits
            relative_non_impactul_commits = 1 - relative_impactul_commits

            stats.append(['Commits impactantes',relative_impactul_commits])
            stats.append(['Commits nao-impactantes', relative_non_impactul_commits])

            my_df = pd.DataFrame(stats, columns=['legenda','Total de commits'])
            my_df.to_csv(file_name1, index=False, header=True)

            # About authors of commits regards of impactful commits and non-impactful commits
            file_name2 = 'authors_commits_statistics.csv'
            stats = []

            continuaram_a_fazer_commits_apos_um_ano = len(set([x.author for x in all_commits if x.author_seniority > 365]))

            all_impactful_authors = len(set([x.author for x in commits]))
            all_authors = len(set([x.author for x in all_commits]))

            relative_impactful_authors = all_impactful_authors/all_authors
            relative_non_impactful_authors = 1 - relative_impactful_authors

            stats.append(['Impactaram a arquitetura',relative_impactful_authors])
            stats.append(['Nao impactaram a arquitetura', relative_non_impactful_authors])

            my_df = pd.DataFrame(stats, columns=['legenda', 'Total de autores'])
            my_df.to_csv(file_name2, index=False, header=True)


            file_name3 = 'among_impactful_commits_statistics.csv'
            stats = __impactful_commits_statistics__(commits)

            my_df = pd.DataFrame(stats, columns=['legenda', 'Total de commits impactantes'])
            my_df.to_csv(file_name3, index=False, header=True)


            file_name4 = 'improving_commits_statistics.csv'
            stats = __impactful_commits_statistics__(commits,IMPROVEMENT)

            my_df = pd.DataFrame(stats, columns=['legenda', 'Total de commits que melhoram'])
            my_df.to_csv(file_name4, index=False, header=True)

            file_name5 = 'decaying_commits_statistics.csv'
            stats = __impactful_commits_statistics__(commits, DECAY)

            my_df = pd.DataFrame(stats, columns=['legenda', 'Total de commits que degradam'])
            my_df.to_csv(file_name5, index=False, header=True)

            file_name = '(1) ' + file_name1 + '</strong>, <strong> (2) ' + file_name2 + '</strong>, <strong>(3) ' + file_name3 +\
                        '</strong>, <strong>(4) ' + file_name4 + '</strong> e <strong>(5) ' + file_name5
            print("Informações gerais")


        messages.success(request, 'Files successfully created! <br/>File: <strong>'+file_name+'</strong>')
    except Exception as e:
        print(e)
        messages.error(request, 'Could not create file! (<strong>motive:</strong> '+e.args[0]+')')

    return HttpResponseRedirect(reverse('analysis:index', ))


def __impactful_commits_statistics__(commits, type=0):
    stats = []
    # FIXME: If seniority changes to years, fix it:
    if type == DECAY:
        commits = [x for x in commits if x.delta_rmd_components > 0.0]
    elif type == IMPROVEMENT:
        commits = [x for x in commits if x.delta_rmd_components < 0.0]

    by_period = {}
    
    # commits = Commit.objects.filter(tag__id__in=Tag.line_major_versions())

    # FIXME:
    # prev_period = None
    # for period_ in groups:
    #     if prev_period==None:
    #         commits_by_period = len(set([x.id for x in commits if x.author_seniority <= period_.period_factor or x.has_submitted_by]))
    #     else:
    #         commits_by_period = len(set([x.id for x in commits if x.author_seniority > period_.period_factor * prev_period.period and
    #                                      x.author_seniority <= period_.period_factor * period_.period and not x.has_submitted_by]))
    #     commits_by_period /= len(commits)
    #     by_period.setdefault(period_,commits_by_period)
    #     prev_period = period_

    # for period in by_period:
    #     if period[0] == -1:
    #         # Mudei no braco
    #         legenda = 'Autores com > {} {} de projeto'.format(prev_period.period, prev_period.period_alias)
    #         if period[0] == 1:
    #             legenda = 'Autores com > {} {} de projeto'.format(period.period, period.period_alias)
    #     else:
    #         legenda = 'Autores com > {} {} e <= {} {} de projeto'.format(prev_period.period, prev_period.period_alias, period.period, period.period_alias)
    #     prev_period = period
    #     stats.append([legenda,by_period[period]])

    # commits = Commit.objects.filter(tag_id__in=Tag.line_major_versions())


    commits_by_period = len(set([x.id for x in commits if x.author_seniority <= 30 or x.has_submitted_by]))
    commits_by_period /= len(commits)
    stats.append(['Autores com até 1 mês de projeto', commits_by_period])

    commits_by_period = len(set([x.id for x in commits if x.author_seniority > 30 and
                                         x.author_seniority <= 365 and not x.has_submitted_by]))
    commits_by_period /= len(commits)
    stats.append(['Autores com > 1 mês e até 1 ano de projeto', commits_by_period])

    commits_by_period = len(set([x.id for x in commits if x.author_seniority > 365 and
                                 x.author_seniority <= 730 and not x.has_submitted_by]))
    commits_by_period /= len(commits)
    stats.append(['Autores com > 1 ano e até 2 anos de projeto', commits_by_period])

    commits_by_period = len(set([x.id for x in commits if x.author_seniority > 730 and
                                 x.author_seniority <= 1095 and not x.has_submitted_by]))
    commits_by_period /= len(commits)
    stats.append(['Autores com > 2 anos e até 3 anos de projeto', commits_by_period])

    commits_by_period = len(set([x.id for x in commits if x.author_seniority > 1095 and
                                 x.author_seniority <= 1460 and not x.has_submitted_by]))
    commits_by_period /= len(commits)
    stats.append(['Autores com > 3 anos e até 4 anos de projeto', commits_by_period])

    commits_by_period = len(set([x.id for x in commits if x.author_seniority > 1460 and
                                 x.author_seniority <= 1825 and not x.has_submitted_by]))
    commits_by_period /= len(commits)
    stats.append(['Autores com > 4 anos e até 5 anos de projeto', commits_by_period])

    commits_by_period = 1-sum([i[1] for i in stats])
    stats.append(['Autores com mais de 5 anos de projeto', commits_by_period])



    # commits_author_with_1year = len(set([x.id for x in commits if x.is_author_newcomer]))
    # commits_author_with_2years = len(set(
    #     [x.id for x in commits if x.author_seniority > 365 and x.author_seniority <= 730 and not x.has_submitted_by]))
    # commits_author_with_3years = len(set([x.id for x in commits if
    #                                       x.author_seniority > 730 and x.author_seniority <= 1095 and not x.has_submitted_by]))
    # commits_author_with_4years = len(set([x.id for x in commits if
    #                                       x.author_seniority > 1095 and x.author_seniority <= 1460 and not x.has_submitted_by]))
    # # commits_author_more_than_3years = len(set([x.id for x in commits if x.author_seniority > 1095 and not x.has_submitted_by]))
    # relative_with_1year = commits_author_with_1year / len(commits)
    # relative_with_2years = commits_author_with_2years / len(commits)
    # relative_with_3years = commits_author_with_3years / len(commits)
    # relative_with_4years = commits_author_with_4years / len(commits)
    # relative_more_than_4years = 1 - (
    #             relative_with_1year + relative_with_2years + relative_with_3years + relative_with_4years)
    #
    # stats.append(['Autores com <= 1 ano de projeto', relative_with_1year])
    # stats.append(['Autores com > 1 ano e <= 2 anos de projeto', relative_with_2years])
    # stats.append(['Autores com > 2 anos e <= 3 anos de projeto', relative_with_3years])
    # stats.append(['Autores com > 3 anos e <= 4 anos de projeto', relative_with_4years])
    # stats.append(['Autores com > 4 anos de projeto', relative_more_than_4years])
    return stats


def __exp_and_degradation_by_class__(file_name, metric_by_dev,commit_db):
    file_name = 'by_commit_frequency_10x_semOutliers.csv'
    begin__in = 0
    interval = 100
    number_of_frequencies = 7
    a = [str(begin__in + x * interval) for x in range(0, number_of_frequencies)]
    last_key = '>'
    a.append(last_key)
    frequencies = {el: [[], []] for el in a}
    # frequencies = OrderedDict({'100':[[],[]],'200':[[],[]],'300':[[],[]],'400':[[],[]],'500':[[],[]],'600':[[],[]],'700':[[],[]],'> 800':[[],[]]})
    # frequencies = OrderedDict({'5': [[], []], '25': [[], []], '45': [[], []], '65': [[], []], '85': [[], []],
    #                            '105': [[], []], '125': [[], []], '145': [[], []], '165': [[], []], '185': [[], []],
    #                            '225': [[], []], '245': [[], []], last_key: [[], []]})
    deltas = [len(author_exp) for author_exp in metric_by_dev.values()]
    threshold = np.percentile(deltas, 80)
    # Sem Peter Donald, ele mexeu bastante em um componente que pode nao fazer parte do core do software
    # devs = [dev_contributions for dev_contributions in metric_by_dev.keys() if len(metric_by_dev[dev_contributions]) >= threshold and dev_contributions.id != 41]
    devs = [dev_contributions for dev_contributions in metric_by_dev.keys() if
            len(metric_by_dev[dev_contributions]) >= threshold]
    means = []
    # Sem Peter Donald, ele mexeu bastante em um componente que pode nao fazer parte do core do software
    commits = commit_db.exclude(normalized_delta=0).filter(
        tag_id__in=Tag.line_1_10_x())
    # Com todos
    # commits = Commit.objects.exclude(normalized_delta=0).filter(tag_id__in=Tag.line_1_10_x())
    for commit in commits:
        if any(commit.author == c for c in devs):
            find = False

            for freq, exp_degrad_arr in frequencies.items():
                exp_arr = exp_degrad_arr[0]
                degrad_arr = exp_degrad_arr[1]
                if freq.isdigit() and commit.total_commits <= int(freq):
                    # if freq.isdigit() and Commit.objects.filter(author=commit.author, tag_id__in=[2,3,4,5,6,7], id__lt=commit.id).count() <= int(freq):
                    exp_arr.append(commit.author_experience)
                    degrad_arr.append(commit.normalized_delta)
                    find = True
                    break;
            if not find:
                frequencies[last_key][0].append(commit.author_experience)
                frequencies[last_key][1].append(commit.normalized_delta)
    # devs = [[dev_contributions.name, metric_by_dev[dev_contributions][0], metric_by_dev[dev_contributions][1], metric_by_dev[dev_contributions][2]] for
    #         dev_contributions in metric_by_dev.keys() if len(metric_by_dev[dev_contributions]) >= threshold]
    mean_list = []
    for freq, means in frequencies.items():
        mean_list.append([freq, np.mean(means[0]), np.mean(means[1])])
    return file_name, mean_list

def __correlation_by_dev_by_component__(file_name, metric_by_dev, commits):
    file_name = 'correlation_dev_comp.csv'
    correlation_list = []
    for dev in metric_by_dev:
        impactful_commits = 0
        if len(metric_by_dev[dev]) == 0:
            continue
        my_df = pd.DataFrame(metric_by_dev[dev], columns=['x', 'y'])
        r = my_df.corr(method='spearman').values[0][1]
        p = my_df.corr(method=spearmanr_pval).values[0][1]
        if not math.isnan(r) and not math.isnan(p):
            impactful_commits = len(set([x.id for x in commits if x.author == dev]))
            correlation_list.append([dev.name, r, p, str(round(r,4))+(' ('+str(impactful_commits)+')')])
    return correlation_list, file_name


def __correlation_by_dev__(file_name, metric_by_dev, commits):
    file_name = 'correlation_dev.csv'
    correlation_list = []
    for dev in metric_by_dev:
        impactful_commits = 0
        my_df = pd.DataFrame(metric_by_dev[dev], columns=['x', 'y'])
        r = my_df.corr(method='spearman').values[0][1]
        p = my_df.corr(method=spearmanr_pval).values[0][1]
        if not math.isnan(r) and not math.isnan(p):
            impactful_commits = len(set([x.id for x in commits if x.author == dev]))
            correlation_list.append([dev.name, r, p, str(round(r,4))+(' ('+str(impactful_commits)+')')])
    return correlation_list, file_name


def __correlation_version__(file_name, metric_by_dev):
    file_name = 'correlation_version.csv'
    correlation_list = []
    for tag in metric_by_dev:
        my_df = pd.DataFrame(metric_by_dev[tag], columns=['x', 'y'])
        r = my_df.corr(method='spearman').values[0][1]
        p = my_df.corr(method=spearmanr_pval).values[0][1]
        correlation_list.append([tag.description, r,p])
    return correlation_list, file_name


def __exp_and_degradation_means__(file_name, metric_by_dev, commit_db, by_author=True):
    if by_author:
        file_name = 'author_population_means.csv'
    else:
        file_name = 'version_population_means.csv'
    population_means_list = []
    deltas = [len(exp_arr[0]) for exp_arr in metric_by_dev.values()]
    threshold = np.percentile(deltas, 80)
    devs = []

    for key, arrays in metric_by_dev.items():
        exp_arr = arrays[0]
        degrad_arr = arrays[1]
        if by_author:
            population_means_list.append(
                [key.name, np.mean(exp_arr), np.mean(degrad_arr), commit_db.filter(author=key).count()])
            if len(exp_arr) >= threshold:
                devs.append(
                    [key.name, np.mean(exp_arr), np.mean(degrad_arr), commit_db.filter(author=key).count()])
        else:
            population_means_list.append(
                [key.description.replace('rel/',''), np.mean(exp_arr), np.mean(degrad_arr)])
    # else:
    #
    return devs, file_name, population_means_list


def __process_metrics__(type,commit_db,request):
    commits = commit_db.exclude(normalized_delta=0).filter(tag_id__in=Tag.line_major_versions(request.session['project']))
    # commits = [x for x in commits if x.author_experience <= 10000]
    # commits = [x for x in commits if x.author_experience <= 10000 and x.normalized_delta > 0]
    # commits = [x for x in commits if abs(x.delta_rmd_components) < 21.62/(10 ** 7)]
    # values = set(map(lambda x: x.author, commits))
    metric_by_dev = {}
    metric_by_dev_by_comp = {}

    if type == CORRELATION_BY_VERSION:
        metric_by_dev = {key: [[c.author_experience, c.normalized_delta*ROUDING_SCALE] for c in commits if c.tag==key] for key in set([c.tag for c in commits])}
    # elif type == CORRELATION_BY_DEV or type == MEANS_BY_COMMITS_FREQUENCY:
    #     metric_by_dev = {
    #         key: [[c.author_experience, c.normalized_delta * ROUDING_SCALE] for c in commits if c.author == key] for key
    #         in set([c.author for c in commits])}
    # Faz duas listas e depois passa o Sum em cada uma dentro da lista principal
    # elif type == POPULATION_MEANS:
    #     metric_by_dev = {key: [[sum(c.author_experience), sum(c.normalized_delta*ROUDING_SCALE)] for c in commits if c.author==key] for key in set([c.author for c in commits])}
    try:
        for commit in commits:

            if type == POPULATION_MEANS:
                if POPULATION == 'tag':
                    key = commit.tag
                else:
                    key = commit.author

                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, [[], []])
                metric_by_dev[key][0].append(commit.author_experience)
                metric_by_dev[key][1].append(commit.normalized_delta*ROUDING_SCALE)
            elif type == CONTRIBUTIONS_BY_DEV:
                key = commit.author
                if key not in metric_by_dev:
                    # increased, decreased
                    metric_by_dev.setdefault(key, [0.0,0.0])
                if commit.delta_rmd_components > 0.0:
                    metric_by_dev[key][0] += commit.delta_rmd_components
                else:
                    metric_by_dev[key][1] += commit.delta_rmd_components

            elif type == CORRELATION_BY_DEV or type == MEANS_BY_COMMITS_FREQUENCY:
                key = commit.author
                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, [])

                if key not in metric_by_dev_by_comp:
                    metric_by_dev_by_comp.setdefault(key,[])

                for component_degradation in commit.component_commits.all():
                    if component_degradation.delta_rmd != 0:
                        metric_by_dev_by_comp[key].append([component_degradation.author_experience,
                                                   component_degradation.delta_rmd / commit.u_cloc])

                metric_by_dev[key].append([commit.author_experience, commit.normalized_delta])
            elif type == DELTAS_TREND:
                key = commit.tag

                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, [0.0,0.0])
                # delta, delta normalizado
                metric_by_dev[key][0] += commit.delta_rmd_components
                metric_by_dev[key][1] += commit.normalized_delta
                # metric_by_dev[key].append([commit.delta_rmd_components*commit.u_cloc, commit.delta_rmd_components])

            elif type == OVERVIEW_BY_DEV:

                key = commit.author
                if key not in metric_by_dev:
                    metric_by_dev.setdefault(key, 0)
                metric_by_dev[key] += 1

    except Exception as e:
        raise e

    return commits, metric_by_dev, metric_by_dev_by_comp

def spearmanr_pval(x,y):
    return spearmanr(x,y)[1]