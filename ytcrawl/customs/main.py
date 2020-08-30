from channels import youtube_channels, YouTubeChannels
from db_channels_uploader import DBChannelsUploader
from db_videos_uploader import DBVideosUploader
from db_papers_uploader import DBPapersUploader
from twitter_organizer import TwitterOrganizer
from altmetric_it import AltmetricIt
from db_handler import DBHandler
from preprocessor import Preprocessor

import argparse
import os
import json
import urllib.request
import pandas as pd
from random import shuffle
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
import re

from search_custom import YouTubeSearch
from videos import filter_videos_by_viewcount, YouTubeVideos


# Customize args: API key
# api_key = 'AIzaSyCVMEUGxxsSw-BKH4c06PHKr_F4qjSdwJw'  # ytcrawl
api_key = 'AIzaSyDuW2lWKYOc-tPjwcXso4LhR8_ZMEZOGKw'  # ytcrawl1
# api_key = 'AIzaSyBahI8vJbinh7itJs2hJRNW4spp0B2Dqpk'  # ytcrawl2

# channelIDs->VideoIDs->uploadVideos


def upload_videos_from_channel_ids(api_key):
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
    # help='List of Channel IDs', default='fromdb')
    parser.add_argument(
        '--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    # parser.add_argument('--api-key', help='API key', default=api_key)

    # Search args
    parser.add_argument('--part', default='id, snippet')
    parser.add_argument('--eventType', default=None)
    parser.add_argument('--channelId', default=None)
    parser.add_argument('--forDeveloper', default=None)
    parser.add_argument('--videoSyndicated', default=None)
    parser.add_argument('--channelType', default=None)
    parser.add_argument('--videoCaption', default=None)
    parser.add_argument('--publishedAfter', default=None)
    parser.add_argument('--publishedBefore', default=None)
    parser.add_argument('--onBehalfOfContentOwner', default=None)
    parser.add_argument('--forContentOwner', default=None)
    parser.add_argument('--regionCode', default=None)
    parser.add_argument('--location', default=None)
    parser.add_argument('--locationRadius', default=None)
    parser.add_argument('--topicId', default=None)
    parser.add_argument('--publishedBefore', default=None)
    parser.add_argument('--videoDimension', default=None)
    parser.add_argument('--videoLicense', default=None)
    parser.add_argument('--maxResults', default=50)
    parser.add_argument('--videoType', default=None)
    parser.add_argument('--videoDefinition', default=None)
    parser.add_argument('--pageToken', default=None)
    parser.add_argument('--relatedToVideoId', default=None)
    parser.add_argument('--relevanceLanguage', default=None)
    parser.add_argument('--videoDuration', default=None)
    parser.add_argument('--forMine', default=None)
    parser.add_argument('--q', default='Google')
    parser.add_argument('--safeSearch', default=None)
    parser.add_argument('--videoEmbeddable', default=None)
    parser.add_argument('--videoCategoryId', default=None)
    parser.add_argument('--order', default=None)
    parser.add_argument(
        '--fields', default='items(id(videoId), snippet(channelTitle))')

    args = vars(parser.parse_args())

    youtube_search = YouTubeSearch(args)
    youtube_search.set_list_queries(['Generetive Adversarial Network'])
    youtube_search.start_search()

    # Video uploader
    db_videos_uploader = DBVideosUploader()

    dict_video_ids = youtube_search_recursive(args)

    # From dict to list
    list_video_ids = []
    for item in dict_video_ids['items']:
        list_video_ids.append(item['id']['videoId'])

    num_new_uploads = 0
    num_queried = len(list_video_ids)
    print('# of videos in query:', num_queried)
    # For every video id
    for i, video_id in enumerate(list_video_ids):
        print('\tProcessing:', i+1, 'out of', num_queried, 'video')
        # Check if video already exists in DB
        if db_videos_uploader.video_id_exists(video_id, args):
            continue

        args.video_id = video_id
        args.part = 'snippet, statistics'
        args.fields = 'items(snippet(channelTitle, tags, title, defaultAudioLanguage, publishedAt, defaultLanguage, channelId, description), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount), contentDetails(duration))'

        # Get data through API
        response = youtube_videos(args)

        # with open(os.path.join('./results/videos', args.video_id + '.txt'), 'w') as new_json:
        #     json.dump(response.get('items', []), new_json)
        items = response.get('items', [])[0]
        print('\nItems from youtube_video:', items)

        db_videos_uploader.insert(
            'videos', items, {'q': args.q, 'videoId': args.video_id})
        num_new_uploads += 1

    print('Newly uploaded videos:', num_new_uploads)
    # Close DB connection
    db_videos_uploader.close()

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--q', help='Search term', default='Google')
#     parser.add_argument('--max-results', help='Max results', default=50)
#     parser.add_argument('--region-code', help='Region code', default=None)
#     parser.add_argument('--page-token', help='Page token', default=None)
#     parser.add_argument('--order', help='Order', default=None)
#     parser.add_argument('--channelId', help='Channel ID', default=None)
#     parser.add_argument('--f-channel-ids', help='List of Channel IDs', default='channel_ids_AI.txt')
#     parser.add_argument('--api-key', help='API key', default=None)

#     args = parser.parse_args()

#     # Customize args: API key
#     # args.api_key = 'AIzaSyCVMEUGxxsSw-BKH4c06PHKr_F4qjSdwJw' # ytcrawl
#     # args.api_key = 'AIzaSyDuW2lWKYOc-tPjwcXso4LhR8_ZMEZOGKw' # ytcrawl1
#     args.api_key = 'AIzaSyBahI8vJbinh7itJs2hJRNW4spp0B2Dqpk' # ytcrawl2

#     # try:
#     #     youtube_search(args)
#     # except (HttpError, e):
#     #     print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))


#     dict_video_ids = youtube_search_recursive(args)

#     # From dict to list
#     list_video_ids = []
#     for item in dict_video_ids['items']:
#         list_video_ids.append(item['id']['videoId'])

#     # Video uploader
#     db_videos_uploader = DBVideosUploader()

#     # For every video id
#     for video_id in list_video_ids:

#         # Check if video already exists in DB
#         if db_videos_uploader.video_id_exists(video_id, args):
#             continue

#         args.video_id = video_id

#         # Get data through API
#         response = youtube_videos(args)

#         # with open(os.path.join('./results/videos', args.video_id + '.txt'), 'w') as new_json:
#         #     json.dump(response.get('items', []), new_json)
#         items = response.get('items', [])[0]
#         print('\nItems from youtube_video:', items)

#         db_videos_uploader.insert('videos', items, {'q': args.q, 'videoId': args.video_id})


#     # Close DB connection
#     db_videos_uploader.close()


# # ChannelIds->uploadChannels

# from db_channels_uploader import DBChannelsUploader
# from channels import youtube_channels
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('--f-channel-ids',
#                         help='List of Channel IDs', default=None)

#     args = parser.parse_args()

#     # DBHandler
#     db_channels_uploader = DBChannelsUploader()

#     # Get channels list
#     if type(args.list_channel_ids) == str:
#         with open(args.list_channel_ids) as f:
#             args.list_channel_ids = json.load(f)[0].values()

#     for channel_id in args.list_channel_ids:

#         # Check if channel already exists in DB
#         if db_channels_uploader.channel_id_exists(channel_id):
#             continue

#         args.channel_id = channel_id

#         # Get data through API
#         response = youtube_channels(args)
#         items = response.get('items', [])[0]
#         print('\nItems from youtube_channels:', items)
#         db_channels_uploader.insert(
#             'channels', items, {'channelId': args.channel_id})

#     db_channels_uploader.close()


# search->(video:check viewCount->)channelIds->uploadChannels
def upload_channels_from_search():
    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='Search term', default='Google')
    parser.add_argument('--max-results', help='Max results', default=50)
    parser.add_argument('--order', help='Order', default=None)
    parser.add_argument('--region-code', help='Region code', default=None)
    parser.add_argument('--page-token', help='Page token', default=None)
    parser.add_argument('--channel-id', help='Channel ID', default=None)

    # Custom args
    parser.add_argument('--f-channel-ids',
                        help='List of Channel IDs', default=None)
    parser.add_argument(
        '--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    parser.add_argument('--api-key', help='API key', default=api_key)
    parser.add_argument(
        '--view-over', help='Validate if viewCount of video is over threshold', default=1000)

    args = parser.parse_args()

    args.part = 'id,snippet'
    args.fields = 'items(id(videoId),snippet(channelId))'

    if args.up_to:
        if int(args.up_to) < int(args.max_results):
            args.max_results = args.up_to

    dict_responses = youtube_search_recursive(args)
    # dict_responses = {'q': 'gan', 'items': [{'snippet': {'channelId': 'UCRTV5p4JsXV3YTdYpTJECRA'}}, {'snippet': {'channelId': 'UCERCYdynnvAR4NJHyG7O5_A'}}]}

    # Filter by viewCount
    dict_responses['items'] = filter_videos_by_viewcount(
        args, dict_responses['items'])

    # DBHandler
    db_channels_uploader = DBChannelsUploader()

    # Get list of channel Ids.
    channels_list = list()
    for item in dict_responses['items']:
        # item == {'snippet': {'channelId': 'UCP7jMXSY2xbc3KCAE0MHQ'}}
        channels_list.append(item['snippet']['channelId'])

    # fields="items(statistics(commentCount, subscriberCount, videoCount, viewCount), brandingSettings(channel(description, title, country, defaultLanguage, keywords)), snippet(publishedAt))"

    for channel_id in channels_list:
        # Check if channel already exists in DB
        if db_channels_uploader.channel_id_exists(channel_id):
            continue

        args.channel_id = channel_id
        print('args:', args)
        # Get data through API
        response = youtube_channels(args)
        print('response:', response)
        items = response.get('items', [])[0]
        print('Items from youtube_channels:', items)
        db_channels_uploader.insert(
            'channels', items, {'channelId': args.channel_id})

    db_channels_uploader.close()

# videos->get urls from description->upload papers


# def upload_papers_from_videos():
#     parser = argparse.ArgumentParser()

#     # Custom args
#     parser.add_argument('--f-channel-ids',
#                         help='List of Channel IDs', default=None)

#     args = parser.parse_args()

#     # Get urls from videos
#     db_papers_uploader = DBPapersUploader()
#     sql = "SELECT `idx`, `description` FROM videos WHERE description LIKE '%arxiv.org/abs/%' OR description LIKE '%arxiv.org/pdf/%';"
#     # sql = "SELECT `idx`, `description` FROM videos WHERE idx=23;"
#     db_papers_uploader.mycursor.execute(sql)
#     results = db_papers_uploader.mycursor.fetchall()
#     num_queried = len(results)
#     print('# of queried videos:', num_queried)

#     # Shuffle
#     print('Before shuffle:', results[0])
#     shuffle(results)
#     print('After shuffle:', results[0])

#     for i, row in enumerate(results):
#         print('Processing:', i+1, 'out of', num_queried, 'videos')
#         args.idx_video = row[0]
#         regex_urls = re.compile(
#             r'https?://arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf|https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
#         list_urls = regex_urls.findall(row[1])
#         num_urls = len(list_urls)
#         print('# of found urls:', num_urls)
#         db_papers_uploader.num_crawled += num_urls

#         for j, url in enumerate(list_urls):
#             print('\n\tProcessing:', j+1, 'out of', num_urls, 'urls:', url)
#             args.url = db_papers_uploader.url_http_to_https(
#                 db_papers_uploader.url_pdf_to_abs(url))
#             # Check if paper exists
#             if not db_papers_uploader.paper_exists(args):
#                 items = db_papers_uploader.get_items(args)
#                 print(items)
#                 db_papers_uploader.insert('papers', items)
#                 db_papers_uploader.num_inserted += 1

#     print('\nDone')
#     print('# of queried videos:', num_queried)
#     print('# of crawled papers:', db_papers_uploader.num_crawled)
#     print('# of inserted papers:', db_papers_uploader.num_inserted)
#     print('# of existed papers:', db_papers_uploader.num_existed)
#     print('# of merge:', len(db_papers_uploader.list_merged))
#     print('Merged urls:', db_papers_uploader.list_merged)


def organize_twitter():

    twitter_organizer = TwitterOrganizer()
    twitter_organizer.update_stats(overwrite=True)


def update_papers_from_arxiv_list():
    parser = argparse.ArgumentParser()
    parser.add_argument('--table', help='Table name', default='papers_cs.AI')
    parser.add_argument('--subject', help='Subject', default='cs.AI')
    parser.add_argument('--YY', help='YY')
    parser.add_argument('--MM', help='MM')
    parser.add_argument('--overwrite', dest='overwrite',
                        help='Overwrite policy', action='store_true', default=False)

    args = parser.parse_args()
    print(args)
    args = vars(args)
    print(args)
    db_papers_uploader = DBPapersUploader()
    db_papers_uploader.update_papers_from_arxiv_list(
        args, overwrite=args['overwrite'])


def videos_by_video_ids(fp_list_searches):
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
    # help='List of Channel IDs', default='fromdb')
    # parser.add_argument('--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    # parser.add_argument('--api-key', help='API key', default=api_key)

    # Search args
    parser.add_argument(
        '--part', default='id, snippet, contentDetails, statistics, liveStreamingDetails')
    parser.add_argument('--hl', default=None)
    parser.add_argument('--maxWidth', default=None)
    parser.add_argument('--locale', default=None)
    parser.add_argument('--id', default=None)
    parser.add_argument('--onBehalfOfContentOwner', default=None)
    parser.add_argument('--regionCode', default=None)
    parser.add_argument('--pageToken', default=None)
    parser.add_argument('--maxResults', default=None)
    parser.add_argument('--chart', default=None)
    parser.add_argument('--myRating', default=None)
    parser.add_argument('--maxHeight', default=None)
    parser.add_argument('--videoCategoryId', default=None)
    parser.add_argument('--fields', default='items(id, snippet(title, publishedAt, description, tags, defaultLanguage, defaultAudioLanguage, channelTitle, channelId), contentDetails(duration), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount), liveStreamingDetails(actualStartTime))')
    parser.add_argument('--filter_by_q', action="store_true", default=False)

    # Custom args
    parser.add_argument('--random-project', action="store_true", default=False)

    args = vars(parser.parse_args())
    with open(fp_list_searches, 'r') as f:
        _list_searches = json.load(f)
        _list_searches = [
            _dict_response for _dict_response in _list_searches if _dict_response["items"]]

    # Test
    # _list_searches = _list_searches[:3]

    youtube_videos = YouTubeVideos(args)
    youtube_videos.set_list_searches(_list_searches).start(filter_by_q=False)
    return youtube_videos


def search_by_q(fp_csv, column):
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
    # help='List of Channel IDs', default='fromdb')
    parser.add_argument(
        '--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    parser.add_argument(
        '--no-recursive', help='Call search API for a single time per query.', action='store_true', default=False)
    parser.add_argument('--random-project', action="store_true", default=False)
    # parser.add_argument('--api-key', help='API key', default=api_key)

    # Search args
    parser.add_argument('--part', default='id')
    parser.add_argument('--eventType', default=None)
    parser.add_argument('--channelId', default=None)
    parser.add_argument('--forDeveloper', default=None)
    parser.add_argument('--videoSyndicated', default=None)
    parser.add_argument('--channelType', default=None)
    parser.add_argument('--videoCaption', default=None)
    parser.add_argument('--publishedAfter', default=None)
    parser.add_argument('--publishedBefore', default=None)
    parser.add_argument('--onBehalfOfContentOwner', default=None)
    parser.add_argument('--forContentOwner', default=None)
    parser.add_argument('--regionCode', default=None)
    parser.add_argument('--location', default=None)
    parser.add_argument('--locationRadius', default=None)
    parser.add_argument('--topicId', default=None)
    parser.add_argument('--videoDimension', default=None)
    parser.add_argument('--videoLicense', default=None)
    parser.add_argument('--maxResults', default=50)
    parser.add_argument('--videoType', default=None)
    parser.add_argument('--videoDefinition', default=None)
    parser.add_argument('--pageToken', default=None)
    parser.add_argument('--relatedToVideoId', default=None)
    parser.add_argument('--relevanceLanguage', default=None)
    parser.add_argument('--videoDuration', default=None)
    parser.add_argument('--forMine', default=None)
    parser.add_argument('--q', default='Google')
    parser.add_argument('--safeSearch', default=None)
    parser.add_argument('--videoEmbeddable', default=None)
    parser.add_argument('--videoCategoryId', default=None)
    parser.add_argument('--order', default=None)
    parser.add_argument(
        '--fields', default='nextPageToken, items(id(videoId))')

    args = vars(parser.parse_args())

    # db_handler = DBHandler()
    # db_handler.sql_handler.select('temp_papers', ['idx', 'urls']).where('subject_1', 'Computer Science', '=').where('subject_2', 'Machine Learning', '=')
    # db_handler.sql_handler.select('papers_cs.AI', ['idx', 'urls']).where('subject_1', 'Computer Science', '=').where('subject_2', 'Artificial Intelligence', '=')
    # _results = db_handler.execute().fetchall()

    # https to http
    # preprocessor = Preprocessor()
    # preprocessor.url_https_to_http
    # _list_queries = list(map(lambda tup: tup[1].split(', ')[1], _results))
    # _list_queries = list(map(lambda tup: preprocessor.url_https_to_http(tup[1].split(', ')[0]), _results))

    # arxiv.org/...
    # _list_queries = list(map(lambda tup: tup[1].split(', ')[0][8:], _results))
    # _list_idx_papers = list(map(lambda tup: tup[0], _results))
    # args['list_idx_papers'] = _list_idx_papers

    # _list_queries = _list_queries[:2]
    # print(_list_queries)

    data_raw = pd.read_csv(
        fp_csv, header=0, keep_default_na=False)
    print("# raw:\t%d" % len(data_raw))
    data_doi = data_raw[data_raw["DOI"] != "nan"]
    data_doi = data_doi[data_doi["DOI"].notna()]
    print("# DOI:\t%d" % len(data_doi))
    if column == "DOI":
        # Filter by DOI.
        data = data_doi[data_doi["DOI"] != ""]
        print("# data:\t%d" % len(data))
        _list_idx_papers = list(data["DOI"])
        _list_queries = list(data["DOI"])
    elif column == "Redirection":
        # Filter by redirection.
        data = data_doi[~data_doi["Redirection"].isin(["Err", "None"])]
        print("# data:\t%d" % len(data))
        _list_idx_papers = list(data["DOI"])
        _list_queries = list(data["Redirection"])
    elif column == "Title":
        # By title
        _list_idx_papers = list(data_doi["DOI"])
        _list_queries = list(
            map(lambda _title: _title.lower(), data_doi["Title"]))

    args["list_idx_papers"] = _list_idx_papers
    youtube_search = YouTubeSearch(args)
    _list_responses = youtube_search.set_list_queries(
        _list_queries).start_search()
    # print(_list_responses)

    # with open('list_searches_doi_health_2014.txt', 'w+') as fp:
    #     json.dump(_list_responses, fp)
    return youtube_search


def num_of_videos():
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
    # help='List of Channel IDs', default='fromdb')
    parser.add_argument(
        '--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    # parser.add_argument('--api-key', help='API key', default=api_key)
    parser.add_argument(
        '--no_recursive', help='Call search API for a single time per query.', action='store_true', default=False)

    # Search args
    parser.add_argument('--part', default='id')
    parser.add_argument('--eventType', default=None)
    parser.add_argument('--channelId', default=None)
    parser.add_argument('--forDeveloper', default=None)
    parser.add_argument('--videoSyndicated', default=None)
    parser.add_argument('--channelType', default=None)
    parser.add_argument('--videoCaption', default=None)
    parser.add_argument('--publishedAfter', default=None)
    parser.add_argument('--publishedBefore', default=None)
    parser.add_argument('--onBehalfOfContentOwner', default=None)
    parser.add_argument('--forContentOwner', default=None)
    parser.add_argument('--regionCode', default=None)
    parser.add_argument('--location', default=None)
    parser.add_argument('--locationRadius', default=None)
    parser.add_argument('--topicId', default=None)
    parser.add_argument('--videoDimension', default=None)
    parser.add_argument('--videoLicense', default=None)
    parser.add_argument('--maxResults', default=50)
    parser.add_argument('--videoType', default=None)
    parser.add_argument('--videoDefinition', default=None)
    parser.add_argument('--pageToken', default=None)
    parser.add_argument('--relatedToVideoId', default=None)
    parser.add_argument('--relevanceLanguage', default=None)
    parser.add_argument('--videoDuration', default=None)
    parser.add_argument('--forMine', default=None)
    parser.add_argument('--q', default='Google')
    parser.add_argument('--safeSearch', default=None)
    parser.add_argument('--videoEmbeddable', default=None)
    parser.add_argument('--videoCategoryId', default=None)
    parser.add_argument('--order', default=None)
    parser.add_argument(
        '--fields', default='pageInfo(totalResults), items')

    args = vars(parser.parse_args())

    _list_queries = [
        'science.sciencemag.org/content',
        # 'arxiv.org/abs',
        # 'nature.com/articles'
    ]
    _range_year = range(2005, 2020)

    for _year in _range_year:
        args['publishedAfter'] = '%d-01-01T00:00:00Z' % _year
        args['publishedBefore'] = '%d-01-01T00:00:00Z' % (_year + 1)
        # print(args)
        youtube_search = YouTubeSearch(args)
        youtube_search.set_list_queries(_list_queries)
        _list_responses = youtube_search.start_search()
        print(_list_responses)


def update_videos_by_list_videos(table_name, fp_list_videos, filter_by_q, overwrite):
    db_videos_uploader = DBVideosUploader(table_name)
    with open(fp_list_videos, 'r') as f:
        _list_responses = json.load(f)
    # _list_responses = _list_responses[:1]
    db_videos_uploader.upload_videos(
        _list_responses, filter_by_q=filter_by_q, overwrite=overwrite)


def upload_channels_by_list_channels(table_name, fp_list_channels, overwrite):
    db_channels_uploader = DBChannelsUploader(table_name)
    with open(fp_list_channels, 'r') as f:
        _list_responses = json.load(f)
    # Test
    # _list_responses[:1]
    db_channels_uploader.upload_channels(_list_responses, overwrite=overwrite)


def channels_by_list_channel_ids(fp_list_channel_ids=None, table_name_videos=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--part', default='id, statistics, brandingSettings, snippet')
    parser.add_argument('--hl', default=None)
    parser.add_argument('--mine', default=None)
    parser.add_argument('--mySubscribers', default=None)
    parser.add_argument('--id', default=None)
    parser.add_argument('--managedByMe', default=None)
    parser.add_argument('--onBehalfOfContentOwner', default=None)
    parser.add_argument('--forUsername', default=None)
    parser.add_argument('--pageToken', default=None)
    parser.add_argument('--categoryId', default=None)
    parser.add_argument('--maxResults', default=None)
    parser.add_argument('--fields', default="items(id, statistics(commentCount, subscriberCount, videoCount, viewCount), brandingSettings(channel(description, title, country, defaultLanguage, keywords)), snippet(publishedAt))")
    args = vars(parser.parse_args())

    if fp_list_channel_ids != None:
        with open(fp_list_channel_ids, 'r') as f:
            _list_channel_ids = json.load(f)
    elif table_name_videos != None:
        db_handler = DBHandler()
        db_handler.sql_handler.select(table_name_videos, "channelId")
        _list_channel_ids = db_handler.execute().fetchall()
        _list_channel_ids = list(map(lambda _row: _row[0], _list_channel_ids))
    else:
        raise ValueError(
            "[-]Either argument fp_list_channel_ids or table_name_videos must be set.")

    youtube_channels = YouTubeChannels(args)
    youtube_channels.set_list_channel_ids(_list_channel_ids).start()


def upload_rel_paper_video(table_name, fp_list_searches):
    with open(fp_list_searches, 'r') as f:
        _list_searches = json.load(f)

    num_responses = 0
    num_insert = 0
    num_pass = 0

    db_handler = DBHandler()

    for _response in _list_searches:
        if _response["items"]:
            num_responses += 1
            for _dict_item in _response["items"]:
                _dict = {"DOI": _response["idx_paper"],
                         "videoId": _dict_item["id"]["videoId"]}
                # Check if already exists
                db_handler.sql_handler.select(table_name, "idx").where(
                    "DOI", _dict["DOI"]).where("videoId", _dict["videoId"])
                _result = db_handler.execute().fetchall()
                print(_dict)
                if len(_result):
                    print("\t[+]Already exists. Passing...")
                    num_pass += 1
                    continue
                db_handler.sql_handler.insert(
                    table_name, dict_columns_values=_dict)
                db_handler.execute()
                num_insert += 1
    print("# responses: %d\t# insert: %d\t# pass: %d" %
          (num_responses, num_insert, num_pass))


def preprocess_scopus():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fpath')
    parser.add_argument('--overwrite', action="store_true", default="Err")
    parser.add_argument('--shuffle', action="store_true", default=False)
    args = parser.parse_args()

    from scopus_preprocessor import ScopusPreprocessor
    scopus_preprocessor = ScopusPreprocessor(
        args.fpath, overwrite=args.overwrite, shuffle=args.shuffle)
    scopus_preprocessor.preprocess_scopus_csv()


def test():
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
    # help='List of Channel IDs', default='fromdb')
    parser.add_argument(
        '--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    parser.add_argument(
        '--no-recursive', help='Call search API for a single time per query.', action='store_true', default=False)
    # parser.add_argument('--api-key', help='API key', default=api_key)

    # Search args
    parser.add_argument('--part', default='id')
    parser.add_argument('--eventType', default=None)
    parser.add_argument('--channelId', default=None)
    parser.add_argument('--forDeveloper', default=None)
    parser.add_argument('--videoSyndicated', default=None)
    parser.add_argument('--channelType', default=None)
    parser.add_argument('--videoCaption', default=None)
    parser.add_argument('--publishedAfter', default=None)
    parser.add_argument('--publishedBefore', default=None)
    parser.add_argument('--onBehalfOfContentOwner', default=None)
    parser.add_argument('--forContentOwner', default=None)
    parser.add_argument('--regionCode', default=None)
    parser.add_argument('--location', default=None)
    parser.add_argument('--locationRadius', default=None)
    parser.add_argument('--topicId', default=None)
    parser.add_argument('--videoDimension', default=None)
    parser.add_argument('--videoLicense', default=None)
    parser.add_argument('--maxResults', default=50)
    parser.add_argument('--videoType', default=None)
    parser.add_argument('--videoDefinition', default=None)
    parser.add_argument('--pageToken', default=None)
    parser.add_argument('--relatedToVideoId', default=None)
    parser.add_argument('--relevanceLanguage', default=None)
    parser.add_argument('--videoDuration', default=None)
    parser.add_argument('--forMine', default=None)
    parser.add_argument('--q', default='Google')
    parser.add_argument('--safeSearch', default=None)
    parser.add_argument('--videoEmbeddable', default=None)
    parser.add_argument('--videoCategoryId', default=None)
    parser.add_argument('--order', default=None)
    parser.add_argument(
        '--fields', default='nextPageToken, items(id(videoId))')

    args = vars(parser.parse_args())
    args["list_idx_papers"] = ["temp_idx_paper"]
    args["random_project"] = True
    youtube_search = YouTubeSearch(args)
    _list_responses = youtube_search.set_list_queries(
        ["scopus"]).start_search()
    # print(_list_responses)

    # with open('list_searches_doi_health_2014.txt', 'w+') as fp:
    #     json.dump(_list_responses, fp)
    return youtube_search


if __name__ == '__main__':
    # update_papers_from_arxiv_list()
    # altmetric_url_from_papers()
    # from search_custom import search_by_domains
    # _result = search_by_domains()

    # youtube_search = search_by_q("scopus/scopus_math+comp_top5perc_1804.csv", column="Redirection")

    # upload_rel_paper_video("rel_paper_video", "results/search/search_20200830_120323.txt")
    # youtube_videos = videos_by_video_ids("results/search/search_20200830_120323.txt")
    # update_videos_by_list_videos("scopus_videos_2018_comp", "./results/videos/videos_20200830_115854.txt", filter_by_q=True, overwrite=True)

    # upload_rel_paper_video("rel_paper_video", "results/search/search_%s.txt" % youtube_search.fname)
    # youtube_videos = videos_by_video_ids("results/search/search_%s.txt" % youtube_search.fname) # Accepts arg --random_project
    # update_videos_by_list_videos("scopus_videos", "./results/videos/videos_%s.txt" % youtube_videos.fname, filter_by_q=True, overwrite=True)
    # print("search_%s.txt" % youtube_search.fname)
    # print("videos_%s.txt" % youtube_videos.fname)

    # channels_by_list_channel_ids(table_name_videos="scopus_videos")
    # upload_channels_by_list_channels('channels', './results/channels/channels_20200730_083658.txt', overwrite=True)
    # num_of_videos()

    # test()
