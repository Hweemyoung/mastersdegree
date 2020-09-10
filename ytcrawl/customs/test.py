from preprocessor import Preprocessor
from db_channels_uploader import DBChannelsUploader
from db_videos_uploader import DBVideosUploader
from db_papers_uploader import DBPapersUploader
from db_handler import DBHandler
from sql_handler import SQLHandler

from datetime import datetime, date
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
import statistics

import pandas as pd


def scopus_csv():
    fpath = "scopus.csv"
    data = pd.read_csv(fpath)
    list_doi = list(data["DOI"])


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
    print('# of video stats files:', len(_list_idx_arxiv))
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
            # 'papers_cs', 'altmetric_id').where('idx_arxiv', _idx_arxiv)
            'papers_cs', 'altmetric_id').where('idx_arxiv', _idx_arxiv).where('subject_1', 'Computer Science', '=').where('subject_2', 'Machine Learning', '=')

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

        x_vals = [val[2:] for val in x_vals]  # YYYY-MM to YY-MM
        primary_axis = axes[_num_fig // num_cols, _num_fig % num_cols]
        primary_axis.set_title(_idx_arxiv, fontsize=10)  # Title: idx_arxiv
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


def interval_from_paper():
    regex_idx_arxiv = re.compile(r'\d{3,5}.\d{3,5}')
    _list_content = ['paper_explanation', 'paper_reference', 'paper_supplementary',
                     'news', 'paper_application', 'dialogue', 'routine', 'paper_assessment']
    _dict_xlim = {'timedelta': [-30, 500],
                  'duration': [0, 150], 'viewCount': [1, 2000]}

    # dict_attr_by_content
    _dict_td_by_content = dict()
    _dict_viewCount_by_content = dict()
    _dict_duration_by_content = dict()

    _list_cols = ['duration', 'viewCount', 'content', 'q', 'publishedAt']
    db_handler = DBHandler()
    db_handler.sql_handler.select('videos_cs.LG', _list_cols)
    _videos_LG = db_handler.execute().fetchall()
    for _row in _videos_LG:
        _dict_video = dict(zip(_list_cols, _row))
        _idx_arxiv = regex_idx_arxiv.findall(_dict_video['q'])[0]
        db_handler.sql_handler.select(
            'papers_cs', 'publishedAt').where('idx_arxiv', _idx_arxiv)
        _d_paper = db_handler.execute().fetchall()[0][0]
        if _d_paper == None:
            continue

        if _dict_video['content'] not in _dict_td_by_content:
            _dict_td_by_content[_dict_video['content']] = list()
            _dict_viewCount_by_content[_dict_video['content']] = list()
            _dict_duration_by_content[_dict_video['content']] = list()

        # viewCount
        # Filter by viewCount?
        # if int(_dict_video['viewCount']) < 500:
            # continue
        _dict_viewCount_by_content[_dict_video['content']].append(
            int(_dict_video['viewCount']))

        # timedelta
        _days_td = (_dict_video['publishedAt'].date() - _d_paper).days
        # Filter by timedelta?
        # if _days_td < 180:
        # continue
        _dict_td_by_content[_dict_video['content']].append(_days_td)

        # duration
        _dict_duration_by_content[_dict_video['content']].append(
            int(_dict_video['duration']) / 60)

    _dict_stats_by_content = dict()
    for _content in _dict_td_by_content:
        _dict_stats_by_content[_content] = dict()
        # timedelta
        _dict_stats_by_content = _add_stats(
            _dict_stats_by_content, _dict_td_by_content, 'timedelta', filter_outliers=True)
        # viewCount
        _dict_stats_by_content = _add_stats(
            _dict_stats_by_content, _dict_viewCount_by_content, 'viewCount', filter_outliers=True)
        # duration
        _dict_stats_by_content = _add_stats(
            _dict_stats_by_content, _dict_duration_by_content, 'duration', filter_outliers=True)
        # N
        _dict_stats_by_content[_content]['n'] = len(
            _dict_td_by_content[_content])

    # print('Dict stats:\n', _dict_stats_by_content)
    for _content in _dict_stats_by_content:
        print('duration for', _content,
              _dict_stats_by_content[_content]['duration'])
        print('viewCount for', _content,
              _dict_stats_by_content[_content]['viewCount'])
        print('timedelta for', _content,
              _dict_stats_by_content[_content]['timedelta'])

    _dict_by_attr = dict()
    _dict_by_attr['timedelta'] = _dict_td_by_content
    _dict_by_attr['viewCount'] = _dict_viewCount_by_content
    _dict_by_attr['duration'] = _dict_duration_by_content

    # Histogram
    fig, axes = plt.subplots(3, 8)
    for _i, _attr in enumerate(_dict_by_attr):
        # for _j, _content in enumerate(_list_content):
        for _j, _content in enumerate(_list_content):
            primary_axis = axes[_i, _j]
            if _i == 0:
                primary_axis.set_title('%s(N=%d)' % (_content, len(
                    _dict_by_attr[_attr][_content]) if _content in _dict_by_attr[_attr] else 0), fontsize=10)  # paper_explanation
            if _j == 0:
                primary_axis.set_ylabel(_attr, fontsize=10)  # duration
            # Remove outliers
            # reject_outliers(np.array(_dict_by_attr[_attr][_content]), m=3.0)
            if _content in _dict_by_attr[_attr]:
                print('attr:', _attr, 'content:', _content)
                print(_dict_by_attr[_attr][_content])
                primary_axis.hist(_dict_by_attr[_attr][_content], bins=10)
            else:
                primary_axis.hist([])
            primary_axis.set_ylim([0, 20])
            # primary_axis.set_xlim(_dict_xlim[_attr])
            # if _attr == 'viewCount':
            # primary_axis.set_xscale('log')

            # primary_axis.plot(x_vals, y_vals_tweetCount, 'b-')
            # primary_axis.set_yscale('log')
            # primary_axis.set_xticklabels(labels=x_vals, rotation=90)

            # primary_axis.set_xlabel('Month')
            # primary_axis.set_ylabel('video')

            # secondary_axis = primary_axis.twinx()
            # secondary_axis.plot(x_vals, y_vals_videoCount, 'g--')
            # secondary_axis.set_ylim([0.1, 10000])  # Videos
            # secondary_axis.set_yscale('log')
    plt.show()


def reject_outliers(data, m=3.):
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else 0.
    return data[s < m]


def _add_stats(dict_stats_by_content, dict_attr_by_content, attribute='timedelta', filter_outliers=True):
    for _content in dict_stats_by_content:
        dict_stats_by_content[_content][attribute] = dict()

        if filter_outliers:
            dict_attr_by_content[_content] = reject_outliers(
                np.sort(np.array(dict_attr_by_content[_content])), m=8.0)
            dict_attr_by_content[_content] = dict_attr_by_content[_content].flatten(
            )

        dict_stats_by_content[_content][attribute]['n'] = len(
            dict_attr_by_content[_content])
        try:
            _mean = statistics.mean(dict_attr_by_content[_content])
        except:
            dict_stats_by_content[_content][attribute]['mean'] = None
        else:
            dict_stats_by_content[_content][attribute]['mean'] = round(
                _mean, 1)
        try:
            _std = statistics.stdev(dict_attr_by_content[_content])
        except:
            dict_stats_by_content[_content][attribute]['std'] = None
        else:
            dict_stats_by_content[_content][attribute]['std'] = round(
                _std, 2)
    return dict_stats_by_content


def filter_by_q():
    db_handler = DBHandler()
    db_handler.sql_handler.select(
        "scopus_videos", ["title", "description", "q", "idx"])
    _results = db_handler.execute().fetchall()
    num_delete = 0
    for _row in _results:
        _new_q = list()
        _list_q = _row[2].split(", ")
        for _q in _list_q:
            if _q.lower() not in _row[0].lower() and _q not in _row[1].lower():
                continue
            _new_q.append(_q)

        if _new_q:
            _new_q = ", ".join(_new_q)
            db_handler.sql_handler.update(
                "scopus_videos", dict_columns_values={"q": _new_q})
            db_handler.execute()
        else:
            db_handler.sql_handler.delete(
                "scopus_videos").where("idx", _row[3])
            db_handler.execute()
            num_delete += 1

    print("# delete: %d" % num_delete)


def cal_paper_video_interval(fp_csv):
    from datetime import datetime, date
    data = pd.read_csv(fp_csv, header=0)

    list_date_videos = list(map(lambda field: datetime.strptime(
        field, "%Y-%m-%d %H:%M:%S").date(), data["publishedAt"]))
    list_date_papers = list(map(lambda field: datetime.strptime(
        field, "%Y-%m-%d").date(), data["paper_published"]))
    list_days_interval = list()
    for date_video, date_paper in zip(list_date_videos, list_date_papers):
        date_interval = date_video - date_paper
        list_days_interval.append(date_interval.days/365)
    print(list_days_interval)
    list_video_ids = data["videoId"]
    return list_days_interval, list_video_ids


def boxplot(list_days_interval, list_video_ids):
    import pandas as pd
    import numpy as np
    df2 = pd.DataFrame(zip(list_days_interval, list_video_ids),
                       columns=["days", "videoId"])
    df2.sort_values(by=["days"])
    print(df2)
    xs = np.array(list_days_interval)
    print("Mean: %f\tMedian: %f\tStdev: %f" %
          (np.average(xs), np.median(xs), np.std(xs)))
    df = pd.DataFrame(xs, columns=["Age(Years)"])
    plt.figure(figsize=(7, 6))  # 크기 지정
    boxplot = df.boxplot(column=['Age(Years)'])
    # plt.yticks(np.arange(0, 101, step=5))
    plt.show()


def str_2_value(value):
    return None if value == None else int(value)


def heatmap_from_csv(df, title=None, col_names=["duration", "viewCount", "likeCount", "dislikeCount", "commentCount"], col_labels=['Duration', '#View', '#Like', '#Dislike', '#Comment']):
    from scipy import stats

    if col_labels == None:
        col_labels = col_names
    # Values must be already calculated on csv.
    corr_pearson, p_pearson = np.zeros((len(col_names),len(col_names))), np.zeros((len(col_names),len(col_names)))
    for _i, _col_i in enumerate(col_names):
        for _j, _col_j in enumerate(col_names):
            corr_pearson[_i][_j], p_pearson[_i][_j] = stats.pearsonr(df[_col_i], df[_col_j])

    # with open(fpath, newline='') as f:
    #     table = list(csv.reader(f))
    # print(table)

    # print(intersection_matrix)
    corr_pearson = np.round(corr_pearson, 2)
    p_pearson = np.round(p_pearson, 2)


    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5, 9))

    ax1.matshow(corr_pearson, cmap=plt.cm.coolwarm, vmin=-1.0, vmax=1.0)
    ax2.matshow(p_pearson, cmap=plt.cm.coolwarm, vmin=-1.0, vmax=1.0)

    # x_pos = np.arange(len(col_labels))
    ax1.set_xticklabels([''] + col_labels, fontsize=8)
    ax2.set_xticklabels([''] + col_labels, fontsize=8)
    # y_pos = np.arange(len(col_labels))
    ax1.set_yticklabels([''] + col_labels, fontsize=8)
    ax2.set_yticklabels([''] + col_labels, fontsize=8)

    ax1.set_title("Pearson Corr.")
    ax2.set_title("P-value")

    for _i in range(len(col_labels)):
        for _j in range(len(col_labels)):
            ax1.text(_i, _j, str(corr_pearson[_j, _i]), va='center', ha='center')
            ax2.text(_i, _j, str(p_pearson[_j, _i]), va='center', ha='center')

    if title != None:
        fig.suptitle(title)
    # plt.clim(-1, 1)
    plt.show()

