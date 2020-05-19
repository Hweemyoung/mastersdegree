from preprocessor import Preprocessor
from db_channels_uploader import DBChannelsUploader
from db_videos_uploader import DBVideosUploader
from db_papers_uploader import DBPapersUploader
from sql_handler import SQLHandler

from datetime import datetime

import urllib.request
from bs4 import BeautifulSoup
import re

import csv
import numpy as np
import matplotlib.pyplot as plt

from altmetric_it import AltmetricIt

import json

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

with open('./test.txt') as fp:
    _dict = json.load(fp)
_dict['citations'][5316]
    
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
