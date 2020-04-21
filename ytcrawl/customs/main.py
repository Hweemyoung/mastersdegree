import argparse, os, json

from search_custom import youtube_search_recursive
from videos import youtube_videos
from db_videos_uploader import DBVideosUploader

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--q', help='Search term', default='Google')
    parser.add_argument('--max-results', help='Max results', default=50)
    parser.add_argument('--region-code', help='Region code', default=None)
    parser.add_argument('--page-token', help='Page token', default=None)
    parser.add_argument('--order', help='Order', default=None)
    parser.add_argument('--channelId', help='Channel ID', default=None)
    parser.add_argument('--f-channel-ids', help='List of Channel IDs', default=None)

    args = parser.parse_args()

    # try:
    #     youtube_search(args)
    # except (HttpError, e):
    #     print('An HTTP error %d occurred:\n%s' % (e.resp.status, e.content))
    dict_video_ids = youtube_search_recursive(args)

    # From dict to list
    list_video_ids = []
    for item in dict_video_ids['items']:
        list_video_ids.append(item['id']['videoId'])
    
    # Video uploader
    db_videos_uploader = DBVideosUploader()

    # For every video id
    for video_id in list_video_ids:

        # Check if video already exists in DB
        if db_videos_uploader.video_id_exists(video_id):
            continue

        args.video_id = video_id

        # Get data through API
        response = youtube_videos(args)

        # with open(os.path.join('./results/videos', args.video_id + '.txt'), 'w') as new_json:
        #     json.dump(response.get('items', []), new_json)
        items = response.get('items', [])[0]
        print('\nItems from youtube_video:', items)

        db_videos_uploader.insert_into_videos(args, items)
    
    # Close DB connection
    db_videos_uploader.close()
    