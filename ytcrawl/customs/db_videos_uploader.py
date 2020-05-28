from db_handler import DBHandler
from preprocessor import Preprocessor
from datetime import datetime
from selenium import webdriver


class DBVideosUploader:
    preprocessor = Preprocessor()
    db_handler = DBHandler()

    def __init__(self, table_name):
        self.table_name = table_name

    def q_exists(self, video_id, q):
        sql = "SELECT `q` FROM videos WHERE `videoId`='%s' AND match(q) against('\"%s\"' in boolean mode);" % (
            video_id, q)
        self.mycursor.execute(sql)
        result = self.mycursor.fetchall()
        exists = len(result) != 0
        if exists:
            print('\nq already exists:', q)
        else:
            print('\nq not exist:', q)
            self.__update_q(video_id, q)

        return exists

    def __update_q(self, video_id, new_q):
        self.db_handler.sql_handler.select(
            self.table_name, ['idx', 'q']).where('videoId', video_id)
        result = self.db_handler.execute().fetchall()
        # sql = "SELECT `q` FROM videos WHERE `videoId`='%s';" % video_id
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        idx = result[0][0]
        old_q = result[0][1] if len(result) else ''
        print('Updating q to:', old_q + ', %s' % new_q)
        self.db_handler.sql_handler.update(self.table_name, dict_columns_values={
                                           'q': old_q + ', ' + new_q}).where('idx', idx)
        self.db_handler.execute()

        # sql = "UPDATE videos SET q='%s' WHERE videoId='%s';" % (
        # old_q + ', %s' % new_q, video_id)
        # self.mycursor.execute(sql)
        # self.conn.commit()

    def __video_id_exists(self, video_id):
        self.db_handler.sql_handler.select(
            self.table_name, 1).where('videoId', video_id, '=')
        result = self.db_handler.execute().fetchall()

        # sql = "SELECT 1 FROM videos WHERE videos.videoId='%s';" % (video_id)
        # print('\nsql:', sql)
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        exists = len(result) != 0
        # if exists:
        #     print('\tVideo already exists:', video_id)
        #     if args.q:
        #         self.q_exists(video_id, args.q)

        return exists

    def upload_videos(self, list_responses):
        _num_videos = len(list_responses)
        for i, _dict_response in enumerate(list_responses):
            print('Processing %d out of %d videos' % (i+1, _num_videos))
            self.__upload_video(_dict_response)

    def __upload_video(self, _dict_response):
        _video_id = _dict_response['items']['id']
        # liveStreaming: set True if exists
        if 'liveStreamingDetails' in _dict_response['items'].keys():
            _dict_response['items']['liveStreamingDetails'] = 1

        # Check if video already exists by videoID
        if self.__video_id_exists(_video_id):
            print('\tVideo already exists:', _video_id)
            self.__update_q_if_not_exist(_video_id, _dict_response['q'])
            self.__update_idx_paper_if_not_exist(_video_id, _dict_response['idx_paper'])

        # Preprocess
        items = self.preprocessor.preprocess(_video_id)
        custom_fields = {
            'q': _dict_response['q'], 'idx_paper': _dict_response['idx_paper']}

        # Get columns, values
        columns, values = self.db_handler.get_columns_values(
            items, custom_fields)

        # Wrap columns
        # columns = self.preprocessor.wrap_columns(columns)

        values = tuple(values)

        self.db_handler.sql_handler.insert(
            self.table_name, columns=columns, values=values)
        
    def __update_idx_paper_if_not_exist(self, video_id, idx_paper):
        pass

    def __update_q_if_not_exist(self, video_id, q):
        # Check if q exists
        self.db_handler.sql_handler.select(self.table_name, 'q').where(
            'videoId', video_id, '=').where('q', q, 'fulltext_list')
        result = self.db_handler.execute().fetchall()
        # sql = "SELECT `q` FROM videos WHERE `videoId`='%s' AND match(q) against('\"%s\"' in boolean mode);" % (
        # video_id, q)
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        exists = len(result) != 0
        if exists:
            print('\tq already exists:', q)
        else:
            print('\tq not exist:', q)
            self.__update_q(video_id, q)

        return exists

    def insert_into_videos(self, args, items):
        print('Inserting video:', args.video_id)

        # items = {'snippet': {'publishedAt': '2019-01-30T08:51:15.000Z', 'channelId': 'UCZHmQk67mSJgfCCTn7xBfew', 'defaultLanguage': 'en', 'tags': ['bert', 'deep learning', 'attention', 'unsupervised', 'nlp',     'transformer', 'squad', 'wordpiece', 'embeddings', 'language', 'language modeling', 'attention layers', 'bidirectional', 'elmo', 'natural language processing', 'machine learning', 'word vectors', 'pretrained',   'fine tuning'], 'description': 'https://arxiv.org/abs/1810.04805\n\nAbstract:\nWe introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from  Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations by jointly conditioning on both left and right context in all layers. As a result, the  pre-trained BERT representations can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without     substantial task-specific architecture modifications. \nBERT is conceptually simple and empirically powerful. It obtains new state-of-the-art results on eleven natural language processing tasks, including    pushing the GLUE benchmark to 80.4% (7.6% absolute improvement), MultiNLI accuracy to 86.7 (5.6% absolute improvement) and the SQuAD v1.1 question answering Test F1 to 93.2 (1.5% absolute improvement),  outperforming human performance by 2.0%.\n\nAuthors:\nJacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova', 'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',    'defaultAudioLanguage': 'en', 'channelTitle': 'Yannic Kilcher'}, 'statistics': {'favoriteCount': '0', 'dislikeCount': '7', 'commentCount': '37', 'viewCount': '23138', 'likeCount': '539'}, 'contentDetails':  {'duration': 'PT40M13S'}}

        items = self.preprocessor.preprocess(items)
        # items = preprocess_items.preprocess_datetime(items)
        # items = preprocess_items.preprocess_list(items)
        # items = preprocess_items.preprocess_ascii(items)
        # print('\nitems:', items)

        self.insert('videos', items, {'q': args.q})

    def update_duration(self):
        preprocessor = Preprocessor()
        sql = "SELECT idx, duration FROM videos;"
        self.mycursor.execute(sql)
        results = self.mycursor.fetchall()
        print(type(results[0]), len(results[0]), results[0])
        for row in results:
            new_duration = preprocessor.preprocess_duration(row[1])
            sql = "UPDATE videos SET duration='%s' WHERE idx=%d;" % (
                new_duration, row[0])
            print(sql)
            self.mycursor.execute(sql)
            self.conn.commit()

    def set_iter_videoId(self):
        self.mycursor.execute(self.sql_handler.select(
            'videos', 'videoId').where('exposition', None).get_sql())
        _result = self.mycursor.fetchall()
        print('result:', _result)
        self._iter = iter(_result)
        self._curr_video_id = None
        self._list_video_ids = list()
        self._list_expositions = list()

    def open_webdriver(self):
        self.driver = webdriver.Chrome('./chromedriver')

    def driver_get_videoId(self):
        self._curr_video_id = self._iter.__next__()[0]
        print('videoId:', self._curr_video_id)
        self.driver.get("https://www.youtube.com/watch?v=%s" %
                        self._curr_video_id)

    def append_list_expositions(self, exposition=0):
        self._list_video_ids.append(self._curr_video_id)
        self._list_expositions.append(exposition)

    def get_sql_expo(self):
        assert len(self._list_video_ids) == len(self._list_expositions)
        for (_video_id, _expo) in zip(self._list_video_ids, self._list_expositions):
            sql = self.sql_handler.update('videos', columns=['exposition'], values=[
                                          _expo]).where('videoId', _video_id).get_sql()
            self.mycursor.execute(sql)
            self.conn.commit()
