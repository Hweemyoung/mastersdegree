from db_handler import DBHandler
from preprocessor import Preprocessor
from datetime import datetime
from selenium import webdriver


class DBVideosUploader:
    preprocessor = Preprocessor()
    db_handler = DBHandler()

    num_insert = 0
    num_update = 0
    num_pass = 0
    num_warning = 0

    fields_q_filter = ("title", "description")

    def __init__(self, table_name='temp_videos'):
        self.table_name = table_name

    def upload_videos(self, list_videos, filter_by_q=False, overwrite=False):
        _num_videos = len(list_videos)
        for i, _dict_response in enumerate(list_videos):
            print('Processing %d out of %d videos' % (i+1, _num_videos))
            if filter_by_q and not self.__q_in_fields(_dict_response):
                print("[-]Q not included.")
                continue
            self.__upload_video(_dict_response, overwrite)
        print("# videos: %d\t# insert: %d\t# update: %d\t# pass: %d\t# warning: %d" %
              (_num_videos, self.num_insert, self.num_update, self.num_pass, self.num_warning))

        return True

    def __q_in_fields(self, dict_response):
        for _field in self.fields_q_filter:
            if dict_response["q"].replace(" ", "").replace("\n", "").lower() in dict_response["items"][0]["snippet"][_field].replace(" ", "").replace("\n", "").lower():
                return True
        return False

    def __update_idx_paper(self, idx_video, new_idx_paper):
        self.db_handler.sql_handler.select(
            self.table_name, 'idx_paper').where('idx', idx_video)
        result = self.db_handler.execute().fetchall()
        # sql = "SELECT `q` FROM videos WHERE `videoId`='%s';" % video_id
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        old_idx_paper = result[0][0] if len(result) else ''
        print('\tUpdating idx_paper to:', old_idx_paper + ', ' + new_idx_paper)
        self.db_handler.sql_handler.update(self.table_name, dict_columns_values={
                                           'idx_paper': old_idx_paper + ', ' + new_idx_paper}).where('idx', idx_video)
        self.db_handler.execute()
        return True

    def __update_q(self, idx_video, new_q):
        self.db_handler.sql_handler.select(
            self.table_name, 'q').where('idx', idx_video)
        result = self.db_handler.execute().fetchall()
        # sql = "SELECT `q` FROM videos WHERE `videoId`='%s';" % video_id
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        old_q = result[0][0] if len(result) else ''
        print('\tUpdating q to:', old_q + ', %s' % new_q)
        self.db_handler.sql_handler.update(self.table_name, dict_columns_values={
                                           'q': old_q + ', ' + new_q}).where('idx', idx_video)
        self.db_handler.execute()
        return True

        # sql = "UPDATE videos SET q='%s' WHERE videoId='%s';" % (
        # old_q + ', %s' % new_q, video_id)
        # self.mycursor.execute(sql)
        # self.conn.commit()

    def __get_idx_by_video_id(self, video_id, idx_paper):
        self.db_handler.sql_handler.reset()
        self.db_handler.sql_handler.select(
            # self.table_name, 'idx').where('videoId', video_id, '=')
            self.table_name, 'idx').where('videoId', video_id, '=').where("idx_paper", idx_paper, "=")
        result = self.db_handler.execute().fetchall()

        # sql = "SELECT 1 FROM videos WHERE videos.videoId='%s';" % (video_id)
        # print('\nsql:', sql)
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        # exists = len(result) != 0
        # if exists:
        #     print('\tVideo already exists:', video_id)
        #     if args.q:
        #         self.q_exists(video_id, args.q)

        # if len(result):
        #     return result[0][0]
        # return False
        if len(result) > 1:
            print("\t[!]Multiple indices found for videoId<%s> and idx_paper<%s>." % (video_id, idx_paper))
            self.num_warning += 1
            
        return result[0][0] if len(result) else False

    def __upload_video(self, _dict_response, overwrite):
        if len(_dict_response["items"]) == 0:
            return True
        _video_id = _dict_response['items'][0]['id']
        _idx_paper = _dict_response["idx_paper"]

        # Check if video already exists by videoID and idx_paper
        _idx_video = self.__get_idx_by_video_id(_video_id, _idx_paper)
        if _idx_video != False and not overwrite:
            print('\tVideo already exists:', _video_id)
            self.__update_q_if_not_exist(_idx_video, _dict_response['q'])

            # Column idx_paper already has _idx_paper: verified by self.__get_idx_by_video_id()
            # self.__update_idx_paper_if_not_exist(
            #     _idx, str(_dict_response['idx_paper']))

            self.num_pass += 1
            return True

        _items = _dict_response['items'][0]
        # Manual preprocessing
        # liveStreaming: set True if exists
        if 'liveStreamingDetails' in _items.keys():
            _items.pop('liveStreamingDetails')
            _items['liveStreaming'] = 1
        else:
            _items['liveStreaming'] = 0
        # key 'id' to 'videoId'
        _items['videoId'] = _items.pop('id')

        # Preprocess
        _items = self.preprocessor.preprocess(_items)

        custom_fields = {
            'q': _dict_response['q'], 'idx_paper': _dict_response['idx_paper']} if _idx_video == False else {}

        # Get columns, values
        columns, values = self.db_handler.get_columns_values(
            _items, custom_fields)

        # Wrap columns
        # columns = self.preprocessor.wrap_columns(columns)

        values = tuple(values)
        # print('\tValues:', values)

        if _idx_video == False:
            self.db_handler.sql_handler.insert(
                self.table_name, columns=columns, values=values)
            self.db_handler.execute()
            self.num_insert += 1
        else:
            self.db_handler.sql_handler.update(
                self.table_name, columns=columns, values=values
            ).where("idx", _idx_video)
            self.db_handler.execute()
            self.__update_q_if_not_exist(_idx_video, _dict_response['q'])
            # self.__update_idx_paper_if_not_exist(
            #     _idx_video, str(_dict_response['idx_paper']))
            self.num_update += 1

        return True

    def __update_idx_paper_if_not_exist(self, idx_video, idx_paper):
        # Check if idx_paper exists
        self.db_handler.sql_handler.select(self.table_name, 'idx_paper').where(
            'idx', idx_video).where('idx_paper', idx_paper, 'fulltext_list')
        result = self.db_handler.execute().fetchall()
        # sql = "SELECT `q` FROM videos WHERE `videoId`='%s' AND match(q) against('\"%s\"' in boolean mode);" % (
        # video_id, q)
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()

        if len(result):
            print('\tidx_paper already exists:', idx_paper)
            return True
        else:
            print('\tidx_paper not exist:', idx_paper)
            return self.__update_idx_paper(idx_video, idx_paper)

    def __update_q_if_not_exist(self, idx_video, q):
        # Check if q exists
        self.db_handler.sql_handler.select(self.table_name, 'q').where(
            'idx', idx_video).where('q', q, 'fulltext_list')
        result = self.db_handler.execute().fetchall()
        # sql = "SELECT `q` FROM videos WHERE `videoId`='%s' AND match(q) against('\"%s\"' in boolean mode);" % (
        # video_id, q)
        # self.mycursor.execute(sql)
        # result = self.mycursor.fetchall()
        if len(result):
            print('\tq already exists:', q)
            return True
        else:
            print('\tq not exist:', q)
            return self.__update_q(idx_video, q)

    def insert_into_videos(self, args, items):
        print('Inserting video:', args.video_id)

        # items = {'snippet': {'publishedAt': '2019-01-30T08:51:15.000Z', 'channelId': 'UCZHmQk67mSJgfCCTn7xBfew', 'defaultLanguage': 'en', 'tags': ['bert', 'deep learning', 'attention', 'unsupervised', 'nlp',     'transformer', 'squad', 'wordpiece', 'embeddings', 'language', 'language modeling', 'attention layers', 'bidirectional', 'elmo', 'natural language processing', 'machine learning', 'word vectors', 'pretrained',   'fine tuning'], 'description': 'https://arxiv.org/abs/1810.04805\n\nAbstract:\nWe introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from  Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations by jointly conditioning on both left and right context in all layers. As a result, the  pre-trained BERT representations can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without     substantial task-specific architecture modifications. \nBERT is conceptually simple and empirically powerful. It obtains new state-of-the-art results on eleven natural language processing tasks, including    pushing the GLUE benchmark to 80.4% (7.6% absolute improvement), MultiNLI accuracy to 86.7 (5.6% absolute improvement) and the SQuAD v1.1 question answering Test F1 to 93.2 (1.5% absolute improvement),  outperforming human performance by 2.0%.\n\nAuthors:\nJacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova', 'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',    'defaultAudioLanguage': 'en', 'channelTitle': 'Yannic Kilcher'}, 'statistics': {'favoriteCount': '0', 'dislikeCount': '7', 'commentCount': '37', 'viewCount': '23138', 'likeCount': '539'}, 'contentDetails':  {'duration': 'PT40M13S'}}

        items = self.preprocessor.preprocess(items)
        # items = preprocess_items.preprocess_datetime(items)
        # items = preprocess_items.preprocess_list(items)
        # items = preprocess_items.preprocess_ascii(items)
        # print('\nitems:', items)

        self.db_handler.insert(self.table_name, items, {'q': args.q})

    def update_duration(self):
        preprocessor = Preprocessor()
        sql = "SELECT idx, duration FROM videos;"
        self.db_handler.mycursor.execute(sql)
        results = self.db_handler.mycursor.fetchall()
        print(type(results[0]), len(results[0]), results[0])
        for row in results:
            new_duration = preprocessor.preprocess_duration(row[1])
            sql = "UPDATE videos SET duration='%s' WHERE idx=%d;" % (
                new_duration, row[0])
            print(sql)
            self.db_handler.mycursor.execute(sql)
            self.db_handler.conn.commit()

    def set_iter_videoId(self):
        self.db_handler.sql_handler.select(
            self.table_name, 'videoId').where('exposition', None)
        _result = self.db_handler.mycursor.fetchall()
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
            self.db_handler.sql_handler.update(self.table_name, columns=['exposition'], values=[
                _expo]).where('videoId', _video_id)
            self.db_handler.execute()