def _200730():
    db_handler = DBHandler()
    _list_fields = [
    "idx",
    "idx_paper",
    "content",
    "video_visual",
    "publishedAt",
    "duration",
    "channelId",
    "viewCount",
    "likeCount",
    "dislikeCount",
    "commentCount",
    "favoriteCount",
    "liveStreaming"
    ]
    _list_videos = list()
    
    # 2014 comp
    db_handler.sql_handler.select(
    "scopus_videos_2014_comp",
    _list_fields
    # )
    ).where("viewCount", 1000, ">")
    # ).where("idx", 135, "<").where("content", ["paper_explanation", "paper_reference"], "in")
    # ).where("idx", 135, "<")
    # ).where("idx", 135, "<").where("content", "paper_supplementary")
    _list_videos += db_handler.execute().fetchall()
    
    # 2014 life
    db_handler.sql_handler.select(
    "scopus_videos_2014_life",
    _list_fields
    # )
    ).where("viewCount", 1000, ">")
    _list_videos += db_handler.execute().fetchall()

    _list_dict_videos = list(
    map(lambda _row: dict(zip(_list_fields, _row)), _list_videos))

    # Channels : Get subscriber count
    db_handler.sql_handler.select(
    "channels",
    ["idx", "channelId", "subscriberCount"]
    )
    _list_channels = db_handler.execute().fetchall()
    # {channelId : tuple(...), ...}
    _dict_channels = dict(
    zip(list(map(lambda _row: _row[1], _list_channels)), _list_channels))

    # Hashmap
    dict_content_key = dict()
    dict_content_key["paper_explanation"] = "paper_explanation"
    dict_content_key["paper_reference"] = "paper_reference"
    dict_content_key["paper_linked_supplementary"] = "paper_supplementary"
    dict_content_key["paper_supplementary"] = "paper_supplementary"
    dict_content_key["paper_application"] = "paper_assessment"
    dict_content_key["paper_assessment"] = "paper_assessment"
    dict_content_key["news"] = "news"
    dict_x = dict()
    dict_x["paper_explanation"] = list()
    dict_x["paper_reference"] = list()
    dict_x["paper_supplementary"] = list()
    dict_x["paper_assessment"] = list()
    dict_x["news"] = list()
    dict_y = dict()
    dict_y["paper_explanation"] = list()
    dict_y["paper_reference"] = list()
    dict_y["paper_supplementary"] = list()
    dict_y["paper_assessment"] = list()
    dict_y["news"] = list()

    df1 = pd.read_csv("scopus/scopus_math+comp_top5perc_1401-1406.csv", header=0)
    df2 = pd.read_csv("scopus/scopus_life+earch_top60_1401-1406.csv", header=0)
    df = pd.concat([df1, df2])

    for _i, _dict_row in enumerate(_list_dict_videos):
        print("[+]Processing %d of %d videos" % (_i+1, len(_list_dict_videos)))
        # Calc age
        _date_video = _dict_row["publishedAt"].date()
        _scopus_row = df[df["DOI"] == _dict_row["idx_paper"]]
        if len(_scopus_row) > 1:
            _scopus_row = _scopus_row.iloc[0]
        _date_paper = date(_scopus_row["Year"], _scopus_row["Month"], 1)
        _age = (_date_video - _date_paper).days/365
        _dict_row["age"] = _age

        # Age - Scaled View
        # Calc view/subscriber
        # _dict_row["scaled_view"] = _dict_row["viewCount"] / _dict_channels[_dict_row["channelId"]][2] if _dict_channels[_dict_row["channelId"]][2] != 0 else _dict_row["viewCount"]
        # _dict_row["scaled_view"] = np.log10(_dict_row["viewCount"] / _dict_channels[_dict_row["channelId"]][2]) if _dict_channels[_dict_row["channelId"]][2] != 0 else np.log10(_dict_row["viewCount"])
        # dict_y[dict_content_key[_dict_row["content"]]].append(_dict_row["scaled_view"])

        # Age - Scaled Like
        # Calc like/subscriber
        # _dict_row["scaled_like"] = _dict_row["likeCount"] / _dict_channels[_dict_row["channelId"]
        #                                                                    ][2] if _dict_channels[_dict_row["channelId"]][2] != 0 else _dict_row["likeCount"]
        # dict_y[dict_content_key[_dict_row["content"]]].append(
        #     _dict_row["scaled_like"])

        # Age - View
        # dict_y[dict_content_key[_dict_row["content"]]].append(_dict_row["viewCount"])
        # dict_y[dict_content_key[_dict_row["content"]]].append(np.log10(_dict_row["viewCount"]))

        # Age - Like
        # dict_y[dict_content_key[_dict_row["content"]]].append(
        #     _dict_row["likeCount"])

        # Boxplot: like/dislike
        # if _dict_row["likeCount"] in (None, 0) or _dict_row["dislikeCount"] == None:
        #     continue
        # _dict_row["r_like_dislike"] = _dict_row["likeCount"] / _dict_row["dislikeCount"] if _dict_row["dislikeCount"] != 0 else _dict_row["likeCount"]
        # dict_y[dict_content_key[_dict_row["content"]]].append(_dict_row["r_like_dislike"])

        # Add x
        dict_x[dict_content_key[_dict_row["content"]]].append(_dict_row["age"])

    # Boxplot
    # Multiple box plots on one Axes
    # fig, ax = plt.subplots()
    # ax.boxplot(list(dict_y.values()), sym="b*")
    # ax.set_yscale("log")
    # plt.title('Excluding: count unavailable or like == 0')
    # list_xticks = list()
    # for _key in dict_y.keys():
    #     list_xticks.append("%s\n(N=%d)"%(_key, len(dict_y[_key])))
    # plt.xticks([1, 2, 3, 4],
    #            list_xticks)
    # plt.show()

    # Scatter
    plt.figure(figsize=(8, 5))

    exp = plt.scatter(x=dict_x["paper_explanation"],
                y=dict_y["paper_explanation"], s=12, marker="o", color="blue")
    ref = plt.scatter(x=dict_x["paper_reference"],
                y=dict_y["paper_reference"], s=12, marker="x", color="black")
    sup = plt.scatter(x=dict_x["paper_supplementary"],
                y=dict_y["paper_supplementary"], s=12, marker="o", color="green")
    ass = plt.scatter(x=dict_x["paper_assessment"],
                y=dict_y["paper_assessment"], s=12, marker="o", color="red")
    news = plt.scatter(x=dict_x["news"],
                y=dict_y["news"], s=12, marker="o", color="lightblue")

    plt.legend((ref, sup, news, exp, ass),
        (
            "paper_reference(N=%d)" % len(dict_y["paper_reference"]),
            "paper_supplementary(N=%d)" % len(dict_y["paper_supplementary"]),
            "news(N=%d)" % len(dict_y["news"]),
            "paper_explanation(N=%d)" % len(dict_y["paper_explanation"]),
            "paper_assessment(N=%d)" % len(dict_y["paper_assessment"]),
        ),
        scatterpoints=1,
        loc='upper right',
        fontsize=8)

    # xs = dict_x["paper_explanation"] + dict_x["paper_reference"] + \
    #     dict_x["paper_supplementary"] + dict_x["paper_assessment"]
    # ys = dict_y["paper_explanation"] + dict_y["paper_reference"] + \
    #     dict_y["paper_supplementary"] + dict_y["paper_assessment"]
    # cs = ["blue"] * len(dict_y["paper_explanation"]) + ["black"] * len(dict_y["paper_reference"]) + \
    #     ["green"] * len(dict_y["paper_supplementary"]) + \
    #     ["red"] * len(dict_y["paper_assessment"])
    # plt.scatter(x=xs, y=ys, s=10, c=cs)

    plt.title("Video metrics (2014 comp + life)")
    plt.xlabel("Video - Publication Timedelta (years)")
    plt.ylabel("log10(View / Subscribers)")
    # plt.yscale("log")
    # plt.ylim(1, 100000)
    plt.show()

