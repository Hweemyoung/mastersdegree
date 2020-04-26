from preprocessor import Preprocessor
from db_channels_uploader import DBChannelsUploader
from db_videos_uploader import DBVideosUploader

if __name__ == '__main__':
    # db_videos = DBVideosUploader()
    # db_videos.update_duration()
    # preprocessor = Preprocessor()
    # duration = 'PT1M46S'
    # timedelta = preprocessor.preprocess_duration(duration)
    # print(timedelta)
    # a = {'seconds': '46', 'minutes': '1', 'hours': None}
    # for i in a.__iter__():
    #     print(i)
    db_videos_uploader = DBVideosUploader()    

    sql = "SELECT channelId FROM channels;"
    db_videos_uploader.mycursor.execute(sql)
    list_channel_ids = db_videos_uploader.mycursor.fetchall()
    print(list_channel_ids, '\n', len(list_channel_ids))
    print(list_channel_ids[0][0])