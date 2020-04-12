"""
list(part, hl=None, maxWidth=None, locale=None, id=None, onBehalfOfContentOwner=None, regionCode=None, pageToken=None, maxResults=None, chart=None, myRating=None, maxHeight=None, videoCategoryId=None)

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

    response = youtube.videos().list(
        part='id, snippet',
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
        # fields='items(snippet(channelTitle, tags, localized, title, defaultAudioLanguage, publishedAt, defaultLanguage, categoryId, channelId, thumbnails, description, liveBroadcastContent), kind, id, etag)'
        fields='items(snippet(description))'
    ).execute()

    # print(response.get('items', []))
    for result in response.get('items', []):
        print(result['snippet']['description'])
    return
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-results', help='Max results', default=25)
    parser.add_argument('--region-code', help='Region code', default=None)
    parser.add_argument('--video-id', help='Video ID')
    args = parser.parse_args()

    # try:
    #     youtube_videos(args)
    # except (HttpError, e):
    #     print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

    youtube_videos(args)
