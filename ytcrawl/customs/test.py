# from preprocessor import Preprocessor
# from db_channels_uploader import DBChannelsUploader
# from db_videos_uploader import DBVideosUploader
# from db_papers_uploader import DBPapersUploader
# from db_handler import DBHandler
# from sql_handler import SQLHandler

# from datetime import datetime, date
# from random import shuffle

# import urllib.request
# from bs4 import BeautifulSoup
# import re

# import csv
# import numpy as np
# import matplotlib.pyplot as plt

# from altmetric_it import AltmetricIt

# import json
# import os
# import statistics

# import pandas as pd


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
    # dict_content_key = dict()
    # dict_content_key["paper_explanation"] = "paper_explanation"
    # dict_content_key["paper_reference"] = "paper_reference"
    # dict_content_key["paper_linked_supplementary"] = "paper_supplementary"
    # dict_content_key["paper_supplementary"] = "paper_supplementary"
    # dict_content_key["paper_application"] = "paper_assessment"
    # dict_content_key["paper_assessment"] = "paper_assessment"
    # dict_content_key["news"] = "news"
    # dict_x = dict()
    # dict_x["paper_explanation"] = list()
    # dict_x["paper_reference"] = list()
    # dict_x["paper_supplementary"] = list()
    # dict_x["paper_assessment"] = list()
    # dict_x["news"] = list()
    # dict_y = dict()
    # dict_y["paper_explanation"] = list()
    # dict_y["paper_reference"] = list()
    # dict_y["paper_supplementary"] = list()
    # dict_y["paper_assessment"] = list()
    # dict_y["news"] = list()

    dict_content_key = dict()
    dict_content_key["creative"] = "creative"
    dict_content_key["presentation"] = "presentation"
    dict_content_key["raw"] = "raw"
    dict_content_key["fixed"] = "fixed"
    dict_x = dict()
    dict_x["creative"] = list()
    dict_x["presentation"] = list()
    dict_x["raw"] = list()
    dict_x["fixed"] = list()
    dict_y = dict()
    dict_y["creative"] = list()
    dict_y["presentation"] = list()
    dict_y["raw"] = list()
    dict_y["fixed"] = list()

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

    # exp = plt.scatter(x=dict_x["paper_explanation"],
    #             y=dict_y["paper_explanation"], s=12, marker="o", color="blue")
    # ref = plt.scatter(x=dict_x["paper_reference"],
    #             y=dict_y["paper_reference"], s=12, marker="x", color="black")
    # sup = plt.scatter(x=dict_x["paper_supplementary"],
    #             y=dict_y["paper_supplementary"], s=12, marker="o", color="green")
    # ass = plt.scatter(x=dict_x["paper_assessment"],
    #             y=dict_y["paper_assessment"], s=12, marker="o", color="red")
    # news = plt.scatter(x=dict_x["news"],
    #             y=dict_y["news"], s=12, marker="o", color="lightblue")

    # plt.legend((ref, sup, news, exp, ass),
    #     (
    #         "paper_reference(N=%d)" % len(dict_y["paper_reference"]),
    #         "paper_supplementary(N=%d)" % len(dict_y["paper_supplementary"]),
    #         "news(N=%d)" % len(dict_y["news"]),
    #         "paper_explanation(N=%d)" % len(dict_y["paper_explanation"]),
    #         "paper_assessment(N=%d)" % len(dict_y["paper_assessment"]),
    #     ),
    #     scatterpoints=1,
    #     loc='upper right',
    #     fontsize=8)

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
    from datetime import datetime, timedelta
    db_handler = DBHandler()
    _set_target_dois = set()
    db_handler.sql_handler.select(table_name, ["idx_paper", "publishedAt"])
    if type(where) == tuple:
        db_handler.sql_handler.where(*where)
    elif type(where) == list:
        for _where in where:
            if type(_where) == tuple:
                db_handler.sql_handler.where(*_where)
    fetches = db_handler.execute().fetchall()
    fetches = parse_fetches(fetches)
    
    for _row in fetches:
#         print("DOI:", _row[0])
        _target_paper = df[df["DOI"] == _row[0]]
