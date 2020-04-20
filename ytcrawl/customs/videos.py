"""
list(part, hl=None, maxWidth=None, locale=None, id=None, onBehalfOfContentOwner=None, regionCode=None,
     pageToken=None, maxResults=None, chart=None, myRating=None, maxHeight=None, videoCategoryId=None)

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

import preprocess_items

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


def youtube_videos(options):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

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
        # fields='items(snippet(channelTitle, tags, localized, title, defaultAudioLanguage, publishedAt, defaultLanguage, categoryId, channelId, thumbnails, description, liveBroadcastContent))
        # fields='items(statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount))'
        # fields='items(contentDetails(definition, dimension, projection, caption, licensedContent, duration))'
        # fields='items(snippet(channelTitle, description, publishedAt), statistics(viewCount, dislikeCount, commentCount, likeCount, favoriteCount))'
        fields=fields
    ).execute()

    # print(response.get('items', []))

    return response


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