def _200805():
    import pandas as pd
    import numpy as np

    data_raw1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_videos_2014_comp.csv", header=0)
    data_raw2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_videos_2019_comp.csv", header=0)
    data_raw = pd.concat([data_raw1, data_raw2], sort=False)

    # Dropna
    print(data_raw.columns[16:21])
    data_dropna = data_raw.dropna(subset=data_raw.columns[16:21])
    # print(len(data_dropna), len(data_raw))
    # data_dropna[data_raw.columns[16:21]].isnull().any()

    # Select ~3 quartiles by viewCount
    q3_viewcount = data_raw["viewCount"].quantile(q=0.25)
    data_filtered = data_dropna[data_dropna["viewCount"] > q3_viewcount]
    # data_filtered = data_dropna[data_dropna["viewCount"] > 1000]
    print("Q3: %.1f\t# data_filtered: %d\t # data_raw: %d" % (q3_viewcount, len(data_filtered), len(data_raw)))

    # comp explanation/assessment/application
    # data_filtered_hq = data_filtered[data_filtered["content"].isin(["paper_explanation", "paper_assessment", "paper_application"])]
    # print("# data HQ: %d\t# data_filtered: %d" % (len(data_filtered_hq), len(data_filtered)))

    # Logarithm
    # Drop dislike == 0 | comment == 0
    data_nonzero = data_filtered[~(data_filtered[data_filtered.columns[19:21]].T == 0.0).any()]
    # Log
    data_nonzero[data_nonzero.columns[16:21]] = np.log(data_nonzero[data_nonzero.columns[16:21]])
    # print(data_nonzero[data_nonzero.columns[16:21]])

    # data_nonzero = data_filtered[~(data_filtered[data_filtered.columns[18:20]].T == 0.0).any()]
    # data_nonzero[data_nonzero.columns[16:20]] = np.log10(data_nonzero[data_nonzero.columns[16:20]])
    # print(data_nonzero[data_nonzero.columns[16:20]])
    print("# data_nonzero: %d\t# data_filtered: %d" % (len(data_nonzero), len(data_filtered)))

    # heatmap_from_csv(data_filtered, title="2014+2019 COMP all(N=%d)" % len(data_filtered))
    # heatmap_from_csv(data_filtered_hq, title="2014+2019 COMP HQ(N=%d)" % len(data_filtered_hq))
    heatmap_from_csv(data_nonzero, title="2014+2019 COMP all(log) (N=%d)" % len(data_nonzero), col_labels=["log(Duration)", "log(View)", "log(Like)", "log(Dislike)", "log(Comment)"])