#         if len(_target_paper) == 0:
#             continue
        if len(_target_paper) > 1:
            _target_paper = _target_paper.iloc[0]
        elif len(_target_paper) == 0:  # Could be filtered before the method
            continue
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

    df1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_life+earch_top60_1901-1906.csv")
    # df2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1701-1706.csv")
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_life+earch_top60_1401-1406.csv")

    db_handler = DBHandler()
    # db_handler.sql_handler.select("scopus_videos_2014_life", ["idx_paper", "publishedAt"])
    # _videos_2014 = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2014_life", ["idx_paper", "publishedAt"]).where("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
    # _videos_2014_exp = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2017_life", ["idx_paper", "publishedAt"])
    # _videos_2017 = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2017_life", ["idx_paper", "publishedAt"]).where("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
    # _videos_2017_exp = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2019_life", ["idx_paper", "publishedAt"])
    # _videos_2019 = db_handler.execute().fetchall()
    # db_handler.sql_handler.select("scopus_videos_2019_life", ["idx_paper", "publishedAt"]).where("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
    # _videos_2019_exp = db_handler.execute().fetchall()

    _list_2019_life = [2, 3, 6, 10, 12, 17, 18, 38, 43, 50, 55, 56, 59, 67, 72, 73, 78, 86, 88, 90, 93, 94, 101, 108, 109, 110, 113, 116, 120, 122, 124, 128, 129, 130, 139, 140, 142, 145, 150, 153, 158, 159, 161, 163, 165, 166, 171, 175, 178, 181, 184, 190, 195, 199, 208, 209, 214, 217, 222, 223, 230, 232, 233, 238, 246, 247, 254, 256, 258, 264, 267, 270, 271, 275, 277, 281, 284, 286, 291, 292, 297, 298, 299, 300, 303, 305, 310, 311, 314, 316, 317, 318, 324, 326, 327, 330, 333, 334, 340, 343]
    _idx_papers_2019 = get_dois_with_videos_within_days_from_publish(df1, "scopus_videos_2019_life", ("idx", _list_2019_life, "in"))
    _idx_papers_2019_exp = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_life",
                                                                        [("idx", _list_2019_life, "in"),
                                                                        ("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
                                                                        ]
                                                                        )
    _idx_papers_2019_news = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_life",
                                                                        [("idx", _list_2019_life, "in"),
                                                                        ("content", "news")
                                                                        ]
                                                                        )
    _idx_papers_2019_sup = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_life",
                                                                        [("idx", _list_2019_life, "in"),
                                                                        ("content", ["paper_linked_supplementary", "paper_supplementary"], "in")
                                                                        ]
                                                                        )
    _idx_papers_2019_ref = get_dois_with_videos_within_days_from_publish(df1,
                                                                        "scopus_videos_2019_life",
                                                                        [("idx", _list_2019_life, "in"),
                                                                        ("content", "paper_reference")
                                                                        ]
                                                                        )
    _idx_papers_2014 = get_dois_with_videos_within_days_from_publish(df3, "scopus_videos_2014_life")
    _idx_papers_2014_exp = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_life",
                                                                        ("content", ["paper_explanation", "paper_assessment", "paper_application"], "in")
                                                                        )
    _idx_papers_2014_news = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_life",
                                                                        ("content", "news")
                                                                        )
    _idx_papers_2014_sup = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_life",
                                                                        ("content", ["paper_linked_supplementary", "paper_supplementary"], "in")
                                                                        )
    _idx_papers_2014_ref = get_dois_with_videos_within_days_from_publish(df3,
                                                                        "scopus_videos_2014_life",
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

def _200914():
    # Reference를 스타일별로 플롯
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
    ).where("viewCount", 1000, ">").where("content", "paper_reference")
    _list_videos += db_handler.execute().fetchall()
    
    # 2014 life
    db_handler.sql_handler.select(
    "scopus_videos_2014_life",
    _list_fields
    ).where("viewCount", 1000, ">").where("content", "paper_reference")
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
    dict_content_key["creative"] = "creative"
    dict_content_key["presentation"] = "presentation"
    dict_content_key["raw"] = "raw"
    dict_content_key["fixed"] = "fixed"
    dict_x = dict()
    dict_x["creative"] = list()
    dict_x["presentation"] = list()
    dict_x["raw"] = list()
    dict_x["fixed"] = list()
    dict_y = dict()
    dict_y["creative"] = list()
    dict_y["presentation"] = list()
    dict_y["raw"] = list()
    dict_y["fixed"] = list()

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
        _dict_row["scaled_view"] = _dict_row["viewCount"] / _dict_channels[_dict_row["channelId"]][2] if _dict_channels[_dict_row["channelId"]][2] != 0 else _dict_row["viewCount"]
        _dict_row["scaled_view"] = np.log10(_dict_row["viewCount"] / _dict_channels[_dict_row["channelId"]][2]) if _dict_channels[_dict_row["channelId"]][2] != 0 else np.log10(_dict_row["viewCount"])
        dict_y[dict_content_key[_dict_row["video_visual"]]].append(_dict_row["scaled_view"])

        # Age - Scaled Like
        # Calc like/subscriber
        # _dict_row["scaled_like"] = _dict_row["likeCount"] / _dict_channels[_dict_row["channelId"]
        #                                                                    ][2] if _dict_channels[_dict_row["channelId"]][2] != 0 else _dict_row["likeCount"]
        # dict_y[dict_content_key[_dict_row["video_visual"]]]].append(
        #     _dict_row["scaled_like"])

        # Age - View
        # dict_y[dict_content_key[_dict_row["video_visual"]]]].append(_dict_row["viewCount"])
        # dict_y[dict_content_key[_dict_row["video_visual"]]]].append(np.log10(_dict_row["viewCount"]))

        # Age - Like
        # dict_y[dict_content_key[_dict_row["video_visual"]]]].append(
        #     _dict_row["likeCount"])

        # Boxplot: like/dislike
        # if _dict_row["likeCount"] in (None, 0) or _dict_row["dislikeCount"] == None:
        #     continue
        # _dict_row["r_like_dislike"] = _dict_row["likeCount"] / _dict_row["dislikeCount"] if _dict_row["dislikeCount"] != 0 else _dict_row["likeCount"]
        # dict_y[dict_content_key[_dict_row["video_visual"]]]].append(_dict_row["r_like_dislike"])

        # Add x
        dict_x[dict_content_key[_dict_row["video_visual"]]].append(_dict_row["age"])

    # Scatter
    plt.figure(figsize=(8, 5))

    # exp = plt.scatter(x=dict_x["paper_explanation"],
    #             y=dict_y["paper_explanation"], s=12, marker="o", color="blue")
    # ref = plt.scatter(x=dict_x["paper_reference"],
    #             y=dict_y["paper_reference"], s=12, marker="x", color="black")
    # sup = plt.scatter(x=dict_x["paper_supplementary"],
    #             y=dict_y["paper_supplementary"], s=12, marker="o", color="green")
    # ass = plt.scatter(x=dict_x["paper_assessment"],
    #             y=dict_y["paper_assessment"], s=12, marker="o", color="red")
    # news = plt.scatter(x=dict_x["news"],
    #             y=dict_y["news"], s=12, marker="o", color="lightblue")

    # plt.legend((ref, sup, news, exp, ass),
    #     (
    #         "paper_reference(N=%d)" % len(dict_y["paper_reference"]),
    #         "paper_supplementary(N=%d)" % len(dict_y["paper_supplementary"]),
    #         "news(N=%d)" % len(dict_y["news"]),
    #         "paper_explanation(N=%d)" % len(dict_y["paper_explanation"]),
    #         "paper_assessment(N=%d)" % len(dict_y["paper_assessment"]),
    #     ),
    #     scatterpoints=1,
    #     loc='upper right',
    #     fontsize=8)

    cre = plt.scatter(x=dict_x["creative"],
                y=dict_y["creative"], s=12, marker="o", color="blue")
    pre = plt.scatter(x=dict_x["presentation"],
                y=dict_y["presentation"], s=12, marker="x", color="black")
    raw = plt.scatter(x=dict_x["raw"],
                y=dict_y["raw"], s=12, marker="o", color="green")
    fix = plt.scatter(x=dict_x["fixed"],
                y=dict_y["fixed"], s=12, marker="o", color="red")

    plt.legend((cre, pre, raw, fix),
        (
            "creative(N=%d)" % len(dict_y["creative"]),
            "presentation(N=%d)" % len(dict_y["presentation"]),
            "raw(N=%d)" % len(dict_y["raw"]),
            "fixed(N=%d)" % len(dict_y["fixed"]),
        ),
        scatterpoints=1,
        loc='upper right',
        fontsize=8,
        framealpha=0.3)

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
    

def _200918():
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange
    from scopus_handler import ScopusHandler

    df1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1901-1906.csv")
    df1_sources = pd.read_csv("scopus/source-results-math_cs-citescore-2018.csv", header=0)
    # df2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1701-1706.csv")
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1401-1406.csv")
    df3_sources = pd.read_csv("scopus/source_math+comp,2013.csv", header=0)

    scopus_2014_comp = ScopusHandler(df3, df3_sources, "scopus_videos_2014_comp")
    scopus_2019_comp = ScopusHandler(df1, df1_sources, "scopus_videos_2019_comp")

    # scopus_2014_comp.plot_journals_scores()
    # scopus_2019_comp.plot_journals_scores()
    # for _i in range(1, 7):
        # scopus_2014_comp.plot_journals_scores(days_until=360 * _i)
    # scopus_2019_comp.plot_journals_scores(days_until=360)

def _201004():
    # 비디오 논문, 저널 수의 시계열 추이
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange
    from scopus_handler import ScopusHandler

    df2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_life+earch_top60_1401-1406.csv")
    df2_sources = pd.read_csv("", header=0)
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_math+comp_top5perc_1401-1406.csv")
    df3_sources = pd.read_csv("scopus/source_math+comp,2013.csv", header=0)
    
    scopus_2014_comp = ScopusHandler(df3, df3_sources, "scopus_videos_2014_comp")
    scopus_2014_life = ScopusHandler(df2, df2_sources, "scopus_videos_2014_life")

    # scopus_2014_comp.plot_journals_scores()
    # scopus_2019_comp.plot_journals_scores()
    for _i in range(1, 7):
        scopus_2014_comp.set_target_videos(days_until=360 * _i)
    # scopus_2019_comp.plot_journals_scores(days_until=360)

