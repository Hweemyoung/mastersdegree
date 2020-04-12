"""
list(part, regionCode=None, hl=None, id=None)
Returns a list of categories that can be associated with YouTube videos.

Args:
  part: string, The part parameter specifies the videoCategory resource properties that the API response will include. Set the parameter value to snippet. (required)
  regionCode: string, The regionCode parameter instructs the API to return the list of video categories available in the specified country. The parameter value is an ISO 3166-1 alpha-2 country code.
  hl: string, The hl parameter specifies the language that should be used for text values in the API response.
  id: string, The id parameter specifies a comma-separated list of video category IDs for the resources that you are retrieving.

Returns:
  An object of the form:

    {
    "eventId": "A String", # Serialized EventId of the request which produced this response.
    "nextPageToken": "A String", # The token that can be used as the value of the pageToken parameter to retrieve the next page in the result set.
    "kind": "youtube#videoCategoryListResponse", # Identifies what kind of resource this is. Value: the fixed string "youtube#videoCategoryListResponse".
    "visitorId": "A String", # The visitorId identifies the visitor.
    "items": [ # A list of video categories that can be associated with YouTube videos. In this map, the video category ID is the map key, and its value is the corresponding videoCategory resource.
      { # A videoCategory resource identifies a category that has been or could be associated with uploaded videos.
        "snippet": { # Basic details about a video category, such as its localized title. # The snippet object contains basic details about the video category, including its title.
          "assignable": True or False,
          "channelId": "UCBR8-60-B28hp2BmDPdntcQ", # The YouTube channel that created the video category.
          "title": "A String", # The video category's title.
        },
        "kind": "youtube#videoCategory", # Identifies what kind of resource this is. Value: the fixed string "youtube#videoCategory".
        "etag": "A String", # Etag of this resource.
        "id": "A String", # The ID that YouTube uses to uniquely identify the video category.
      },
    ],
    "tokenPagination": { # Stub token pagination template to suppress results.
    },
    "etag": "A String", # Etag of this resource.
    "prevPageToken": "A String", # The token that can be used as the value of the pageToken parameter to retrieve the previous page in the result set.
    "pageInfo": { # Paging details for lists of resources, including total number of items available and number of resources returned in a single page.
      "totalResults": 42, # The total number of results in the result set.
      "resultsPerPage": 42, # The number of results included in the API response.
    },
  }
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


def youtube_video_categories(options):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    response = youtube.videoCategories().list(
        part='id, snippet',
        regionCode=options.region_code,
        hl=None,
        id=None,
        fields='items(id,snippet(title))'
    ).execute()

    print(response.get('items', []))
    return
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--region-code', help='Region code', default=None)
    args = parser.parse_args()

    # try:
    #     youtube_video_categories(args)
    # except (HttpError, e):
    #     print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

    youtube_video_categories(args)