def parse_fetches(fetches):
    _new_fetches = list()
    for _fetch in fetches:
        for _doi in _fetch[0].split(", "):
            _new_fetches.append(
                (_doi, _fetch[1])
            )
    return _new_fetches

def get_dois_with_videos_within_days_from_publish(df, table_name, where=None, days_from=None, days_until=None):
#     複数の動画が与えられる論文の場合、複数のsetに含まれることがある。
    from db_handler import DBHandler
    from datetime import timedelta
    db_handler = DBHandler()
    _set_target_dois = set()
    db_handler.sql_handler.select(table_name, ["idx_paper", "publishedAt"])
    if type(where) == tuple:
        db_handler.sql_handler.where(*where)
    fetches = db_handler.execute().fetchall()
    fetches = parse_fetches(fetches)
    
    for _row in fetches:
#         print("DOI:", _row[0])
        _target_paper = df[df["DOI"] == _row[0]]
#         if len(_target_paper) == 0:
#             continue
        if len(_target_paper) > 1:
            _target_paper = _target_paper.iloc[0]
#         print(_target_paper)
        _dt_publish = datetime(_target_paper["Year"], _target_paper["Month"], 1)
        
        if days_from != None:
            _dt_video_from = _dt_publish + timedelta(days=days_from)
            if _row[1] < _dt_video_from:
                continue
        
        if days_until != None:
            _dt_video_until = _dt_publish + timedelta(days=days_until)
            if _row[1] > _dt_video_until:
                continue
        
        _set_target_dois.add(_row[0])
    
#     if days_until == None:
#         _set_target_dois = set(map(lambda _row: _row[0], fetches))
#     else:
#         for _row in fetches:
#             _target_paper = df[df["DOI"] == _row[0]]
#             if len(_target_paper) > 1:
#                 _target_paper = _target_paper.iloc[0]
#             _dt_publish = datetime(_target_paper["Year"], _target_paper["Month"], 1)
            
#             _dt_video_from = _dt_publish + timedelta(days=days_from)
#             _dt_video_until = _dt_publish + timedelta(days=days_until)
            
#             if _row[1] < _dt_video_deadline:
#                 _set_target_dois.add(_row[0])
    
    return _set_target_dois