def plot_timedelta_metrics(targets, metric="viewCount", q=0.25, where_videos=None, scale_by_sub=True, label_by="content"):
    # Reference를 스타일별로 플롯
    import numpy as np, pandas as pd
    import matplotlib.pyplot as plt
    from db_handler import DBHandler
    from datetime import date

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

    def fetch_videos(target, q_target):
        db_handler.sql_handler.select(
        "scopus_videos_%s" % target,
        _list_fields
        ).where("viewCount", q_target, ">")
        if where_videos != None:
            db_handler.sql_handler.where(*where_videos)
        return db_handler.execute().fetchall()

    def calc_q_target(target, metric, q):
        _q_target = pd.read_csv("scopus/scopus_videos_%s.csv" % target, header=0)[metric].quantile(q)
        print("Quantile %.2f\n%s: %.1f\t" % (q, target, _q_target))
        return _q_target

    if type(targets) in (tuple, list):
        for _target in targets:
            _q_target = calc_q_target(_target, metric, q)
            _list_videos += fetch_videos(_target, _q_target)
    else:
        _q_target = calc_q_target(targets, metric, q)
        _list_videos += fetch_videos(targets, _q_target)

    _list_dict_videos = list(
    map(lambda _row: dict(zip(_list_fields, _row)), _list_videos))

    # Channels : Get subscriber count
    _list_columns_channels = ["idx", "channelId", "subscriberCount", "user_type"]
    db_handler.sql_handler.select("channels", _list_columns_channels)
    if scale_by_sub:
        db_handler.sql_handler.where("subscriberCount", None, "<>")  # Filter off NULL subscriberCount
    _list_channels = db_handler.execute().fetchall()
    # {channelId : tuple(...), ...}
    _dict_channels = dict(
    zip(list(map(lambda _row: _row[1], _list_channels)), _list_channels))

    if label_by == "video_visual":
        _list_labels = [
            "creative",
            "presentation",
            "raw",
            "fixed"
        ]

    elif label_by == "user_type":
        _list_labels = [
            "individual_researchers",
            "individual_citizens",
            "individual_journalists",
            "individual_professionals",
            "researchers_community",
            "research_organization",
            "funding_organization",
            "public_authorities",
            "civil_society_organization",
            "publishers/journals",
            "media",
            "business",
            "others",
        ]

    elif label_by == "content":
        _list_labels = [
            "paper_explanation",
            "paper_linked_supplementary",
            "paper_supplementary",
            "paper_application",
            "paper_assessment",
            "paper_reference",
            "news",
        ]

    # Hashmap
    dict_content_key = dict()
    dict_x = dict()
    dict_y = dict()
    for _label in _list_labels:
        dict_content_key[_label] = _label
        dict_x[_label] = list()
        dict_y[_label] = list()

    df1 = pd.read_csv("scopus/scopus_math+comp_top5perc_1401-1406.csv", header=0)
    df2 = pd.read_csv("scopus/scopus_life+earch_top60_1401-1406.csv", header=0)
    df3 = pd.read_csv("scopus/scopus_math+comp_top5perc_1901-1906.csv", header=0)
    df4 = pd.read_csv("scopus/scopus_life+earch_top60_1901-1906.csv", header=0)
    df = pd.concat([df1, df2, df3, df4])

    _num_dots = 0
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

        # Add label
        if label_by == "video_visual":
            _dict_row["label"] = _dict_row["video_visual"]
        elif label_by == "content":
            _dict_row["label"] = _dict_row["content"]
        elif label_by == "user_type":
            try:
                _dict_row["label"] = _dict_channels[_dict_row["channelId"]][3]
            except KeyError:
                continue

        if scale_by_sub:
            try:
                _dict_row["y_value"] = np.log10(_dict_row[metric] / _dict_channels[_dict_row["channelId"]][2]) if _dict_channels[_dict_row["channelId"]][2] != 0 else np.log10(_dict_row[metric])
                dict_y[_dict_row["label"]].append(_dict_row["y_value"])
            except KeyError:
                continue
        else:
            dict_y[_dict_row["label"]].append(np.log10(_dict_row[metric]))

        # Add x
        dict_x[_dict_row["label"]].append(_dict_row["age"])

        _num_dots += 1

    # Scatter
    plt.figure(figsize=(8, 5))

    _tup_plts = tuple(map(lambda _label: plt.scatter(x=dict_x[_label], y=dict_y[_label], s=12, marker="o"), _list_labels))
    _tup_legends = tuple(map(lambda _label: "%s(N=%d)" % (_label, len(dict_y[_label])), _list_labels))

    plt.legend(_tup_plts,
    _tup_legends,
    scatterpoints=1,
    loc='upper right',
    fontsize=8,
    framealpha=0.3)

    plt.title("Video metrics (%s, q=%.2f, N=%d)" % (targets, q, _num_dots))
    plt.xlabel("Video - Publication Timedelta (years)")
    plt.ylabel("log10(%s / Subscribers)" % metric) if scale_by_sub else plt.ylabel("log10(%s)" % metric)
    # plt.yscale("log")
    # plt.ylim(1, 100000)
    plt.show()

def calc_q_target(target, metric, q):
    import pandas as pd
    # 타겟 연도/분야 논문 언급 비디오에 대해 메트릭의 q를 반환
    _q_target = pd.read_csv("scopus/scopus_videos_%s.csv" % target, header=0)[metric].quantile(q)
    print("Quantile %.2f\n%s: %.1f\t" % (q, target, _q_target))
    return _q_target

def boxplot_by_label(targets="2014_life", label_by="user_type", metric="viewCount", q=None, log_scale=True):
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange
    db_handler = DBHandler()
    _dict_df = dict()
    # _list_idx_videos_2019_life = [2, 3, 6, 10, 12, 17, 18, 38, 43, 50, 55, 56, 59, 67, 72, 73, 78, 86, 88, 90, 93, 94, 101, 108, 109, 110, 113, 116, 120, 122, 124, 128, 129, 130, 139, 140, 142, 145, 150, 153, 158, 159, 161, 163, 165, 166, 171, 175, 178, 181, 184, 190, 195, 199, 208, 209, 214, 217, 222, 223, 230, 232, 233, 238, 246, 247, 254, 256, 258, 264, 267, 270, 271, 275, 277, 281, 284, 286, 291, 292, 297, 298, 299, 300, 303, 305, 310, 311, 314, 316, 317, 318, 324, 326, 327, 330, 333, 334, 340, 343]
    _dict_videos = dict()
    
    if type(targets) == list:
        for _target in targets:
            _dict_df[_target] = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_%s.csv" % _target)
            db_handler.sql_handler.select("scopus_videos_%s" % _target, ["idx_paper", "publishedAt"])
            if type(q) != type(None):
                db_handler.sql_handler.where(metric, calc_q_target(_target, metric, q), ">")
            _dict_videos[_target] = db_handler.execute().fetchall()
            
    else:
        _dict_df[targets] = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_%s.csv" % targets)
        db_handler.sql_handler.select("scopus_videos_%s" % targets, ["idx_paper", "publishedAt"])
        _dict_videos[targets] = db_handler.execute().fetchall()

    for _target in _dict_df:
        print("# ", _target, len(_dict_videos[_target]))
    
    # Set list_labels
    if label_by == "video_visual":
        _list_labels = [
            "creative",
            "presentation",
            "raw",
            "fixed"
        ]

    elif label_by == "user_type":
        _list_labels = [
            "individual_researchers",
            "individual_citizens",
            # "individual_journalists",
            "individual_professionals",
            "researchers_community",
            "research_organization",
#             "funding_organization",
#             "public_authorities",
            "civil_society_organization",
            "publishers/journals",
            "media",
            "business",
            "others",
        ]

    elif label_by == "content":
        _list_labels = [
            "paper_explanation",
            "paper_linked_supplementary",
            "paper_supplementary",
            "paper_application",
            "paper_assessment",
            "paper_reference",
            "news",
        ]
    
    # Get idx_papers from DB
