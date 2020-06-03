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
from random import shuffle

from bs4 import BeautifulSoup
import re

from search_custom import YouTubeSearch
from videos import youtube_videos, filter_videos_by_viewcount, YouTubeVideos


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
    parser.add_argument('--fields', default='items(id(videoId), snippet(channelTitle))')

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


def altmetric_url_from_papers():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--table', help='Table of target papers')
    parser.add_argument('--overwrite', dest='overwrite',
                        help='Overwrite policy', action='store_true', default='incomplete')
    parser.add_argument('--driver', help='Driver', default='chrome')
    parser.add_argument('--p_driver', help='Driver path',
                        default='./chromedriver_83')
    parser.add_argument('--no_bookmarklet', help='Whether to install new bookmarklet or not', action='store_true', default=False)
    parser.add_argument('--max_times_find', type=int, help='Max times to find', default=5)
    parser.add_argument('--sec_sleep', type=float, help='Sleep seconds', default=1.0)

    parser.add_argument('--news', help='Set news as target', action='store_true', default=False)
    parser.add_argument('--blogs', help='Set blogs as target', action='store_true', default=False)
    parser.add_argument('--twitter', help='Set twitter as target', action='store_true', default=False)
    parser.add_argument('--wikipedia', help='Set wikipedia as target', action='store_true', default=False)
    parser.add_argument('--google', help='Set google as target', action='store_true', default=False)
    parser.add_argument('--reddit', help='Set reddit as target', action='store_true', default=False)
    parser.add_argument('--video', help='Set video as target', action='store_true', default=False)
    args = vars(parser.parse_args())
    # args = dict()
    # args['table'] = 'temp_papers'
    # args['overwrite']='incomplete'
    # args['driver']='chrome'
    # args['p_driver']='./chromedriver_83'
    # args['new_bookmarklet']=True
    # args['max_times_find']=5
    # args['sec_sleep']=1.0
    # args['news']=False
    # args['blogs']=False
    # args['twitter']=False
    # args['wikipedia']=False
    # args['google']=False
    # args['reddit']=False
    # args['video']=False

    # # Custom args
    # parser.add_argument('--f-channel-ids',
    #                     help='List of Channel IDs', default=None)

    # args = parser.parse_args()

    altmetric_it = AltmetricIt(args)
    altmetric_it.crawl_altmetric_from_papers(overwrite='incomplete')

    # Select urls from temp_papers
    # altmetric_it.db_handler.sql_handler.select(args['table'], 'urls')
    # _list_urls = altmetric_it.db_handler.execute().fetchall()
    # _list_urls = list(map(lambda _row: _row[0], _list_urls))

    # altmetric_it.crawl_altmetric_from_papers(overwrite='incompleted')
    # altmetric_it.update_results(overwrite='incompleted')

    # db_handler = DBHandler()
    # db_handler.sql_handler.select('papers', 'idx, urls')
    # sql = db_handler.sql_handler.get_sql()
    # db_handler.mycursor.execute(sql)
    # list_urls = db_handler.mycursor.fetchall()
    # # list_urls = list_urls[:2]
    # num_papers = len(list_urls)
    # list_failed = dict()
    # print('# of paper urls:', num_papers)

    # # Twitter
    # list_failed['twitter'] = list()
    # regex_abs = re.compile(r'https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
    # for i, field in enumerate(list_urls):
    #     print('Processing: %d out of %d papers' % (i+1, num_papers))
    #     _str_urls = field[1]
    #     _url_abs = regex_abs.findall(_str_urls)[0]
    #     _success = altmetric_it.get_twitter_from_url(
    #         _url_abs, overwrite='incompleted')
    #     if not _success:
    #         print('---------------Job failed: %s' % altmetric_it.msg_error)
    #         list_failed['twitter'].append({
    #             'idx': field[0],
    #             'url': _url_abs,
    #             'msg_error': altmetric_it.msg_error
    #         })
    #     else:
    #         print('---------------Job successful.')
    #         print('\n')

    # with open('./altmetricit/log_fail_%s.txt' % datetime.now().strftime('%Y%m%d_%H%M%S'), 'w+') as f:
    #     json.dump(list_failed, f)


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

