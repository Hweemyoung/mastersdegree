"""
list(part, eventType=None, channelId=None, forDeveloper=None, videoSyndicated=None, channelType=None, videoCaption=None, publishedAfter=None, onBehalfOfContentOwner=None, forContentOwner=None, regionCode=None, location=None, locationRadius=None, type=None, topicId=None, publishedBefore=None,
	 videoDimension=None, videoLicense=None, maxResults=None, videoType=None, videoDefinition=None, pageToken=None, relatedToVideoId=None, relevanceLanguage=None, videoDuration=None, forMine=None, q=None, safeSearch=None, videoEmbeddable=None, videoCategoryId=None, order=None)
Returns a collection of search results that match the query parameters specified in the API request. By default, a search result set identifies matching video, channel, and playlist resources, but you can also configure queries to only retrieve a specific type of resource.

Args:
  part: string, The part parameter specifies a comma-separated list of one or more search resource properties that the API response will include. Set the parameter value to snippet. (required)
  eventType: string, The eventType parameter restricts a search to broadcast events. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  completed - Only include completed broadcasts.
	  live - Only include active broadcasts.
	  upcoming - Only include upcoming broadcasts.
  channelId: string, The channelId parameter indicates that the API response should only contain resources created by the channel
  forDeveloper: boolean, The forDeveloper parameter restricts the search to only retrieve videos uploaded via the developer's application or website. The API server uses the request's authorization credentials to identify the developer. Therefore, a developer can restrict results to videos uploaded through the developer's own app or website but not to videos uploaded through other apps or sites.
  videoSyndicated: string, The videoSyndicated parameter lets you to restrict a search to only videos that can be played outside youtube.com. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Return all videos, syndicated or not.
	  true - Only retrieve syndicated videos.
  channelType: string, The channelType parameter lets you restrict a search to a particular type of channel.
	Allowed values
	  any - Return all channels.
	  show - Only retrieve shows.
  videoCaption: string, The videoCaption parameter indicates whether the API should filter video search results based on whether they have captions. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Do not filter results based on caption availability.
	  closedCaption - Only include videos that have captions.
	  none - Only include videos that do not have captions.
  publishedAfter: string, The publishedAfter parameter indicates that the API response should only contain resources created after the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
  onBehalfOfContentOwner: string, Note: This parameter is intended exclusively for YouTube content partners.

The onBehalfOfContentOwner parameter indicates that the request's authorization credentials identify a YouTube CMS user who is acting on behalf of the content owner specified in the parameter value. This parameter is intended for YouTube content partners that own and manage many different YouTube channels. It allows content owners to authenticate once and get access to all their video and channel data, without having to provide authentication credentials for each individual channel. The CMS account that the user authenticates with must be linked to the specified YouTube content owner.
  forContentOwner: boolean, Note: This parameter is intended exclusively for YouTube content partners.

The forContentOwner parameter restricts the search to only retrieve resources owned by the content owner specified by the onBehalfOfContentOwner parameter. The user must be authenticated using a CMS account linked to the specified content owner and onBehalfOfContentOwner must be provided.
  regionCode: string, The regionCode parameter instructs the API to return search results for the specified country. The parameter value is an ISO 3166-1 alpha-2 country code.
  location: string, The location parameter, in conjunction with the locationRadius parameter, defines a circular geographic area and also restricts a search to videos that specify, in their metadata, a geographic location that falls within that area. The parameter value is a string that specifies latitude/longitude coordinates e.g. (37.42307,-122.08427).


- The location parameter value identifies the point at the center of the area.
- The locationRadius parameter specifies the maximum distance that the location associated with a video can be from that point for the video to still be included in the search results.The API returns an error if your request specifies a value for the location parameter but does not also specify a value for the locationRadius parameter.
  locationRadius: string, The locationRadius parameter, in conjunction with the location parameter, defines a circular geographic area.

The parameter value must be a floating point number followed by a measurement unit. Valid measurement units are m, km, ft, and mi. For example, valid parameter values include 1500m, 5km, 10000ft, and 0.75mi. The API does not support locationRadius parameter values larger than 1000 kilometers.

Note: See the definition of the location parameter for more information.
  type: string, The type parameter restricts a search query to only retrieve a particular type of resource. The value is a comma-separated list of resource types.
  topicId: string, The topicId parameter indicates that the API response should only contain resources associated with the specified topic. The value identifies a Freebase topic ID.
  publishedBefore: string, The publishedBefore parameter indicates that the API response should only contain resources created before the specified time. The value is an RFC 3339 formatted date-time value (1970-01-01T00:00:00Z).
  videoDimension: string, The videoDimension parameter lets you restrict a search to only retrieve 2D or 3D videos. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  2d - Restrict search results to exclude 3D videos.
	  3d - Restrict search results to only include 3D videos.
	  any - Include both 3D and non-3D videos in returned results. This is the default value.
  videoLicense: string, The videoLicense parameter filters search results to only include videos with a particular license. YouTube lets video uploaders choose to attach either the Creative Commons license or the standard YouTube license to each of their videos. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Return all videos, regardless of which license they have, that match the query parameters.
	  creativeCommon - Only return videos that have a Creative Commons license. Users can reuse videos with this license in other videos that they create. Learn more.
	  youtube - Only return videos that have the standard YouTube license.
  maxResults: integer, The maxResults parameter specifies the maximum number of items that should be returned in the result set.
  videoType: string, The videoType parameter lets you restrict a search to a particular type of videos. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Return all videos.
	  episode - Only retrieve episodes of shows.
	  movie - Only retrieve movies.
  videoDefinition: string, The videoDefinition parameter lets you restrict a search to only include either high definition (HD) or standard definition (SD) videos. HD videos are available for playback in at least 720p, though higher resolutions, like 1080p, might also be available. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Return all videos, regardless of their resolution.
	  high - Only retrieve HD videos.
	  standard - Only retrieve videos in standard definition.
  pageToken: string, The pageToken parameter identifies a specific page in the result set that should be returned. In an API response, the nextPageToken and prevPageToken properties identify other pages that could be retrieved.
  relatedToVideoId: string, The relatedToVideoId parameter retrieves a list of videos that are related to the video that the parameter value identifies. The parameter value must be set to a YouTube video ID and, if you are using this parameter, the type parameter must be set to video.
  relevanceLanguage: string, The relevanceLanguage parameter instructs the API to return search results that are most relevant to the specified language. The parameter value is typically an ISO 639-1 two-letter language code. However, you should use the values zh-Hans for simplified Chinese and zh-Hant for traditional Chinese. Please note that results in other languages will still be returned if they are highly relevant to the search query term.
  videoDuration: string, The videoDuration parameter filters video search results based on their duration. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Do not filter video search results based on their duration. This is the default value.
	  long - Only include videos longer than 20 minutes.
	  medium - Only include videos that are between four and 20 minutes long (inclusive).
	  short - Only include videos that are less than four minutes long.
  forMine: boolean, The forMine parameter restricts the search to only retrieve videos owned by the authenticated user. If you set this parameter to true, then the type parameter's value must also be set to video.
  q: string, The q parameter specifies the query term to search for.

Your request can also use the Boolean NOT (-) and OR (|) operators to exclude videos or to find videos that are associated with one of several search terms. For example, to search for videos matching either "boating" or "sailing", set the q parameter value to boating|sailing. Similarly, to search for videos matching either "boating" or "sailing" but not "fishing", set the q parameter value to boating|sailing -fishing. Note that the pipe character must be URL-escaped when it is sent in your API request. The URL-escaped value for the pipe character is %7C.
  safeSearch: string, The safeSearch parameter indicates whether the search results should include restricted content as well as standard content.
	Allowed values
	  moderate - YouTube will filter some content from search results and, at the least, will filter content that is restricted in your locale. Based on their content, search results could be removed from search results or demoted in search results. This is the default parameter value.
	  none - YouTube will not filter the search result set.
	  strict - YouTube will try to exclude all restricted content from the search result set. Based on their content, search results could be removed from search results or demoted in search results.
  videoEmbeddable: string, The videoEmbeddable parameter lets you to restrict a search to only videos that can be embedded into a webpage. If you specify a value for this parameter, you must also set the type parameter's value to video.
	Allowed values
	  any - Return all videos, embeddable or not.
	  true - Only retrieve embeddable videos.
  videoCategoryId: string, The videoCategoryId parameter filters video search results based on their category. If you specify a value for this parameter, you must also set the type parameter's value to video.
  order: string, The order parameter specifies the method that will be used to order resources in the API response.
	Allowed values
	  date - Resources are sorted in reverse chronological order based on the date they were created.
	  rating - Resources are sorted from highest to lowest rating.
	  relevance - Resources are sorted based on their relevance to the search query. This is the default value for this parameter.
	  title - Resources are sorted alphabetically by title.
	  videoCount - Channels are sorted in descending order of their number of uploaded videos.
	  viewCount - Resources are sorted from highest to lowest number of views.

Returns:
  An object of the form:

	{
	# Serialized EventId of the request which produced this response.
	"eventId": "A String",
	# The token that can be used as the value of the pageToken parameter to retrieve the next page in the result set.
	"nextPageToken": "A String",
	# Identifies what kind of resource this is. Value: the fixed string "youtube#searchListResponse".
	"kind": "youtube#searchListResponse",
	"visitorId": "A String", # The visitorId identifies the visitor.
	"items": [ # A list of results that match the search criteria.
	  { # A search result contains information about a YouTube video, channel, or playlist that matches the search parameters specified in an API request. While a search result points to a uniquely identifiable resource, like a video, it does not have its own persistent data.
		"snippet": { # Basic details about a search result, including title, description and thumbnails of the item referenced by the search result. # The snippet object contains basic details about a search result, such as its title or description. For example, if the search result is a video, then the title will be the video's title and the description will be the video's description.
		  "thumbnails": { # Internal representation of thumbnails for a YouTube resource. # A map of thumbnail images associated with the search result. For each object in the map, the key is the name of the thumbnail image, and the value is an object that contains other information about the thumbnail.
			"default": { # A thumbnail is an image representing a YouTube resource. # The default image for this resource.
			  "url": "A String", # The thumbnail image's URL.
			  "width": 42, # (Optional) Width of the thumbnail image.
			  "height": 42, # (Optional) Height of the thumbnail image.
			},
			"high": { # A thumbnail is an image representing a YouTube resource. # The high quality image for this resource.
			  "url": "A String", # The thumbnail image's URL.
			  "width": 42, # (Optional) Width of the thumbnail image.
			  "height": 42, # (Optional) Height of the thumbnail image.
			},
			"medium": { # A thumbnail is an image representing a YouTube resource. # The medium quality image for this resource.
			  "url": "A String", # The thumbnail image's URL.
			  "width": 42, # (Optional) Width of the thumbnail image.
			  "height": 42, # (Optional) Height of the thumbnail image.
			},
			"maxres": { # A thumbnail is an image representing a YouTube resource. # The maximum resolution quality image for this resource.
			  "url": "A String", # The thumbnail image's URL.
			  "width": 42, # (Optional) Width of the thumbnail image.
			  "height": 42, # (Optional) Height of the thumbnail image.
			},
			"standard": { # A thumbnail is an image representing a YouTube resource. # The standard quality image for this resource.
			  "url": "A String", # The thumbnail image's URL.
			  "width": 42, # (Optional) Width of the thumbnail image.
			  "height": 42, # (Optional) Height of the thumbnail image.
			},
		  },
		  "title": "A String", # The title of the search result.
		  # The value that YouTube uses to uniquely identify the channel that published the resource that the search result identifies.
		  "channelId": "A String",
		  # The creation date and time of the resource that the search result identifies. The value is specified in ISO 8601 (YYYY-MM-DDThh:mm:ss.sZ) format.
		  "publishedAt": "A String",
		  # It indicates if the resource (video or channel) has upcoming/active live broadcast content. Or it's "none" if there is not any upcoming/active live broadcasts.
		  "liveBroadcastContent": "A String",
		  # The title of the channel that published the resource that the search result identifies.
		  "channelTitle": "A String",
		  "description": "A String", # A description of the search result.
		},
		# Identifies what kind of resource this is. Value: the fixed string "youtube#searchResult".
		"kind": "youtube#searchResult",
		"etag": "A String", # Etag of this resource.
		"id": { # A resource id is a generic reference that points to another YouTube resource. # The id object contains information that can be used to uniquely identify the resource that matches the search request.
		  "kind": "A String", # The type of the API resource.
		  # The ID that YouTube uses to uniquely identify the referred resource, if that resource is a channel. This property is only present if the resourceId.kind value is youtube#channel.
		  "channelId": "A String",
		  # The ID that YouTube uses to uniquely identify the referred resource, if that resource is a playlist. This property is only present if the resourceId.kind value is youtube#playlist.
		  "playlistId": "A String",
		  # The ID that YouTube uses to uniquely identify the referred resource, if that resource is a video. This property is only present if the resourceId.kind value is youtube#video.
		  "videoId": "A String",
		},
	  },
	],
	"tokenPagination": { # Stub token pagination template to suppress results.
	},
	"regionCode": "A String",
	"etag": "A String", # Etag of this resource.
	# The token that can be used as the value of the pageToken parameter to retrieve the previous page in the result set.
	"prevPageToken": "A String",
	"pageInfo": { # Paging details for lists of resources, including total number of items available and number of resources returned in a single page.
	  "totalResults": 42, # The total number of results in the result set.
	  # The number of results included in the API response.
	  "resultsPerPage": 42,
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
from db_handler import DBHandler
from youtube import YouTube

from datetime import datetime
import json
import os

# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = 'AIzaSyCVMEUGxxsSw-BKH4c06PHKr_F4qjSdwJw'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YouTubeSearch(YouTube):
	args = {
		'part': None,
		'eventType': None,
		'channelId': None,
		'forDeveloper': None,
		'videoSyndicated': None,
		'channelType': None,
		'videoCaption': None,
		'publishedAfter': None,
		'publishedBefore': None,
		'onBehalfOfContentOwner': None,
		'forContentOwner': None,
		'regionCode': None,
		'location': None,
		'locationRadius': None,
		'topicId': None,
		'videoDimension': None,
		'videoLicense': None,
		'maxResults': None,
		'videoType': None,
		'videoDefinition': None,
		'pageToken': None,
		'relatedToVideoId': None,
		'relevanceLanguage': None,
		'videoDuration': None,
		'forMine': None,
		'q': None,
		'safeSearch': None,
		'videoEmbeddable': None,
		'videoCategoryId': None,
		'order': None,
		'fields': None
	}

	def __init__(self, args, method_name='search'):
		super(YouTubeSearch, self).__init__(args, method_name)

	def set_list_channel_ids(self, list_channel_ids):
		self.list_channel_ids = list_channel_ids
		return self

	def set_list_queries(self, list_queries):
		self.list_queries = list_queries
		return self

	def start_search(self, args=None, list_queries=None, list_channel_ids=None, recursive=True):
		if args == None:
			args = self.args
		if list_queries == None:
			list_queries = self.list_queries
		if list_channel_ids == None:
			# Empty list
			list_channel_ids = list()
		if 'no_recursive' in args:
			recursive = not args['no_recursive']
		_list_responses = self.__search(args, list_queries, list_channel_ids, recursive)
		self.save_task(_list_responses, args)
		return _list_responses

	def __search(self, args, list_queries=None, list_channel_ids=None, recursive=True):
		# q(, channelId) must be already set when list_queries == None
		_list_responses = list()
		if list_queries:
			_num_queries = len(list_queries)
			print('# of queries: ', _num_queries)
			# Per query
			for i, _q in enumerate(list_queries):
				print('Processing %d out of %d queries' % (i+1, _num_queries))
				args['q'] = _q
				
				# args['idx_paper'] = args['list_idx_papers'][i]

				if list_channel_ids:
					_num_channel_ids = len(list_channel_ids)
					for j, _channel_id in enumerate(list_channel_ids):
						print('\tQuery from %d out of %d channels.' %
							  (j+1, _num_channel_ids))
						args['channelId'] = _channel_id
						self.list_responses.append(
							self.__youtube_search_recursive(args, recursive))
				else:
					self.list_responses.append(
						self.__youtube_search_recursive(args, recursive))

		elif 'q' in args.keys():
			# q must be already set in args
			self.list_responses.append(self.__youtube_search_recursive(args, recursive))
		else:
			raise KeyError('q not given')
		return self.list_responses

	def __youtube_search_recursive(self, args, recursive=True):
		# For single q (+single channelId)
		# args['pageToken'] = None
		# print('Initial args:', args)
		print('q: ', args['q'])

		_dict_responses = dict()
		_dict_responses['q'] = args['q']
		_dict_responses['publishedAfter'] = args['publishedAfter']
		_dict_responses['publishedBefore'] = args['publishedBefore']
		# _dict_responses['idx_paper'] = args['idx_paper']
		_dict_responses['items'] = list()
		_dict_responses['totalResults'] = list()

		_page = 0
		# _response = self.__youtube_search(args)
		# _dict_responses['items'] += _response['items'][0]
		# while len(_response.get('items', [])) != 0:
		while True:
			_no_remain = False
			print('\tPage: %d' % (_page + 1))
			if args['up_to'] != None:  # Not None
				# Save quota by querying least amount required
				if int(args['up_to']) < int(args['maxResults']):
					args['maxResults'] = args['up_to']
				_remains = int(args['up_to']) - int(args['maxResults'])
				print('\tRemains: %d' % _remains)
				if _remains > 0:
					args['up_to'] = str(_remains)
				elif _no_remain:
					break
				else:
					_no_remain = True

			# Get response
			_response = False
			while _response == False:
				_response = self.__youtube_search(args)

			_dict_responses['items'].append(_response['items'])
			_dict_responses['totalResults'].append(_response['pageInfo']['totalResults'])

			if not recursive:
				break
			# Next page token
			_next_page_token = _response.get('nextPageToken')
			if _next_page_token == None:
				print('\tNo page token. Break.')
				break
			args['pageToken'] = _next_page_token
			_page += 1

		return _dict_responses

	def __youtube_search(self, options):
		# Call the search.list method to retrieve results matching the specified
		# query term.
		try:
			_response = self.youtube.search().list(
				part=options['part'],
				eventType=options['eventType'],
				channelId=options['channelId'],
				forDeveloper=options['forDeveloper'],
				videoSyndicated=options['videoSyndicated'],
				channelType=options['channelType'],
				videoCaption=options['videoCaption'],
				publishedAfter=options['publishedAfter'],
				publishedBefore=options['publishedBefore'],
				onBehalfOfContentOwner=options['onBehalfOfContentOwner'],
				forContentOwner=options['forContentOwner'],
				regionCode=options['regionCode'],
				location=options['location'],
				locationRadius=options['locationRadius'],
				type='video',
				topicId=options['topicId'],
				videoDimension=options['videoDimension'],
				videoLicense=options['videoLicense'],
				maxResults=options['maxResults'],
				videoType=options['videoType'],
				videoDefinition=options['videoDefinition'],
				pageToken=options['pageToken'],
				relatedToVideoId=options['relatedToVideoId'],
				relevanceLanguage=options['relevanceLanguage'],
				videoDuration=options['videoDuration'],
				forMine=options['forMine'],
				q=options['q'],
				safeSearch=options['safeSearch'],
				videoEmbeddable=options['videoEmbeddable'],
				videoCategoryId=options['videoCategoryId'],
				order=options['order'],
				fields=options['fields']
			).execute()
		except HttpError as e:  # Quota exceeded
			print(e)
			print('Rebuilding youtube with new api key.')
			self.build_youtube()
			_response = False

		# Add each result to the appropriate list, and then display the lists of
		# matching videos, channels, and playlists.
		# print(_response.get('items', []))
		# for result in _response.get('items', []):
		#     print('\nChannel title:', result['snippet']['channelTitle'], '\nTitle: ',
		#           result['snippet']['title'], '\nDescription: ', result['snippet']['description'])
		return _response
