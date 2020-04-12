"""
list(part, regionCode=None, hl=None, id=None)
Returns a list of categories that can be associated with YouTube channels.

Args:
  part: string, The part parameter specifies the guideCategory resource properties that the API response will include. Set the parameter value to snippet. (required)
  regionCode: string, The regionCode parameter instructs the API to return the list of guide categories available in the specified country. The parameter value is an ISO 3166-1 alpha-2 country code.
  hl: string, The hl parameter specifies the language that will be used for text values in the API response.
  id: string, The id parameter specifies a comma-separated list of the YouTube channel category ID(s) for the resource(s) that are being retrieved. In a guideCategory resource, the id property specifies the YouTube channel category ID.

Returns:
  An object of the form:

    {
    "eventId": "A String", # Serialized EventId of the request which produced this response.
    "nextPageToken": "A String", # The token that can be used as the value of the pageToken parameter to retrieve the next page in the result set.
    "kind": "youtube#guideCategoryListResponse", # Identifies what kind of resource this is. Value: the fixed string "youtube#guideCategoryListResponse".
    "visitorId": "A String", # The visitorId identifies the visitor.
    "items": [ # A list of categories that can be associated with YouTube channels. In this map, the category ID is the map key, and its value is the corresponding guideCategory resource.
      { # A guideCategory resource identifies a category that YouTube algorithmically assigns based on a channel's content or other indicators, such as the channel's popularity. The list is similar to video categories, with the difference being that a video's uploader can assign a video category but only YouTube can assign a channel category.
        "snippet": { # Basic details about a guide category. # The snippet object contains basic details about the category, such as its title.
          "channelId": "UCBR8-60-B28hp2BmDPdntcQ",
          "title": "A String", # Description of the guide category.
        },
        "kind": "youtube#guideCategory", # Identifies what kind of resource this is. Value: the fixed string "youtube#guideCategory".
        "etag": "A String", # Etag of this resource.
        "id": "A String", # The ID that YouTube uses to uniquely identify the guide category.
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


def youtube_guide_categories(options):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    # search_response = youtube.search().list(
    #     q=options.q,
    #     part='id,snippet',
    #     maxResults=options.max_results
    # ).execute()

    search_response = youtube.guideCategories().list(
        part='id, snippet',
        regionCode=options.region_code,
        hl=None,
        id=None,
        fields='items(id,snippet(title))'
    ).execute()
    
    videos=[]
    channels=[]
    playlists=[]

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    # print(search_response.get('items', []))
    print(search_response)
    return
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append('%s (%s)' % (search_result['snippet']['title'],
                                       search_result['id']['videoId']))
        elif search_result['id']['kind'] == 'youtube#channel':
            channels.append('%s (%s)' % (search_result['snippet']['title'],
                                         search_result['id']['channelId']))
        elif search_result['id']['kind'] == 'youtube#playlist':
            playlists.append('%s (%s)' % (search_result['snippet']['title'],
                                          search_result['id']['playlistId']))

    print('Videos:\n', '\n'.join(videos), '\n')
    print('Channels:\n', '\n'.join(channels), '\n')
    print('Playlists:\n', '\n'.join(playlists), '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--region-code', help='Region code', default=None)
    args = parser.parse_args()

    # try:
    #     youtube_guide_categories(args)
    # except (HttpError, e):
    #     print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))

    youtube_guide_categories(args)