#     _dict_list_idx_papers_by_target = dict()
#     for _target in _dict_df:
#         _dict_list_idx_papers_by_target[_target] = dict()
#         if label_by == "user_type":
#             for _label in _list_labels:
#                 db_handler.sql_handler.select("channels", "channelId").where("user_type", _label)  # Get target channelIds
#                 _list_target_channelids = list(map(lambda _row: _row[0], db_handler.execute().fetchall()))
#                 print("[+]_list_target_channelids:", _list_target_channelids)
#                 if len(_list_target_channelids):
#                     db_handler.sql_handler.select("scopus_videos_%s" % _target, "idx_paper").where("channelId", _list_target_channelids, "in")  # Get target idx_papers
#                     _dict_list_idx_papers_by_target[_target][_label] = list(map(lambda _row: _row[0], db_handler.execute().fetchall()))
#                 else:
#                     _dict_list_idx_papers_by_target[_target][_label] = list()
#                 print("[+]# Target DOIs:", _target, _label, len(_dict_list_idx_papers_by_target[_target][_label]))
        
#         else:
#             pass

    # Get metrics
    _dict_list_metrics_by_target = dict()
    for _target in _dict_df:
        _dict_list_metrics_by_target[_target] = dict()
        if label_by == "user_type":
            for _label in _list_labels:
                db_handler.sql_handler.select("channels", "channelId").where("user_type", _label)  # Get target channelIds
                _list_target_channelids = list(map(lambda _row: _row[0], db_handler.execute().fetchall()))
                if len(_list_target_channelids):
                    db_handler.sql_handler.select("scopus_videos_%s" % _target, metric).where("channelId", _list_target_channelids, "in")  # Get metrics
                    _dict_list_metrics_by_target[_target][_label] = list(map(lambda _row: _row[0], db_handler.execute().fetchall()))
                    if log_scale:
                        _dict_list_metrics_by_target[_target][_label] = np.log10(_dict_list_metrics_by_target[_target][_label])
                else:
                    _dict_list_metrics_by_target[_target][_label] = list()
                print("[+]# Target videos:", _target, _label, len(_dict_list_metrics_by_target[_target][_label]))
        
        else:
            pass
        
    # Boxplot
    _list_data = list()
    _list_plot_labels = list()
    for _label in _list_labels:
        _list_temp = list()
        for _target in _dict_list_metrics_by_target:
            _list_temp.append(_dict_list_metrics_by_target[_target][_label])
        _list_data.append(_list_temp)
        _list_plot_labels.append(_label)
    
    fig, axes = plt.subplots(ncols=len(_list_labels), figsize=(16, 6), sharey=True)
#     fig, axes = plt.subplots(ncols=len(_list_labels), sharey=True)
    fig.subplots_adjust(wspace=0)
    
    for _i, ax in enumerate(axes):
        ax.boxplot(_list_data[_i])
        _xticklabels = list(map(lambda _target: "%s\n(N=%d)" % (_target, len(_dict_list_metrics_by_target[_target][_list_plot_labels[_i]])), targets))
        ax.set_xlabel("\n".join(_list_plot_labels[_i].split("_")), fontsize=8)
        ax.set_xticklabels(_xticklabels, fontsize=6)
        ax.margins(0.05) # Optional
    
    fig.suptitle(metric)
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    plt.ylabel("log10(%s)" % metric) if log_scale else plt.ylabel(metric)
#     plt.xlabel(label_by)
#     plt.yscale("log")
    plt.show()

def _201117():
    boxplot_by_label(targets=["2014_life", "2014_comp"], metric="viewCount", q=0.1, log_scale=True)

def _201202():
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange
    from scopus_handler import ScopusHandler
    
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_comp.csv")
    df3_sources = pd.read_csv("scopus/source-results-math_cs-citescore-2013.csv", header=0)
    scopus_2014_comp = ScopusHandler(df3, df3_sources, "scopus_videos_2014_comp")

    scopus_2014_comp.plot_box_by_journals()

def _201208():
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange
    from scopus_handler import ScopusHandler
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_comp.csv")
    df3_sources = pd.read_csv("scopus/source_2013_comp.csv", header=0)
    scopus_2014_comp = ScopusHandler(df3, df3_sources, "scopus_videos_2014_comp", title="2014_comp", verbose=False)
    # fig1
    scopus_2014_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="sum", label_by=None, regression=True, log_scale=True)
    # fig2
    scopus_2014_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="sum", label_by="content-simple", regression=False, log_scale=True)
    # fig3
    scopus_2014_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="sum", label_by="content-simple", regression=True, log_scale=True)
    # fig4
    scopus_2014_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="calibrated-sum", label_by="content-simple", regression=False, log_scale=True)
    # fig5
    scopus_2014_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="calibrated-sum", label_by="content-simple", regression=True, log_scale=True)
    
    df1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2019_comp.csv")
    df1_sources = pd.read_csv("scopus/source_2018_comp.csv", header=0)
    scopus_2019_comp = ScopusHandler(df1, df1_sources, "scopus_videos_2019_comp", title="2019_comp", verbose=False)
    # fig6
    scopus_2019_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="sum", label_by="content-simple", regression=True, log_scale=True)
    # fig7
    scopus_2019_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="calibrated-sum", label_by="content-simple", regression=True, log_scale=True)

def _201215():
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from scipy import stats
    from datetime import datetime, timedelta
    from calendar import monthrange
    from scopus_handler import ScopusHandler
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_comp.csv")
    df3_sources = pd.read_csv("scopus/source_2013_comp.csv", header=0)
    scopus_2014_comp = ScopusHandler(df3, df3_sources, "scopus_videos_2014_comp", title="2014_comp", verbose=False)
    
    scopus_2014_comp.model_metrics(paper_metric="Cited by", video_metric="viewCount", method="calibrated-weighed-sum", label_by="content-simple", regression=True, log_scale=True)