def _200819():
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange

    df1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1901-1906.csv")
    df2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1701-1706.csv")
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1401-1406.csv")
    print("Raw:", len(df1), len(df2), len(df3))
    df1 = df1.drop_duplicates(subset=["DOI"])
    df2 = df2.drop_duplicates(subset=["DOI"])
    df3 = df3.drop_duplicates(subset=["DOI"])
    print("Duplicates droped:", len(df1), len(df2), len(df3))

    db_handler = DBHandler()
    db_handler.sql_handler.select("scopus_videos_2014_comp", ["idx_paper", "publishedAt"])
    _videos_2014 = db_handler.execute().fetchall()
    db_handler.sql_handler.select("scopus_videos_2017_comp", ["idx_paper", "publishedAt"])
    _videos_2017 = db_handler.execute().fetchall()
    db_handler.sql_handler.select("scopus_videos_2019_comp", ["idx_paper", "publishedAt"])
    _videos_2019 = db_handler.execute().fetchall()

    _idx_papers_2019 = get_dois_with_videos_within_days_from_publish(df1, "scopus_videos_2019_comp")
    _idx_papers_2019_90 = get_dois_with_videos_within_days_from_publish(df1, "scopus_videos_2019_comp", None, None, 90)
    # print(len(_idx_papers_2019), len(_idx_papers_2019_90))
    _idx_papers_2017 = get_dois_with_videos_within_days_from_publish(df2, "scopus_videos_2017_comp")
    _idx_papers_2017_90 = get_dois_with_videos_within_days_from_publish(df2, "scopus_videos_2017_comp", None, None, 90)
    # print(len(_idx_papers_2017), len(_idx_papers_2017_90))
    _idx_papers_2014 = get_dois_with_videos_within_days_from_publish(df3, "scopus_videos_2014_comp")
    _idx_papers_2014_90 = get_dois_with_videos_within_days_from_publish(df3, "scopus_videos_2014_comp", None, None, 90)
    # print(len(_idx_papers_2014), len(_idx_papers_2014_90))

    # Citation
    print("Citation - all")
    _2019_wo_videos_cit = np.log10(df1[~df1.DOI.isin(_idx_papers_2019)]["Cited by"].dropna().astype(int))
    _2019_w_videos_cit = np.log10(df1[df1.DOI.isin(_idx_papers_2019)]["Cited by"].dropna().astype(int))
    _2017_wo_videos_cit = np.log10(df2[~df2.DOI.isin(_idx_papers_2017)]["Cited by"].dropna().astype(int))
    _2017_w_videos_cit = np.log10(df2[df2.DOI.isin(_idx_papers_2017)]["Cited by"].dropna().astype(int))
    _2014_wo_videos_cit = np.log10(df3[~df3.DOI.isin(_idx_papers_2014)]["Cited by"].dropna().astype(int))
    _2014_w_videos_cit = np.log10(df3[df3.DOI.isin(_idx_papers_2014)]["Cited by"].dropna().astype(int))

    plt.figure(figsize=(10, 6))
    plt.title("Citation")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel("log10(Citation)")
    plt.boxplot([
        _2019_wo_videos_cit,
        _2019_w_videos_cit,
        _2017_wo_videos_cit,
        _2017_w_videos_cit,
        _2014_wo_videos_cit,
        _2014_w_videos_cit
    ],
        labels=[
            "2019 w/o videos\n(N=%s)"%len(_2019_wo_videos_cit),
            "2019 w/ videos\n(N=%s)"%len(_2019_w_videos_cit),
            "2017 w/o videos\n(N=%s)"%len(_2017_wo_videos_cit),
            "2017 w/ videos\n(N=%s)"%len(_2017_w_videos_cit),
            "2014 w/o videos\n(N=%s)"%len(_2014_wo_videos_cit),
            "2014 w/ videos\n(N=%s)"%len(_2014_w_videos_cit)
        ]
    )
    plt.show()

    _s2019, _p2019 = stats.ttest_ind(
        _2019_wo_videos_cit,
        _2019_w_videos_cit
    )
    print("2019\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2019_wo_videos_cit), np.mean(_2019_w_videos_cit), _s2019, _p2019))

    _s2017, _p2017 = stats.ttest_ind(
        _2017_wo_videos_cit,
        _2017_w_videos_cit
    )
    print("2017\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2017_wo_videos_cit), np.mean(_2017_w_videos_cit), _s2017, _p2017))

    _s2014, _p2014 = stats.ttest_ind(
        _2014_wo_videos_cit,
        _2014_w_videos_cit
    )
    print("2014\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2014_wo_videos_cit), np.mean(_2014_w_videos_cit), _s2014, _p2014))

    # AAS
    print("AAS - all")
    _2019_wo_videos_aas = np.log10(df1[~df1.DOI.isin(_idx_papers_2019)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2019_w_videos_aas = np.log10(df1[df1.DOI.isin(_idx_papers_2019)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2017_wo_videos_aas = np.log10(df2[~df2.DOI.isin(_idx_papers_2017)][df2["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2017_w_videos_aas = np.log10(df2[df2.DOI.isin(_idx_papers_2017)][df2["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_wo_videos_aas = np.log10(df3[~df3.DOI.isin(_idx_papers_2014)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_w_videos_aas = np.log10(df3[df3.DOI.isin(_idx_papers_2014)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))

    plt.figure(figsize=(10, 6))
    plt.title("AAS")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel("log10(AAS)")
    plt.boxplot([
        _2019_wo_videos_aas,
        _2019_w_videos_aas,
        _2017_wo_videos_aas,
        _2017_w_videos_aas,
        _2014_wo_videos_aas,
        _2014_w_videos_aas
    ],
        labels=[
            "2019 w/o videos\n(N=%s)"%len(_2019_wo_videos_aas),
            "2019 w/ videos\n(N=%s)"%len(_2019_w_videos_aas),
            "2017 w/o videos\n(N=%s)"%len(_2017_wo_videos_aas),
            "2017 w/ videos\n(N=%s)"%len(_2017_w_videos_aas),
            "2014 w/o videos\n(N=%s)"%len(_2014_wo_videos_aas),
            "2014 w/ videos\n(N=%s)"%len(_2014_w_videos_aas)
        ]
    )
    
    plt.show()

    _s2019, _p2019 = stats.ttest_ind(
        _2019_wo_videos_aas,
        _2019_w_videos_aas
    )
    print("2019\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2019_wo_videos_aas), np.mean(_2019_w_videos_aas), _s2019, _p2019))

    _s2017, _p2017 = stats.ttest_ind(
        _2017_wo_videos_aas,
        _2017_w_videos_aas
    )
    print("2017\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2017_wo_videos_aas), np.mean(_2017_w_videos_aas), _s2017, _p2017))

    _s2014, _p2014 = stats.ttest_ind(
        _2014_wo_videos_aas,
        _2014_w_videos_aas
    )
    print("2014\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2014_wo_videos_aas), np.mean(_2014_w_videos_aas), _s2014, _p2014))

    print("Citation - 90")
    _2019_90_wo_videos_cit = np.log10(df1[~df1.DOI.isin(_idx_papers_2019_90)]["Cited by"].dropna().astype(int))
    _2019_90_w_videos_cit = np.log10(df1[df1.DOI.isin(_idx_papers_2019_90)]["Cited by"].dropna().astype(int))
    _2017_90_wo_videos_cit = np.log10(df2[~df2.DOI.isin(_idx_papers_2017_90)]["Cited by"].dropna().astype(int))
    _2017_90_w_videos_cit = np.log10(df2[df2.DOI.isin(_idx_papers_2017_90)]["Cited by"].dropna().astype(int))
    _2014_90_wo_videos_cit = np.log10(df3[~df3.DOI.isin(_idx_papers_2014_90)]["Cited by"].dropna().astype(int))
    _2014_90_w_videos_cit = np.log10(df3[df3.DOI.isin(_idx_papers_2014_90)]["Cited by"].dropna().astype(int))

    plt.figure(figsize=(10, 6))
    plt.title("Citation-90")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel("log10(citation)")
    plt.boxplot([
        _2019_90_wo_videos_cit,
        _2019_90_w_videos_cit,
        _2017_90_wo_videos_cit,
        _2017_90_w_videos_cit,
        _2014_90_wo_videos_cit,
        _2014_90_w_videos_cit
    ],
        labels=[
            "2019 w/o videos-90\n(N=%s)"%len(_2019_90_wo_videos_cit),
            "2019 w/ videos-90\n(N=%s)"%len(_2019_90_w_videos_cit),
            "2017 w/o videos-90\n(N=%s)"%len(_2017_90_wo_videos_cit),
            "2017 w/ videos-90\n(N=%s)"%len(_2017_90_w_videos_cit),
            "2014 w/o videos-90\n(N=%s)"%len(_2014_90_wo_videos_cit),
            "2014 w/ videos-90\n(N=%s)"%len(_2014_90_w_videos_cit)
        ]
    )

    _s2019, _p2019 = stats.ttest_ind(
        _2019_90_wo_videos_cit,
        _2019_90_w_videos_cit
    )
    print("2019\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2019_90_wo_videos_cit), np.mean(_2019_90_w_videos_cit), _s2019, _p2019))

    _s2017, _p2017 = stats.ttest_ind(
        _2017_90_wo_videos_cit,
        _2017_90_w_videos_cit
    )
    print("2017\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2017_90_wo_videos_cit), np.mean(_2017_90_w_videos_cit), _s2017, _p2017))

    _s2014, _p2014 = stats.ttest_ind(
        _2014_90_wo_videos_cit,
        _2014_90_w_videos_cit
    )
    print("2014\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2014_90_wo_videos_cit), np.mean(_2014_90_w_videos_cit), _s2014, _p2014))

    plt.show()

    print("AAS - 90")
    _2019_90_wo_videos_aas = np.log10(df1[~df1.DOI.isin(_idx_papers_2019_90)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2019_90_w_videos_aas = np.log10(df1[df1.DOI.isin(_idx_papers_2019_90)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2017_90_wo_videos_aas = np.log10(df2[~df2.DOI.isin(_idx_papers_2017_90)][df2["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2017_90_w_videos_aas = np.log10(df2[df2.DOI.isin(_idx_papers_2017_90)][df2["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_90_wo_videos_aas = np.log10(df3[~df3.DOI.isin(_idx_papers_2014_90)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_90_w_videos_aas = np.log10(df3[df3.DOI.isin(_idx_papers_2014_90)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))

    plt.figure(figsize=(10, 6))
    plt.title("AAS-90")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel("log10(AAS)")
    plt.boxplot([
        _2019_90_wo_videos_aas,
        _2019_90_w_videos_aas,
        _2017_90_wo_videos_aas,
        _2017_90_w_videos_aas,
        _2014_90_wo_videos_aas,
        _2014_90_w_videos_aas
    ],
        labels=[
            "2019 w/o videos-90\n(N=%s)"%len(_2019_90_wo_videos_aas),
            "2019 w/ videos-90\n(N=%s)"%len(_2019_90_w_videos_aas),
            "2017 w/o videos-90\n(N=%s)"%len(_2017_90_wo_videos_aas),
            "2017 w/ videos-90\n(N=%s)"%len(_2017_90_w_videos_aas),
            "2014 w/o videos-90\n(N=%s)"%len(_2014_90_wo_videos_aas),
            "2014 w/ videos-90\n(N=%s)"%len(_2014_90_w_videos_aas)
        ]
    )

    plt.show()

    _s2019, _p2019 = stats.ttest_ind(
        _2019_90_wo_videos_aas,
        _2019_90_w_videos_aas
    )
    print("2019\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2019_90_wo_videos_aas), np.mean(_2019_90_w_videos_aas), _s2019, _p2019))

    _s2017, _p2017 = stats.ttest_ind(
        _2017_90_wo_videos_aas,
        _2017_90_w_videos_aas
    )
    print("2017\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2017_90_wo_videos_aas), np.mean(_2017_90_w_videos_aas), _s2017, _p2017))

    _s2014, _p2014 = stats.ttest_ind(
        _2014_90_wo_videos_aas,
        _2014_90_w_videos_aas
    )
    print("2014\tMean: %.1f/%.1f\tS = %f\tp = %f" % (
        np.mean(_2014_90_wo_videos_aas), np.mean(_2014_90_w_videos_aas), _s2014, _p2014))
    
def _200904():
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange

    df1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1901-1906.csv")
    df2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1701-1706.csv")
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1401-1406.csv")

    db_handler = DBHandler()
    db_handler.sql_handler.select("scopus_videos_2014_comp", ["idx_paper", "publishedAt"])
    _videos_2014 = db_handler.execute().fetchall()
    db_handler.sql_handler.select("scopus_videos_2014_comp", ["idx_paper", "publishedAt"]).where("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
    _videos_2014_exp = db_handler.execute().fetchall()
    db_handler.sql_handler.select("scopus_videos_2017_comp", ["idx_paper", "publishedAt"])
    # _videos_2017 = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2017_comp", ["idx_paper", "publishedAt"]).where("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
    # _videos_2017_exp = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2019_comp", ["idx_paper", "publishedAt"])
    _videos_2019 = db_handler.execute().fetchall()
    db_handler.sql_handler.select("scopus_videos_2019_comp", ["idx_paper", "publishedAt"]).where("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
    _videos_2019_exp = db_handler.execute().fetchall()

    _idx_papers_2019 = get_dois_with_videos_within_days_from_publish(df1, "scopus_videos_2019_comp")
    _idx_papers_2019_exp = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_comp",
                                                                        ("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
                                                                        )
    _idx_papers_2019_news = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_comp",
                                                                        ("content", "news")
                                                                        )
    _idx_papers_2019_sup = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_comp",
                                                                        ("content", ["paper_linked_supplementary", "paper_supplementary"], "in")
                                                                        )
    _idx_papers_2019_ref = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_comp",
                                                                        ("content", "paper_reference")
                                                                        )
    _idx_papers_2014 = get_dois_with_videos_within_days_from_publish(df3, "scopus_videos_2014_comp")
    _idx_papers_2014_exp = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_comp",
                                                                        ("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
                                                                        )
    _idx_papers_2014_news = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_comp",
                                                                        ("content", "news")
                                                                        )
    _idx_papers_2014_sup = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_comp",
                                                                        ("content", ["paper_linked_supplementary", "paper_supplementary"], "in")
                                                                        )
    _idx_papers_2014_ref = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_comp",
                                                                        ("content", "paper_reference")
                                                                        )

    print(len(_idx_papers_2019),
        len(_idx_papers_2019_exp),
        len(_idx_papers_2019_news),
        len(_idx_papers_2019_sup),
        len(_idx_papers_2019_ref),
        len(_idx_papers_2014),
        len(_idx_papers_2014_exp),
        len(_idx_papers_2014_news),
        len(_idx_papers_2014_sup),
        len(_idx_papers_2014_ref)
    )
    print(
        "2019 ratio of papers w/ videos: %.2f\n2014 ratio of papers w/ videos: %.2f" % (100 * len(_idx_papers_2019) / len(df1), 100 * len(_idx_papers_2014) / len(df3))
    )

    # print(
    #     len(_videos_2014),
    #     len(_videos_2014_exp),
    #     len(_videos_2017),
    #     len(_videos_2017_exp),
    #     len(_videos_2019),
    #     len(_videos_2019_exp)
    # )

    # Citation
    _2019_wo_videos_cit = np.log10(df1[~df1.DOI.isin(_idx_papers_2019)][df1["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2019_w_videos_cit_exp = np.log10(df1[df1.DOI.isin(_idx_papers_2019_exp)][df1["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2019_w_videos_cit_news = np.log10(df1[df1.DOI.isin(_idx_papers_2019_news)][df1["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2019_w_videos_cit_sup = np.log10(df1[df1.DOI.isin(_idx_papers_2019_sup)][df1["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2019_w_videos_cit_ref = np.log10(df1[df1.DOI.isin(_idx_papers_2019_ref)][df1["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2014_wo_videos_cit = np.log10(df3[~df3.DOI.isin(_idx_papers_2014)][df3["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2014_w_videos_cit_exp = np.log10(df3[df3.DOI.isin(_idx_papers_2014_exp)][df3["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2014_w_videos_cit_news = np.log10(df3[df3.DOI.isin(_idx_papers_2014_news)][df3["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2014_w_videos_cit_sup = np.log10(df3[df3.DOI.isin(_idx_papers_2014_sup)][df3["Cited by"] != "None"]["Cited by"].dropna().astype(int))
    _2014_w_videos_cit_ref = np.log10(df3[df3.DOI.isin(_idx_papers_2014_ref)][df3["Cited by"] != "None"]["Cited by"].dropna().astype(int))

    plt.figure(figsize=(16, 6))
    plt.title("Citation")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel("log10(Citation)")
    plt.boxplot([
        _2019_wo_videos_cit,
        _2019_w_videos_cit_exp,
        _2019_w_videos_cit_news,
        _2019_w_videos_cit_sup,
        _2019_w_videos_cit_ref,
        _2014_wo_videos_cit,
        _2014_w_videos_cit_exp,
        _2014_w_videos_cit_news,
        _2014_w_videos_cit_sup,
        _2014_w_videos_cit_ref
    ],
        labels=[
            "2019 w/o videos\n(N=%s)"%len(_2019_wo_videos_cit),
            "2019 w/ exp\n(N=%s)"%len(_2019_w_videos_cit_exp),
            "2019 w/ news\n(N=%s)"%len(_2019_w_videos_cit_news),
            "2019 w/ sup\n(N=%s)"%len(_2019_w_videos_cit_sup),
            "2019 w/ ref\n(N=%s)"%len(_2019_w_videos_cit_ref),
            "2014 w/o videos\n(N=%s)"%len(_2014_wo_videos_cit),
            "2014 w/ exp\n(N=%s)"%len(_2014_w_videos_cit_exp),
            "2014 w/ news\n(N=%s)"%len(_2014_w_videos_cit_news),
            "2014 w/ sup\n(N=%s)"%len(_2014_w_videos_cit_sup),
            "2014 w/ ref\n(N=%s)"%len(_2014_w_videos_cit_ref),
        ]
    )

    print("2019\tMean: %.1f"%np.mean(_2019_wo_videos_cit))
    _s2019_exp, _p2019_exp = stats.ttest_ind(
        _2019_wo_videos_cit,
        _2019_w_videos_cit_exp
    )
    print("2019 exp\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_cit_exp), _s2019_exp, _p2019_exp))
    _s2019_news, _p2019_news = stats.ttest_ind(
        _2019_wo_videos_cit,
        _2019_w_videos_cit_news
    )
    print("2019 news\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_cit_news), _s2019_news, _p2019_news))
    _s2019_sup, _p2019_sup = stats.ttest_ind(
        _2019_wo_videos_cit,
        _2019_w_videos_cit_sup
    )
    print("2019 sup\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_cit_sup), _s2019_sup, _p2019_sup))
    _s2019_ref, _p2019_ref = stats.ttest_ind(
        _2019_wo_videos_cit,
        _2019_w_videos_cit_ref
    )
    print("2019 ref\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_cit_ref), _s2019_ref, _p2019_ref))
    _s2014_exp, _p2014_exp = stats.ttest_ind(
        _2014_wo_videos_cit,
        _2014_w_videos_cit_exp
    )
    print("2014\tMean: %.1f"%np.mean(_2014_wo_videos_cit))
    print("2014 exp\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_cit_exp), _s2014_exp, _p2014_exp))
    _s2014_news, _p2014_news = stats.ttest_ind(
        _2014_wo_videos_cit,
        _2014_w_videos_cit_news
    )
    print("2014 news\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_cit_news), _s2014_news, _p2014_news))
    _s2014_sup, _p2014_sup = stats.ttest_ind(
        _2014_wo_videos_cit,
        _2014_w_videos_cit_sup
    )
    print("2014 sup\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_cit_sup), _s2014_sup, _p2014_sup))
    _s2014_ref, _p2014_ref = stats.ttest_ind(
        _2014_wo_videos_cit,
        _2014_w_videos_cit_ref
    )
    print("2014 ref\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_cit_ref), _s2014_ref, _p2014_ref))

    plt.show()

    # AAS
    _2019_wo_videos_aas = np.log10(df1[~df1.DOI.isin(_idx_papers_2019)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2019_w_videos_aas_exp = np.log10(df1[df1.DOI.isin(_idx_papers_2019_exp)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2019_w_videos_aas_news = np.log10(df1[df1.DOI.isin(_idx_papers_2019_news)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2019_w_videos_aas_sup = np.log10(df1[df1.DOI.isin(_idx_papers_2019_sup)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2019_w_videos_aas_ref = np.log10(df1[df1.DOI.isin(_idx_papers_2019_ref)][df1["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_wo_videos_aas = np.log10(df3[~df3.DOI.isin(_idx_papers_2014)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_w_videos_aas_exp = np.log10(df3[df3.DOI.isin(_idx_papers_2014_exp)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_w_videos_aas_news = np.log10(df3[df3.DOI.isin(_idx_papers_2014_news)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_w_videos_aas_sup = np.log10(df3[df3.DOI.isin(_idx_papers_2014_sup)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    _2014_w_videos_aas_ref = np.log10(df3[df3.DOI.isin(_idx_papers_2014_ref)][df3["AAS"] != "None"]["AAS"].dropna().astype(int))
    # _2014_w_videos_aas_ref = np.log10(df3[df3.DOI.isin(_idx_papers_2014_ref) and df3["AAS"] != "None"]["AAS"].dropna().astype(int))

    plt.figure(figsize=(16, 6))
    plt.title("AAS")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel("log10(AAS)")
    plt.boxplot([
        _2019_wo_videos_aas,
        _2019_w_videos_aas_exp,
        _2019_w_videos_aas_news,
        _2019_w_videos_aas_sup,
        _2019_w_videos_aas_ref,
        _2014_wo_videos_aas,
        _2014_w_videos_aas_exp,
        _2014_w_videos_aas_news,
        _2014_w_videos_aas_sup,
        _2014_w_videos_aas_ref
    ],
        labels=[
            "2019 w/o videos\n(N=%s)"%len(_2019_wo_videos_aas),
            "2019 w/ exp\n(N=%s)"%len(_2019_w_videos_aas_exp),
            "2019 w/ news\n(N=%s)"%len(_2019_w_videos_aas_news),
            "2019 w/ sup\n(N=%s)"%len(_2019_w_videos_aas_sup),
            "2019 w/ ref\n(N=%s)"%len(_2019_w_videos_aas_ref),
            "2014 w/o videos\n(N=%s)"%len(_2014_wo_videos_aas),
            "2014 w/ exp\n(N=%s)"%len(_2014_w_videos_aas_exp),
            "2014 w/ news\n(N=%s)"%len(_2014_w_videos_aas_news),
            "2014 w/ sup\n(N=%s)"%len(_2014_w_videos_aas_sup),
            "2014 w/ ref\n(N=%s)"%len(_2014_w_videos_aas_ref),
        ]
    )

    print("2019\tMean: %.1f"%np.mean(_2019_wo_videos_aas))
    print("2019\tMean: %.1f"%np.mean(_2019_wo_videos_aas))
    _s2019_exp, _p2019_exp = stats.ttest_ind(
        _2019_wo_videos_aas,
        _2019_w_videos_aas_exp
    )
    print("2019 exp\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_aas_exp), _s2019_exp, _p2019_exp))
    _s2019_news, _p2019_news = stats.ttest_ind(
        _2019_wo_videos_aas,
        _2019_w_videos_aas_news
    )
    print("2019 news\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_aas_news), _s2019_news, _p2019_news))
    _s2019_sup, _p2019_sup = stats.ttest_ind(
        _2019_wo_videos_aas,
        _2019_w_videos_aas_sup
    )
    print("2019 sup\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_aas_sup), _s2019_sup, _p2019_sup))
    _s2019_ref, _p2019_ref = stats.ttest_ind(
        _2019_wo_videos_aas,
        _2019_w_videos_aas_ref
    )
    print("2019 ref\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2019_w_videos_aas_ref), _s2019_ref, _p2019_ref))
    _s2014_exp, _p2014_exp = stats.ttest_ind(
        _2014_wo_videos_aas,
        _2014_w_videos_aas_exp
    )
    print("2014\tMean: %.1f"%np.mean(_2014_wo_videos_aas))
    print("2014 exp\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_aas_exp), _s2014_exp, _p2014_exp))
    _s2014_news, _p2014_news = stats.ttest_ind(
        _2014_wo_videos_aas,
        _2014_w_videos_aas_news
    )
    print("2014 news\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_aas_news), _s2014_news, _p2014_news))
    _s2014_sup, _p2014_sup = stats.ttest_ind(
        _2014_wo_videos_aas,
        _2014_w_videos_aas_sup
    )
    print("2014 sup\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_aas_sup), _s2014_sup, _p2014_sup))
    _s2014_ref, _p2014_ref = stats.ttest_ind(
        _2014_wo_videos_aas,
        _2014_w_videos_aas_ref
    )
    print("2014 ref\tMean: %.1f\tS = %.4f\tp = %.4f"%(np.mean(_2014_w_videos_cit_ref), _s2014_ref, _p2014_ref))

    plt.show()

if __name__ == '__main__':
    # 200904
    _200904()
    
    # 200819
    # _200819()
    
    # 200805
    # _200805()

    # 200729

    # db_handler.sql_handler.select("channels", [
    #                               "idx", "commentCount", "subscriberCount", "videoCount", "viewCount"])
    # _list_scopus_videos = db_handler.execute().fetchall()
    # for _row in _list_scopus_videos:
    #     db_handler.sql_handler.update("channels", dict_columns_values={
    #         "commentInt": str_2_value(_row[1]),
    #         "subscriberInt": str_2_value(_row[2]),
    #         "videoInt": str_2_value(_row[3]),
    #         "viewInt": str_2_value(_row[4])
    #         }).where("idx", _row[0])
    #     db_handler.execute()

    # db_handler.sql_handler.select("scopus_videos", ["idx", "duration"])
    # _list_scopus_videos = db_handler.execute().fetchall()
    # for _row in _list_scopus_videos:
    #     db_handler.sql_handler.update("scopus_videos", dict_columns_values={
    #         "durationInt": str_2_value(_row[1])}).where("idx", _row[0])
    #     db_handler.execute()

    # db_handler.sql_handler.update("scopus_videos", dict_columns_values={
    #     "likeInt": "2"
    # }).where("idx", 1)
    # db_handler.execute()

    # 200720
    # list_days_interval, list_video_ids = cal_paper_video_interval(
    #     "scopus/scopus_videos_200720_1630.csv")
    # boxplot(list_days_interval, list_video_ids)

    # 200719
    # filter_by_q()

    # _temp()
    # test_plt(num_cols=6, max_fig=20)
    # interval_from_paper()
    # sql_handler = SQLHandler()

    # heatmap_from_csv("table.csv")

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
