"""
list(
part,
hl=None,
maxWidth=None,
locale=None,
id=None,
onBehalfOfContentOwner=None,
regionCode=None,
pageToken=None,
maxResults=None,
chart=None,
myRating=None,
maxHeight=None,
videoCategoryId=None)

Returns a list of videos that match the API request parameters.

"""

#!/usr/bin/python

# This sample executes a search request for the specified search term.
# Sample usage:
#   python search.py --q=surfing --max-results=10
# NOTE: To use the sample, you must provide a developer key obtained
#       in the Google APIs Console. Search for "REPLACE_ME" in this code
#       to find the correct place to provide that key..

import argparse
import os
import json
import mysql.connector
from youtube import YouTube


from datetime import datetime
from db_videos_uploader import DBVideosUploader
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = 'AIzaSyCVMEUGxxsSw-BKH4c06PHKr_F4qjSdwJw'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YouTubeVideos(YouTube):
    args = {
        'part': 'id, snippet, contentDetails, statistics, liveStreamingDetails',
        'hl': None,
        'maxWidth': None,
        'locale': None,
        'id': None,
        'onBehalfOfContentOwner': None,
        'regionCode': None,
        'pageToken': None,
        'maxResults': None,
        'chart': None,
        'myRating': None,
        'maxHeight': None,
        'videoCategoryId': None,
        'fields': 'items(id, snippet(title, publishedAt, description, tags, defaultLanguage, defaultAudioLanguage, channelTitle, channelId), contentDetails(duration), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount), liveStreamingDetails)'
    }

    def __init__(self, args, method_name='videos'):
        super(YouTubeVideos, self).__init__(args, method_name)

    def set_list_video_ids(self, list_video_ids):
        self.list_video_ids = list_video_ids
        return self

    def start_search(self, args=None, list_video_ids=None):
        if args == None:
            args = self.args
        if list_video_ids == None:
            list_video_ids = self.list_video_ids
        _list_responses = self.__search(args, list_video_ids)
        self.save_task(_list_responses, args)
        return _list_responses

    def __search(self, args, list_video_ids=None):
        _list_responses = list()
        if list_video_ids:
            _num_video_ids = len(list_video_ids)
            print('# of video IDs: ', _num_video_ids)
            for i, _video_id in enumerate(list_video_ids):
                print('Processing %d out of %d video IDs' %
                      (i+1, _num_video_ids))
                args['id'] = _video_id

                args['idx_paper'] = args['list_idx_papers'][i]

                self.list_responses.append(self.__youtube_videos(args))

        elif 'id' in args.keys():
            # q must be already set in args
            self.list_responses.append(self.__youtube_videos(args))
        else:
            raise KeyError('Video ID not given')
        return self.list_responses
    
    def __youtube_videos(self, options):
        print('Video ID: ', args['id'])
        try:
            _response = self.youtube.videos().list(
                part=options['part'],
                hl=options['hl'],
                maxWidth=options['maxWidth'],
                locale=options['locale'],
                id=options['id'],
                onBehalfOfContentOwner=options['onBehalfOfContentOwner'],
                regionCode=options['regionCode'],
                pageToken=options['pageToken'],
                maxResults=options['maxResults'],
                chart=options['chart'],
                myRating=options['myRating'],
                maxHeight=options['maxHeight'],
                videoCategoryId=options['videoCategoryId'],
                fields=options['fields']
            ).execute()
        except HttpError as e:  # Quota exceeded
            print(e)
            print('Rebuilding youtube with new api key.')
            self.build_youtube()
            _response = False
        
        return _response



def youtube_videos(options):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=options.api_key if options.api_key else DEVELOPER_KEY)

    fields = 'items(snippet(channelTitle, tags, title, defaultAudioLanguage, publishedAt, defaultLanguage, channelId, description), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount), contentDetails(duration))'
    response = youtube.videos().list(
        part='snippet, statistics, contentDetails',
        hl=None,
        maxWidth=None,
        locale=None,
        id=options.video_id,
        onBehalfOfContentOwner=None,
        regionCode=options.region_code,
        pageToken=None,
        maxResults=options.max_results,
        chart=None,
        myRating=None,
        maxHeight=None,
        videoCategoryId=None,
        # fields='items(id)'
        # fields='items(snippet(channelTitle, tags, localized, title, defaultAudioLanguage, publishedAt, defaultLanguage, categoryId, channelId, thumbnails, description, liveBroadcastContent))'
        # fields='items(statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount))'
        # fields='items(contentDetails(definition, dimension, projection, caption, licensedContent, duration))'
        # fields='items(snippet(channelTitle, description, publishedAt), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount))'
        fields=options.fields
        'snippet(title, publishedAt, description, tags, defaultLanguage, defaultAudioLanguage, channelTitle, channelId), contentDetails(duration), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount), liveStreamingDetails'
    ).execute()

    # print(response.get('items', []))

    return response


def filter_videos_by_viewcount(args, items):
    # items == youtube_search_recursive()['items']
    print('Filtering with viewCount.\nBefore:', len(items))
    filtered_items = list()
    for item in items:
        args.video_id = item['id']['videoId']
        args.part = 'statistics'
        args.fields = 'items(statistics(viewCount))'
        response = youtube_videos(args)
        video_item = response.get('items', [])[0]
        if int(video_item['statistics']['viewCount']) > int(args.view_over):
            filtered_items.append(item)
    # Replace items to filtered
    print('After:', len(filtered_items))
    return filtered_items


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-results', help='Max results', default=25)
    parser.add_argument('--region-code', help='Region code', default=None)
    parser.add_argument('--video-id', help='Video ID', default=None)
    # parser.add_argument('--q', help='Query', default=None)
    args = parser.parse_args()

    # folder = './results/pdf'
    # for fname in os.listdir(folder):
    #     with open(os.path.join(folder, fname)) as f:
    #         items_list = json.load(f)['items']
    #     for item in items_list:
    #         videoId = item['id']['videoId']
    #         args.video_id = videoId

    #         response = youtube_videos(args)

    #         for result in response.get('items', []):
    #             print(result['snippet']['description'])

    # try:
    #     youtube_videos(args)
    # except (HttpError, e):
    #     print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

    list_video_ids = []
    for video_id in list_video_ids:
        args.video_id = video_id

        response = youtube_videos(args)
        print(response)
        with open(os.path.join('./results/videos', args.video_id + '.txt'), 'w') as new_json:
            json.dump(response.get('items', []), new_json)
        items = response.get('items')
        print(items)

        db_videos_uploader = DBVideosUploader()
        db_videos_uploader.insert_into_videos(args, items)