def _201217(subject="comp", m=3, num_comparisons=6, max_num_trial=6, metric="Cited by", log_scale=True, list_metrics=["num_affiliations", "Cited by"], list_log_scale=[False, True], alpha=0.05):
    if num_comparisons < max_num_trial:
        raise ValueError
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    import functools
    from scipy.stats import normaltest, iqr, ttest_ind
    from scopus_handler import ScopusHandler

    def preprocess_authors(df):
        _column_name = "Author(s) ID"
        df = df.astype({_column_name: str})
        # nan, "[No author id available]"
        df = df[df[_column_name].notna()]
        df = df[df[_column_name] != "[No author id available]"]
        # Split by ;
        df = __set_num_authors(df)
        df = __set_first_author(df)
        df = __set_last_author(df)
        df = __set_list_authors(df)
        return df

    def __set_num_authors(df):
        df["num_authors"] = df["Author(s) ID"].apply(lambda _text: len(_text.split(";")))
        return df

    def __set_first_author(df):
        df["first_author"] = df["Author(s) ID"].apply(lambda _text: _text.split(";")[0])
        return df

    def __set_last_author(df):
        df["last_author"] = df["Author(s) ID"].apply(lambda _text: _text.split(";")[-1])
        return df

    def __set_list_authors(df):
        df["list_authors"] = df["Author(s) ID"].apply(lambda _text: _text.split(";"))
        return df

    def preprocess_affiliations(df):
        _column_name = "Affiliations"
        df = df.astype({_column_name: str})
        # nan
        df = df[df[_column_name].notna()]
        # Split by ;
        df["num_affiliations"] = df[_column_name].apply(lambda _text: len(_text.split(";")))
        return df

    def preprocess_funding(df):
        import math
        _column_name = "Funding Details"
        df["is_funded"] = df[_column_name].fillna(False)
        df["is_funded"] = df["is_funded"].apply(lambda _text: True if _text != False else _text)
    #     df["is_funded"] = df[_column_name].apply(lambda _text: False if math.isnan(_text) else True)
        return df

    def preprocess_access_type(df):
        _column_name = "Access Type"
        df["is_open"] = df[_column_name].fillna(False)
        df["is_open"] = df["is_open"].apply(lambda _text: True if _text != False else _text)
    #     df["is_funded"] = df[_column_name].apply(lambda _text: False if math.isnan(_text) else True)
        return df

    def preprocess_df(df):
        # 저자 수, 기관 수: 같은 수
        # 국제 집필 여부, 펀드 유무, 공개 논문 여부: 같은 여부
        # 동일 저널, 동일 문서 타입, 동일 토픽: 같은 분류
        df = df.drop_duplicates(subset=["DOI"])
        df = preprocess_authors(df)
        df = preprocess_affiliations(df)
        df = preprocess_funding(df)
        df = preprocess_access_type(df)
        return df

    def get_filtering(target_scopus, df_counterparts, list_comparisons_equal=None, list_comparisons_isin_pairs=None):
        if type(list_comparisons_equal) != type(None):
            _filtering_equal = list(map(lambda _column_name: df_counterparts[_column_name].apply(lambda _text: _text == target_scopus[_column_name]), list_comparisons_equal))
        else:
            _filtering_equal = None
        # _filtering_isin = list(map(lambda _pair_column_names: target_scopus[_pair_column_names[0]].isin(df_counterparts[_pair_column_names[1]])))
        # _filtering_isin = list(map(lambda _pair_column_names: df_counterparts[_pair_column_names[0]].str.contains(target_scopus[_pair_column_names[1]]), list_comparisons_isin_pairs))
        if type(list_comparisons_isin_pairs) != type(None):
            _filtering_isin = list(map(lambda _pair_column_names: df_counterparts[_pair_column_names[0]].apply(lambda _list: target_scopus[_pair_column_names[1]] in _list),  # Get boolean
                list_comparisons_isin_pairs)
            )
        else:
            _filtering_isin = None
        
        
        # temp = pd.concat(
        #     _filtering_isin,
        #     axis=1
        # ).all(axis=1)
        # print(temp.value_counts())
        # exit()
        
        # _filtering = pd.concat(
        #     list(map(lambda _column_name: df_counterparts[_column_name] == target_scopus[_column_name] if _column_name not in comparisons_isin \
        #         else target_scopus[_column_name].isin(df_counterparts[_column_name]),
        #         list_comparisons)),
        #     axis=1
        # ).all(axis=1)
        if _filtering_equal != None and _filtering_isin != None:
            _filtering = pd.concat(
                _filtering_equal + _filtering_isin,
                axis=1
            ).all(axis=1)
            return _filtering
        elif _filtering_equal != None:
            _filtering = pd.concat(
                _filtering_equal,
                axis=1
            ).all(axis=1)
            return _filtering
        elif _filtering_isin != None:
            _filtering = pd.concat(
                _filtering_isin,
                axis=1
            ).all(axis=1)
            return _filtering
        else:
            raise ValueError("Both list_comparisons_equal and list_comparisons_isin_pairs are None.")

    def get_pairs(df, df_sources, scopus_handler, m=3, num_comparisons=6, max_num_trial=6, metric="Cited by", log_scale=True):
        # 1:m matching
        
        _list_pairs = list()
        # _list_comparisons = [
        #     "is_open",
        #     # "num_authors",
        #     # "num_affiliations",
        #     "first_author",
        #     "last_author",
        #     "is_funded",
        #     "Document Type",
        #     "Source title",  # First priority
        # ][-num_comparisons:]
        _list_comparisons_equal = [
            # "is_open",
            # "num_authors",
            # "num_affiliations",
            # "first_author",
            "last_author",
            "is_funded",
            "Document Type",
            "Source title",  # First priority
        ][-num_comparisons:]
        _list_comparisons_isin_pairs = [
            ("list_authors", "first_author")  # (Counterparts, Target)
        ]
        dict_scopus_by_trial = dict()
        dict_scopus_by_trial["out"] = list()
        for _i in range(max_num_trial):
            dict_scopus_by_trial[_i] = list()

        _set_dois = set(map(lambda _tup_video: _tup_video[2], scopus_handler.set_target_videos().list_target_videos))
        # print("!HERE!")
        # print(len(_set_dois))
        # return
        # _set_dois = set(map(lambda _tup_video: _tup_video[2], scopus_handler.set_target_videos(where=("content", ("paper_explanation", "paper_assessment", "paper_application"), "in")).list_target_videos))

        df = preprocess_df(df)
        if log_scale:
            df = df.dropna(subset=[metric])
            df = df[df[metric] != "None"]
        # Exclude target DOIs
        df_target_dois = df[df["DOI"].isin(_set_dois)]
        df_counterparts = df[~df["DOI"].isin(_set_dois)]

        for _i, (_idx, _target_scopus) in enumerate(df_target_dois.iterrows()):
            print("[+]Processing %d of %d..." % (_i + 1, len(df_target_dois)))
        #     print(_target_scopus)
        #     _filtering = pd.concat([
        #         df3["num_authors"] == _target_scopus["num_authors"],
        #         df3["num_affiliations"] == _target_scopus["num_affiliations"],
        #         df3["is_funded"] == _target_scopus["is_funded"],
        #         df3["is_open"] == _target_scopus["is_open"],
        #         df3["Source title"] == _target_scopus["Source title"],
        #         df3["Document Type"] == _target_scopus["Document Type"],
        #     ], axis=1).all(axis=1)
            _num_trial = 0
            while True:
                print(f"\t[+]{_num_trial + 1} th trial.")
                # _filtering = get_filtering(_target_scopus, df_counterparts, _list_comparisons_equal[_num_trial:], _list_comparisons_isin_pairs)
                _filtering = get_filtering(_target_scopus, df_counterparts, _list_comparisons_equal[_num_trial:])
                # Randomly sample m matchers
                try:
                    _scopus_counterparts = df_counterparts.loc[df_counterparts[_filtering].sample(m).index]
                except ValueError:  # sample larger than population
                    print("\t[-]Sample larger than population\n\tDOI: %s\tPopulation: %d\n\tRetrying..." % (_target_scopus["DOI"], len(df_counterparts[_filtering])))
                    # _scopus_counterparts = df[_filtering]
                    _num_trial += 1
                    if _num_trial == max_num_trial:
                        print("\t[-]Reached max_num_trial. Continue to next target_scopus.")
                        dict_scopus_by_trial["out"].append(_target_scopus)
                        break
                else:
                    # Append to list
                    _list_pairs.append((_target_scopus, _scopus_counterparts))
                    dict_scopus_by_trial[_num_trial].append(_target_scopus)
                    # Drop samples from original df
                    df_counterparts = df_counterparts.drop(_scopus_counterparts.index)
                    break
        return (_list_pairs, dict_scopus_by_trial)
    
    def get_metric_pairs(df, df_sources, scopus_handler, m=3, num_comparisons=6, max_num_trial=6, metric="Cited by", log_scale=True):
        if scopus_handler.dois_targets != None:
            print("[+]DOIs already set.")
            _dict_scopus_by_trial = None
            _meters_targets = list(np.nan_to_num(df[df.DOI.isin(scopus_handler.dois_targets)][metric].astype(int)))
            _meters_counterparts = list(np.nan_to_num(df[df.DOI.isin(scopus_handler.dois_counterparts)][metric].astype(int)))
            _dois_targets = scopus_handler.dois_targets
            _dois_counterparts = scopus_handler.dois_counterparts
        else:
            print("[-]Searching DOIs")
            (_list_pairs, _dict_scopus_by_trial) = get_pairs(df, df_sources, scopus_handler, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, metric=metric, log_scale=log_scale)
            _meters_targets = list(map(lambda _pair: int(np.nan_to_num(_pair[0][metric])), _list_pairs))
            _meters_counterparts = functools.reduce(lambda a, b: a + b, list(map(lambda _twin: list(np.nan_to_num(_twin[1][metric].astype(int).values)), _list_pairs)))
            _dois_targets = list(map(lambda _pair: np.nan_to_num(_pair[0]["DOI"]), _list_pairs))
            _dois_counterparts = functools.reduce(lambda a, b: a + b, list(map(lambda _twin: list(_twin[1]["DOI"].astype(str).values), _list_pairs)))
        # print(_meters_counterparts)
        if log_scale:
            _meters_targets = np.log10(_meters_targets)
            _meters_counterparts = np.log10(_meters_counterparts)
        return (_meters_counterparts, _meters_targets, _dict_scopus_by_trial, _dois_targets, _dois_counterparts)
    
    def get_corr(df, df_sources, scopus_handler, m=3, num_comparisons=6, max_num_trial=6, list_metrics=["num_affiliations", "Cited by"], list_log_scale=[False, True]):
        _list_meters_targets = list()
        _list_meters_counterparts = list()
        (_list_pairs, _dict_scopus_by_trial) = get_pairs(df, df_sources, scopus_handler, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, metric=list_metrics[1], log_scale=list_log_scale[1])
        # print(_list_pairs)
        for _i in range(2):
            _metrics_targets = list(map(lambda _pair: int(np.nan_to_num(_pair[0][list_metrics[_i]])), _list_pairs))
            _metrics_counterparts = functools.reduce(lambda a, b: a + b, list(map(lambda _pair: list(np.nan_to_num(_pair[1][list_metrics[_i]].astype(int).values)), _list_pairs)))
            
            if list_log_scale[_i]:
                _metrics_targets = np.log10(_metrics_targets)
                _metrics_counterparts = np.log10(_metrics_counterparts)

            _list_meters_targets.append(_metrics_targets)
            _list_meters_counterparts.append(_metrics_counterparts)
        
        def plot_scatter(list_meters, list_metrics, list_log_scale):
            # print("[+]Plot counterparts")
            plt.ylabel(list_metrics[0]) if list_log_scale[0] else plt.ylabel(f"log10{list_metrics[0]}")
            plt.ylabel(list_metrics[1]) if list_log_scale[1] else plt.ylabel(f"log10{list_metrics[1]}")
            plt.scatter(list_meters[0], list_meters[1])
            plt.show()
        
        plot_scatter(_list_meters_counterparts, list_metrics, list_log_scale)
        plot_scatter(_list_meters_targets, list_metrics, list_log_scale)
    
    def __remove_outliers(list_meters, outlier_threshold=1.5):
        S1 = pd.Series(list_meters)
        _iqr1 = iqr(S1)
        S1 = S1[S1.between(S1.quantile(0.25) - outlier_threshold * _iqr1, S1.quantile(0.75) + outlier_threshold * _iqr1)]
        return list(S1)

    def __normaltest(list_meters, alpha):
        stat, p  = normaltest(list_meters)
        # stat, p  = shapiro(S)
        # stat, p = kstest(S1, S2)
        print(f"p = {p}")
        if p > alpha :
            print("Normal.")
        else :
            print("NOT normal.")

        
    # df1 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2019_comp.csv")
    # df1_sources = pd.read_csv("scopus/source_2018_comp.csv", header=0)
    # scopus_2019_comp = ScopusHandler(df1, df1_sources, "scopus_videos_2019_comp", verbose=False)
    # df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_comp.csv")
    # df3_sources = pd.read_csv("scopus/source_2013_comp.csv", header=0)
    # scopus_2014_comp = ScopusHandler(df3, df3_sources, "scopus_videos_2014_comp", verbose=False)
    # _2019_wo_videos_cit, _2019_w_videos_cit, _2019_dict_scopus_by_trial = get_pairs(df1, df1_sources, scopus_2019_comp, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, metric=metric, log_scale=log_scale)
    # _2014_wo_videos_cit, _2014_w_videos_cit, _2014_dict_scopus_by_trial = get_pairs(df3, df3_sources, scopus_2014_comp, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, metric=metric, log_scale=log_scale)
    
    df4 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_%s.csv" % subject)
    df4_sources = pd.read_csv("scopus/source_2013_%s.csv" % subject, header=0)
    scopus_2014 = ScopusHandler(df4, df4_sources, "scopus_videos_2014_%s" % subject, verbose=True, preset_dois=True)
    scopus_2014.db_handler.sql_handler.list_where_clauses = []
    # get_corr(df4, df4_sources, scopus_2014, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, list_metrics=list_metrics, list_log_scale=list_log_scale)
    _2014_wo_videos_cit, _2014_w_videos_cit, _2014_dict_scopus_by_trial, _2014_dois_targets, _2014_dois_counterparts = get_metric_pairs(df4, df4_sources, scopus_2014, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, metric=metric, log_scale=log_scale)

    df2 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2019_%s.csv" % subject)
    df2_sources = pd.read_csv("scopus/source_2018_%s.csv" % subject, header=0)
    scopus_2019 = ScopusHandler(df2, df2_sources, "scopus_videos_2019_%s" % subject, verbose=True, preset_dois=True)
    scopus_2019.db_handler.sql_handler.list_where_clauses = []
    _2019_wo_videos_cit, _2019_w_videos_cit, _2019_dict_scopus_by_trial, _2019_dois_targets, _2019_dois_counterparts = get_metric_pairs(df2, df2_sources, scopus_2019, m=m, num_comparisons=num_comparisons, max_num_trial=max_num_trial, metric=metric, log_scale=log_scale)

    # Remove outliers
    # _2019_wo_videos_cit = __remove_outliers(_2019_wo_videos_cit)
    # _2019_w_videos_cit = __remove_outliers(_2019_w_videos_cit)
    # _2014_wo_videos_cit = __remove_outliers(_2014_wo_videos_cit)
    # _2014_w_videos_cit = __remove_outliers(_2014_w_videos_cit)
    print("2019 target DOIs:", _2019_dois_targets)
    print("2019 counterparts DOIs:", _2019_dois_counterparts)
    print("2014 target DOIs:", _2014_dois_targets)
    print("2014 counterparts DOIs:", _2014_dois_counterparts)
    if _2019_dict_scopus_by_trial != None:
        for _i in _2019_dict_scopus_by_trial:
            print("%s trial(s): %d" % (_i, len(_2019_dict_scopus_by_trial[_i])))
    if _2014_dict_scopus_by_trial != None:
        for _i in _2014_dict_scopus_by_trial:
            print("%s trial(s): %d" % (_i, len(_2014_dict_scopus_by_trial[_i])))
    print("2019")
    __normaltest(__remove_outliers(_2019_wo_videos_cit), alpha)
    __normaltest(__remove_outliers(_2019_w_videos_cit), alpha)
    print(np.mean(_2019_wo_videos_cit), np.mean(_2019_w_videos_cit))
    print(ttest_ind(_2019_wo_videos_cit, _2019_w_videos_cit))
    print("2014")
    __normaltest(__remove_outliers(_2014_wo_videos_cit), alpha)
    __normaltest(__remove_outliers(_2014_w_videos_cit), alpha)
    print(np.mean(_2014_wo_videos_cit), np.mean(_2014_w_videos_cit))
    print(ttest_ind(_2014_wo_videos_cit, _2014_w_videos_cit))
    
    plt.figure(figsize=(10, 6))
    # plt.ylim(-0.2, 3.5)
    plt.title(f"{metric} - {subject}")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel(f"log10({metric})")
    plt.boxplot([
            _2019_wo_videos_cit,
            _2019_w_videos_cit,
            _2014_wo_videos_cit,
            _2014_w_videos_cit
        ],
        labels=[
            "2019 w/o videos\n(N=%s)"%len(_2019_wo_videos_cit),
            "2019 w/ videos\n(N=%s)"%len(_2019_w_videos_cit),
            "2014 w/o videos\n(N=%s)"%len(_2014_wo_videos_cit),
            "2014 w/ videos\n(N=%s)"%len(_2014_w_videos_cit)
        ],
        showmeans=True
    )
    plt.show()