def videos_by_video_ids():
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
                        # help='List of Channel IDs', default='fromdb')
    # parser.add_argument('--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
    # parser.add_argument('--api-key', help='API key', default=api_key)

    # Search args
    parser.add_argument('--part', default='id, snippet, contentDetails, statistics, liveStreamingDetails')
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

    args = vars(parser.parse_args())
    with open('./results/search/search_AI_with_videos.txt', 'r') as f:
        _list_searches = json.load(f)
        # _list_searches = json.load(f)[:2]
    youtube_videos = YouTubeVideos(args)
    return youtube_videos.set_list_searches(_list_searches).start()

def search_by_urls():
    parser = argparse.ArgumentParser()

    # Custom args
    # parser.add_argument('--list-channel-ids',
                        # help='List of Channel IDs', default='fromdb')
    parser.add_argument(
        '--up-to', help='Number of results queried up to. None indicates unlimited.', default=None)
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
    parser.add_argument('--fields', default='items(id(videoId))')

    args = vars(parser.parse_args())

    db_handler = DBHandler()
    # db_handler.sql_handler.select('temp_papers', ['idx', 'urls']).where('subject_1', 'Computer Science', '=').where('subject_2', 'Machine Learning', '=')
    db_handler.sql_handler.select('papers_cs.AI', ['idx', 'urls']).where('subject_1', 'Computer Science', '=').where('subject_2', 'Artificial Intelligence', '=')
    _results = db_handler.execute().fetchall()

    # https to http
    # preprocessor = Preprocessor()
    # preprocessor.url_https_to_http
    # _list_queries = list(map(lambda tup: tup[1].split(', ')[1], _results))
    # _list_queries = list(map(lambda tup: preprocessor.url_https_to_http(tup[1].split(', ')[0]), _results))
    _list_queries = list(map(lambda tup: tup[1].split(', ')[0][8:], _results)) # arxiv.org/...
    _list_idx_papers = list(map(lambda tup: tup[0], _results))
    args['list_idx_papers'] = _list_idx_papers

    # _list_queries = _list_queries[:2]
    # print(_list_queries)

    youtube_search = YouTubeSearch(args)
    youtube_search.set_list_queries(_list_queries)
    _list_responses = youtube_search.start_search()
    print(_list_responses)

    with open('list_cs_AI.txt', 'w+') as fp:
        json.dump(_list_responses, fp)

def update_videos_by_list_videos(table_name, fp_list_videos):
    db_videos_uploader = DBVideosUploader(table_name)
    with open(fp_list_videos, 'r') as f:
        _list_responses = json.load(f)
    # _list_responses = _list_responses[:1]
    db_videos_uploader.upload_videos(_list_responses)

def upload_channels_by_list_channels(table_name, fp_list_channels):
    db_channels_uploader = DBChannelsUploader(table_name)
    with open(fp_list_channels, 'r') as f:
        _list_responses = json.load(f)
    _list_responses[:1]
    db_channels_uploader.upload_channels(_list_responses)

def channels_by_list_channel_ids(table_name, fp_list_channel_ids):
    parser = argparse.ArgumentParser()
    parser.add_argument('--part', default='id, statistics, brandingSettings, snippet')
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
    
    with open(fp_list_channel_ids, 'r') as f:
        _list_channel_ids = json.load(f)
    youtube_channels = YouTubeChannels(args)
    youtube_channels.set_list_channel_ids(_list_channel_ids).start()




if __name__ == '__main__':
    # update_papers_from_arxiv_list()
    altmetric_url_from_papers()
    # search_by_urls()
    # videos_by_video_ids()
    # update_videos_by_list_videos('videos_cs.AI', './results/videos/videos_20200602_230922.txt')
    # channels_by_list_channel_ids('channels', './results/channels/list_channel_ids_AI.txt')
    # upload_channels_by_list_channels('channels', './results/channels/channels_20200602_233006.txt')