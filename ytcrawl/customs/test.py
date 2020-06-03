from preprocessor import Preprocessor
from db_channels_uploader import DBChannelsUploader
from db_videos_uploader import DBVideosUploader
from db_papers_uploader import DBPapersUploader
from db_handler import DBHandler
from sql_handler import SQLHandler

from datetime import datetime
from random import shuffle

import urllib.request
from bs4 import BeautifulSoup
import re

import csv
import numpy as np
import matplotlib.pyplot as plt

from altmetric_it import AltmetricIt

import json
import os


def _check_arxiv_id_exists():
    with open('./test.txt') as fp:
        _dict = json.load(fp)
    _list_citations = _dict['citations']
    _list_i_no_arxiv_id = list()
    for i, _dict_citation in enumerate(_list_citations):
        if 'arxivId' not in _dict_citation:
            _list_i_no_arxiv_id.append(i)
        elif _dict_citation['arxivId'] == None:
            _list_i_no_arxiv_id.append(i)
        else:
            print(_dict_citation['arxivId'])
    print(_list_i_no_arxiv_id)


def _temp():
    db_handler = DBHandler()
    db_handler.sql_handler.select('temp_videos', 'channelId')
    _list_channel_ids = db_handler.execute().fetchall()
    _list_channel_ids = list(
        set(list(map(lambda tup: tup[0], _list_channel_ids))))
    with open('./results/channels/temp_channel_ids.txt', 'w+') as f:
        json.dump(_list_channel_ids, f)