def _210105(subject, metric="Cited by"):
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from datetime import datetime, timedelta
    from calendar import monthrange
    import functools
    from scipy.stats import normaltest, iqr, ttest_ind, shapiro
    from scopus_handler import ScopusHandler
    
    def get_list_meters(scopus_handler, metric="Cited by", where=None):
        _list_dois = list(map(lambda _row: _row[2], scopus_handler.set_target_videos(where=where).list_target_videos))
        return np.log10(scopus_handler.df_scopus[scopus_handler.df_scopus.DOI.isin(_list_dois)][scopus_handler.df_scopus[metric] != "None"][metric].dropna().astype(int).values)
    
    def __remove_outliers(list_meters, outlier_threshold=1.5):
        S1 = pd.Series(list_meters)
        _iqr1 = iqr(S1)
        S1 = S1[S1.between(S1.quantile(0.25) - outlier_threshold * _iqr1, S1.quantile(0.75) + outlier_threshold * _iqr1)]
        return list(S1)

    def __normaltest(list_meters, alpha=0.05):
        try:
            stat, p  = normaltest(list_meters)
            # stat, p  = shapiro(list_meters)
        except ValueError:
            print("Normaltest not executable.")
            return (None, None)
        # stat, p  = shapiro(S)
        # stat, p = kstest(S1, S2)
        print("p = %.3f" % p)
        if p > alpha :
            print("Normal.")
        else :
            print("NOT normal.")
        return (stat, p)

    df4 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_%s.csv" % subject)
    df4_sources = pd.read_csv("scopus/source_2013_%s.csv" % subject, header=0)
    scopus_2014 = ScopusHandler(df4, df4_sources, "scopus_videos_2014_%s" % subject, verbose=False)
    scopus_2014.db_handler.sql_handler.list_where_clauses = []
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2019_%s.csv" % subject)
    df3_sources = pd.read_csv("scopus/source_2018_%s.csv" % subject, header=0)
    scopus_2019 = ScopusHandler(df3, df3_sources, "scopus_videos_2019_%s" % subject, verbose=False)
    scopus_2019.db_handler.sql_handler.list_where_clauses = []

    _2014_w_videos_cit_exp = get_list_meters(scopus_2014, metric=metric, where=("content", ["paper_explanation", "paper_application", "paper_assessment"], "in"))
    _2014_w_videos_cit_news = get_list_meters(scopus_2014, metric=metric, where=("content", ["news"], "in"))
    _2014_w_videos_cit_sup = get_list_meters(scopus_2014, metric=metric, where=("content", ["paper_linked_supplementary", "paper_supplementary"], "in"))
    _2014_w_videos_cit_ref = get_list_meters(scopus_2014, metric=metric, where=("content", ["paper_reference"], "in"))
    _2019_w_videos_cit_exp = get_list_meters(scopus_2019, metric=metric, where=("content", ["paper_explanation", "paper_application", "paper_assessment"], "in"))
    _2019_w_videos_cit_news = get_list_meters(scopus_2019, metric=metric, where=("content", ["news"], "in"))
    _2019_w_videos_cit_sup = get_list_meters(scopus_2019, metric=metric, where=("content", ["paper_linked_supplementary", "paper_supplementary"], "in"))
    _2019_w_videos_cit_ref = get_list_meters(scopus_2019, metric=metric, where=("content", ["paper_reference"], "in"))
    list_list_meters = [
        _2019_w_videos_cit_exp,
        _2019_w_videos_cit_news,
        _2019_w_videos_cit_sup,
        _2019_w_videos_cit_ref,
        _2014_w_videos_cit_exp,
        _2014_w_videos_cit_news,
        _2014_w_videos_cit_sup,
        _2014_w_videos_cit_ref
    ]
    print("Means:")
    print("\t".join(list(map(lambda _list_meters: "%.2f" % np.mean(_list_meters), list_list_meters))))
    list(map(lambda _list_meters: __normaltest(__remove_outliers(_list_meters)), list_list_meters))
    plt.figure(figsize=(12, 6))
    plt.title("AAS - Life & Earth")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel(f"log10(AAS)")
    plt.boxplot([
            _2019_w_videos_cit_exp,
            _2019_w_videos_cit_news,
            _2019_w_videos_cit_sup,
            _2019_w_videos_cit_ref,
            _2014_w_videos_cit_exp,
            _2014_w_videos_cit_news,
            _2014_w_videos_cit_sup,
            _2014_w_videos_cit_ref
        ],
        labels=[
            "2019 w/ exp\n(N=%s)"%len(_2019_w_videos_cit_exp),
            "2019 w/ news\n(N=%s)"%len(_2019_w_videos_cit_news),
            "2019 w/ sup\n(N=%s)"%len(_2019_w_videos_cit_sup),
            "2019 w/ ref\n(N=%s)"%len(_2019_w_videos_cit_ref),
            "2014 w/ exp\n(N=%s)"%len(_2014_w_videos_cit_exp),
            "2014 w/ news\n(N=%s)"%len(_2014_w_videos_cit_news),
            "2014 w/ sup\n(N=%s)"%len(_2014_w_videos_cit_sup),
            "2014 w/ ref\n(N=%s)"%len(_2014_w_videos_cit_ref),
        ],
        showmeans=True
    )
    plt.show()

def _210106(subject, metric="Cited by"):  # By channels
    import numpy as np
    import pandas as pd
    from db_handler import DBHandler
    from matplotlib import pyplot as plt
    from datetime import datetime, timedelta
    from calendar import monthrange
    import functools
    from scipy.stats import normaltest, iqr, ttest_ind, shapiro
    from scopus_handler import ScopusHandler
    
    def get_list_meters(scopus_handler, metric="Cited by", where=None):
        _list_dois = list(map(lambda _row: _row[2], scopus_handler.set_target_videos(where=where).list_target_videos))
        return np.log10(scopus_handler.df_scopus[scopus_handler.df_scopus.DOI.isin(_list_dois)][scopus_handler.df_scopus[metric] != "None"][metric].dropna().astype(int).values)
    
    def __remove_outliers(list_meters, outlier_threshold=1.5):
        S1 = pd.Series(list_meters)
        _iqr1 = iqr(S1)
        S1 = S1[S1.between(S1.quantile(0.25) - outlier_threshold * _iqr1, S1.quantile(0.75) + outlier_threshold * _iqr1)]
        return list(S1)

    def __normaltest(list_meters, alpha=0.05):
        try:
            stat, p  = normaltest(list_meters)
            # stat, p  = shapiro(list_meters)
        except ValueError:
            print("Normaltest not executable.")
            return (None, None)
        # stat, p  = shapiro(S)
        # stat, p = kstest(S1, S2)
        print("p = %.3f" % p)
        if p > alpha :
            print("Normal.")
        else :
            print("NOT normal.")
        return (stat, p)

    df4 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2014_%s.csv" % subject)
    df4_sources = pd.read_csv("scopus/source_2013_%s.csv" % subject, header=0)
    scopus_2014 = ScopusHandler(df4, df4_sources, "scopus_videos_2014_%s" % subject, verbose=False)
    scopus_2014.db_handler.sql_handler.list_where_clauses = []
    df3 = pd.read_csv("/home/hweem/git/mastersdegree/ytcrawl/customs/scopus/scopus_2019_%s.csv" % subject)
    df3_sources = pd.read_csv("scopus/source_2018_%s.csv" % subject, header=0)
    scopus_2019 = ScopusHandler(df3, df3_sources, "scopus_videos_2019_%s" % subject, verbose=False)
    scopus_2019.db_handler.sql_handler.list_where_clauses = []

    _2014_w_videos_cit_exp = get_list_meters(scopus_2014, metric=metric, where=("content", ["paper_explanation", "paper_application", "paper_assessment"], "in"))
    _2014_w_videos_cit_news = get_list_meters(scopus_2014, metric=metric, where=("content", ["news"], "in"))
    _2014_w_videos_cit_sup = get_list_meters(scopus_2014, metric=metric, where=("content", ["paper_linked_supplementary", "paper_supplementary"], "in"))
    _2014_w_videos_cit_ref = get_list_meters(scopus_2014, metric=metric, where=("content", ["paper_reference"], "in"))
    _2019_w_videos_cit_exp = get_list_meters(scopus_2019, metric=metric, where=("content", ["paper_explanation", "paper_application", "paper_assessment"], "in"))
    _2019_w_videos_cit_news = get_list_meters(scopus_2019, metric=metric, where=("content", ["news"], "in"))
    _2019_w_videos_cit_sup = get_list_meters(scopus_2019, metric=metric, where=("content", ["paper_linked_supplementary", "paper_supplementary"], "in"))
    _2019_w_videos_cit_ref = get_list_meters(scopus_2019, metric=metric, where=("content", ["paper_reference"], "in"))
    list_list_meters = [
        _2019_w_videos_cit_exp,
        _2019_w_videos_cit_news,
        _2019_w_videos_cit_sup,
        _2019_w_videos_cit_ref,
        _2014_w_videos_cit_exp,
        _2014_w_videos_cit_news,
        _2014_w_videos_cit_sup,
        _2014_w_videos_cit_ref
    ]
    print("Means:")
    print("\t".join(list(map(lambda _list_meters: "%.2f" % np.mean(_list_meters), list_list_meters))))
    list(map(lambda _list_meters: __normaltest(__remove_outliers(_list_meters)), list_list_meters))
    plt.figure(figsize=(12, 6))
    plt.title("AAS - Life & Earth")
    # plt.yscale("log")
    # plt.ylim([0, 200])
    plt.ylabel(f"log10(AAS)")
    plt.boxplot([
            _2019_w_videos_cit_exp,
            _2019_w_videos_cit_news,
            _2019_w_videos_cit_sup,
            _2019_w_videos_cit_ref,
            _2014_w_videos_cit_exp,
            _2014_w_videos_cit_news,
            _2014_w_videos_cit_sup,
            _2014_w_videos_cit_ref
        ],
        labels=[
            "2019 w/ exp\n(N=%s)"%len(_2019_w_videos_cit_exp),
            "2019 w/ news\n(N=%s)"%len(_2019_w_videos_cit_news),
            "2019 w/ sup\n(N=%s)"%len(_2019_w_videos_cit_sup),
            "2019 w/ ref\n(N=%s)"%len(_2019_w_videos_cit_ref),
            "2014 w/ exp\n(N=%s)"%len(_2014_w_videos_cit_exp),
            "2014 w/ news\n(N=%s)"%len(_2014_w_videos_cit_news),
            "2014 w/ sup\n(N=%s)"%len(_2014_w_videos_cit_sup),
            "2014 w/ ref\n(N=%s)"%len(_2014_w_videos_cit_ref),
        ],
        showmeans=True
    )
    plt.show()


if __name__ == '__main__':
    # 210105
    _210105(subject="life", metric="AAS")

    # 201217
    # _201217(subject="comp", m=2, num_comparisons=1, max_num_trial=1, metric="Cited by", log_scale=True)
    # _201217(subject="comp", m=2, num_comparisons=3, max_num_trial=1, metric="Cited by", log_scale=True)
    # _201217(subject="comp", m=2, num_comparisons=4, max_num_trial=1, metric="Cited by", log_scale=True)
    # _201217(subject="life", m=2, num_comparisons=3, max_num_trial=1, metric="num_authors", log_scale=True)
    # _201217(subject="comp", m=2, num_comparisons=3, max_num_trial=1, list_metrics=["num_authors", "Cited by"], list_log_scale=[False, True])
    
    # 201215
    # _201215()
    
    # 201208
    # _201208()
    
    # 201202
    # _201202()
    
    # 201117
    # _201117()
    
    # 200918
    # _200918()
    
    # 200914
    # _200914()

    # 200904
    # _200904()
    
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