def test_plt(num_cols, max_fig=30):
    db_handler = DBHandler()
    _list_idx_arxiv = [_fname[:-4] for _fname in os.listdir('./stats/videos')]
    shuffle(_list_idx_arxiv)
    _num_fig = 0
    _iter_idx_arxiv = iter(_list_idx_arxiv)

    fig, axes = plt.subplots(max_fig//num_cols + 1, num_cols)

    while _num_fig < max_fig:
        try:
            _idx_arxiv = next(_iter_idx_arxiv)
        except StopIteration:
            print('\tList idx_arxiv exhausted.')
            break

        with open('./stats/videos/%s.txt' % _idx_arxiv, 'r') as f:
            _dict_stats_videos = json.load(f)
        db_handler.sql_handler.select(
            'papers_cs', 'altmetric_id').where('idx_arxiv', _idx_arxiv)

        altmetric_id = db_handler.execute().fetchall()[0][0]
        if altmetric_id == None:
            print('\tAltmetric_id not found.')
            continue

        try:
            f = open('./stats/twitter/%s.txt' % altmetric_id, 'r')
        except FileNotFoundError:
            print('\tTwitter file not found.')
            continue
        else:
            _dict_stats_twitter = json.load(f)

        x_vals = list(set(list(_dict_stats_videos['videos']['videoCount'].keys(
        )) + list(_dict_stats_twitter['twitter']['count_tweets'].keys())))
        x_vals.sort()
        y_vals_videoCount = list()
        # y_vals_explanationCount = list()
        y_vals_tweetCount = list()
        for _key in x_vals:
            val_videoCount = int(_dict_stats_videos['videos']['viewCount'][_key]
                                 ) if _key in _dict_stats_videos['videos']['videoCount'] else 0
            y_vals_videoCount.append(val_videoCount)
            # val_explanationCount = int(_dict_stats_videos['videos']['content'][_key]['paper_explanation']
                                #  ) if _key in _dict_stats_videos['videos']['videoCount'] else 0
            # y_vals_explanationCount.append(val_explanationCount)
            val_tweetCount = int(_dict_stats_twitter['twitter']['count_tweets'][_key]
                                 ) if _key in _dict_stats_twitter['twitter']['count_tweets'] else 0
            y_vals_tweetCount.append(val_tweetCount)

        x_vals = [val[2:] for val in x_vals] # YYYY-MM to YY-MM
        primary_axis = axes[_num_fig // num_cols, _num_fig % num_cols]
        primary_axis.set_title(_idx_arxiv, fontsize=10) # Title: idx_arxiv
        primary_axis.set_ylim([0.1, 100])  # Tweets
        primary_axis.plot(x_vals, y_vals_tweetCount, 'b-')
        primary_axis.set_yscale('log')
        primary_axis.set_xticklabels(labels=x_vals, rotation=90)
        # primary_axis.set_xlabel('Month')
        # primary_axis.set_ylabel('video')
        secondary_axis = primary_axis.twinx()
        secondary_axis.plot(x_vals, y_vals_videoCount, 'g--')
        secondary_axis.set_ylim([0.1, 10000])  # Videos
        secondary_axis.set_yscale('log')

        _num_fig += 1
    plt.subplots_adjust(wspace=0.4, hspace=1)
    # plt.tight_layout(pad=0, w_pad=0.1, h_pad=0)
    # plt.xticks(rotation='vertical')
    plt.show()


if __name__ == '__main__':
    # _temp()
    test_plt(num_cols=6, max_fig=20)
    # sql_handler = SQLHandler()

    # with open('table.csv', newline='') as f:
    # table = csv.reader(f)
    # print(list(table))

    # table = np.genfromtxt('table.csv', delimiter=',')
    # table = np.round(table, 2)
    # print(table)

    # fig, ax = plt.subplots()

    # intersection_matrix = table

    # ax.matshow(intersection_matrix, cmap=plt.cm.Reds)

    # cols = ['#contents', 'Duration', '#View',
    #         '#Like', '#Dislike', '#Comment']
    # x_pos = np.arange(len(cols))
    # plt.xticks(x_pos, cols)
    # y_pos = np.arange(len(cols))
    # plt.yticks(y_pos, cols)

    # for i in range(len(cols)):
    #     for j in range(len(cols)):
    #         c = intersection_matrix[j, i]
    #         ax.text(i, j, str(c), va='center', ha='center')

    # plt.show()

    # db_papers_uploader = DBPapersUploader()

    # a = 'http://arxiv.org/pdf/1503.01445.pdf'
    # print(db_papers_uploader.url_http_to_https(a))

    # regex_http = re.compile(r'^https://')
    # print(bool(regex_http.match(a)))

    # regex = re.compile(r'https?://arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf|https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
    # a = 'http://arxiv.org/pdf/1503.01445.pdf'

    # print(bool(regex.match(a)))
    #     results = regex.findall("""
    #     Machine learning provides us an incredible set of tools. If you have a difficult problem at hand, you don't need to hand craft an algorithm for it. It finds out by itself what is important about the problem and tries to solve it on its own. In this video, you'll see a number of incredible applications of different machine learning techniques (neural networks, deep learning, convolutional neural networks and more).

    # Note: the fluid simulation paper is using regression forests, which is a machine learning technique, but not strictly deep learning. There are variants of it that are though (e.g., Deep Neural Decision Forests).
    # ________________________

    # The paper "Toxicity Prediction using Deep Learning" and "Prediction of human population responses to toxic compounds by a collaborative competition" are available here:
    # http://arxiv.org/pdf/1503.01445.pdf
    # http://www.nature.com/nbt/journal/v33/n9/full/nbt.3299.html

    # The paper "A Comparison of Algorithms and Humans For Mitosis Detection" is available here:
    # http://people.idsia.ch/~juergen/deeplearningwinsMICCAIgrandchallenge.html
    # http://people.idsia.ch/~ciresan/data/isbi2014.pdf

    # Kaggle-related things:
    # http://kaggle.com
    # https://www.kaggle.com/c/dato-native
    # http://blog.kaggle.com/2015/12/03/dato-winners-interview-1st-place-mad-professors/

    # The paper "Deep AutoRegressive Networks" is available here:
    # http://arxiv.org/abs/1310.8499v2
    # https://www.youtube.com/watch?v=-yX1SYeDHbg&feature=youtu.be&t=2976

    # The furniture completion paper, "Data-driven Structural Priors for Shape Completion" is available here:
    # http://cs.stanford.edu/~mhsung/projects/structure-completion

    # Data-driven fluid simulations using regression forests:
    # https://graphics.ethz.ch/~sobarbar/papers/Lad15/DatadrivenFluids.mov
    # https://www.inf.ethz.ch/personal/ladickyl/fluid_sigasia15.pdf

    # Selfies and convolutional neural networks:
    # http://karpathy.github.io/2015/10/25/selfie/

    # Multiagent Cooperation and Competition with Deep Reinforcement Learning:
    # http://arxiv.org/pdf/1511.08779.pdf
    # https://www.youtube.com/watch?v=Gb9DprIgdGw&index=2&list=PLfLv_F3r0TwyaZPe50OOUx8tRf0HwdR_u
    # https://github.com/NeuroCSUT/DeepMind-Atari-Deep-Q-Learner-2Player

    # Kaggle automatic essay scoring contest:
    # https://www.kaggle.com/c/asap-aes
    # http://www.vikparuchuri.com/blog/on-the-automated-scoring-of-essays/

    # Great talks on Kaggle:
    # https://www.youtube.com/watch?v=9Zag7uhjdYo
    # https://www.youtube.com/watch?v=OKOlO9nIHUE
    # https://www.youtube.com/watch?v=R9QxucPzicQ

    # The thumbnail image was created by Barn Images - https://flic.kr/p/xxBc94

    # Subscribe if you would like to see more of these! - http://www.youtube.com/subscription_center?add_user=keeroyz

    # Splash screen/thumbnail design: Felcia Fehr - http://felicia.hu

    # Kroly Zsolnai-Fehr's links:
    # Patreon  https://www.patreon.com/TwoMinutePapers
    # Facebook  https://www.facebook.com/TwoMinutePapers/
    # Twitter  https://twitter.com/karoly_zsolnai
    # Web  https://cg.tuwien.ac.at/~zsolnai/
    #     """)
    #     print(results)

    # subheader = soup.find('div', {'class': 'subheader'})
    # subheader = subheader.find('h1').find(text=True)
    # vals = str(subheader).split(' > ')
    # cols = ['subject_1', 'subject_2', 'subject_3']
    # d = dict(zip(cols, vals))
    # print(d)

    # html = urllib.request.urlopen("https://arxiv.org/abs/1810.04805")
    # soup = BeautifulSoup(html, 'html.parser')

    # abstract = soup.find('blockquote', {'class': 'abstract'})
    # abstract = abstract.find_all(text=True)
    # abstract = [text for text in abstract if text not in ('\n', 'Abstract:')]
    # # Remove \n
    # abstract = map(lambda text: text.replace('\n', ' '), abstract)
    # abstract = '\n'.join(abstract)
    # print(abstract)

    # div_authors = soup.find('div', {'class': 'authors'})
    # div_authors = div_authors.find_all(text=True)
    # div_authors = [author for author in div_authors if author not in ('Authors:', ', ')]
    # div_authors = ', '.join(div_authors)
    # print(div_authors)

    # div_dateline = soup.find('div', {'class': 'dateline'})
    # print(div_dateline)
    # print(type(div_dateline))
    # regex_date = re.compile(r'\d{1,2} \w{3} \d{4}')
    # published_date = regex_date.findall(str(div_dateline))[0]
    # published_date = '02 Oct 2019'
    # print(datetime.strptime(published_date, '%d %b %Y').strftime('%Y-%m-%d'))
