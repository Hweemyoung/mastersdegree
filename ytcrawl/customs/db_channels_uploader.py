from db_uploader import DBUploader
from datetime import datetime


class DBChannelsUploader(DBUploader):
    def channel_id_exists(self, channel_id):
        sql = "SELECT 1 FROM channels WHERE channels.channelId='%s';" % (
            channel_id)
        print('\nsql:', sql)
        self.mycursor.execute(sql)
        result = self.mycursor.fetchall()
        if len(result) != 0:
            print('\nChannels already exists:', channel_id)
        return len(result) != 0

    # def insert_into_channels(self, args, items):
    #     print('\Inserting channel:', args.channel_id)

    #     # items = {'snippet': {'publishedAt': '2019-01-30T08:51:15.000Z', 'channelId': 'UCZHmQk67mSJgfCCTn7xBfew', 'defaultLanguage': 'en', 'tags': ['bert', 'deep learning', 'attention', 'unsupervised', 'nlp',     'transformer', 'squad', 'wordpiece', 'embeddings', 'language', 'language modeling', 'attention layers', 'bidirectional', 'elmo', 'natural language processing', 'machine learning', 'word vectors', 'pretrained',   'fine tuning'], 'description': 'https://arxiv.org/abs/1810.04805\n\nAbstract:\nWe introduce a new language representation model called BERT, which stands for Bidirectional Encoder Representations from  Transformers. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations by jointly conditioning on both left and right context in all layers. As a result, the  pre-trained BERT representations can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without     substantial task-specific architecture modifications. \nBERT is conceptually simple and empirically powerful. It obtains new state-of-the-art results on eleven natural language processing tasks, including    pushing the GLUE benchmark to 80.4% (7.6% absolute improvement), MultiNLI accuracy to 86.7 (5.6% absolute improvement) and the SQuAD v1.1 question answering Test F1 to 93.2 (1.5% absolute improvement),  outperforming human performance by 2.0%.\n\nAuthors:\nJacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova', 'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',    'defaultAudioLanguage': 'en', 'channelTitle': 'Yannic Kilcher'}, 'statistics': {'favoriteCount': '0', 'dislikeCount': '7', 'commentCount': '37', 'viewCount': '23138', 'likeCount': '539'}, 'contentDetails':  {'duration': 'PT40M13S'}}

    #     # items = preprocess_items.preprocess_datetime(items)
    #     # items = preprocess_items.preprocess_list(items)
    #     # items = preprocess_items.preprocess_ascii(items)
    #     items = self.preprocessor.preprocess(items)
    #     # print('\nitems:', items)

    #     columns = list()
    #     values = list()
    #     for part in items:
    #         # print(part)
    #         columns = columns + list(items[part].keys())
    #         values = values + list(items[part].values())

    #     # Custom fields
    #     # columns = columns + ['q', 'queriedAt', 'videoId']
    #     # values = values + [args.q, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), args.video_id]

    #     columns = self.preprocessor.wrap_columns(columns)
    #     # values = preprocess_items.wrap_values(values)
    #     print('\ncolumns:', columns, '#:', len(columns))
    #     print('\nvalues:', values, '#:', len(values))

    #     # sql = 'INSERT INTO videos ' + \
    #     #     '(' + ', '.join(columns) + ')' + ' VALUES ' + \
    #     #       '(' + ', '.join(values) + ')' + ';'
    #     sql = 'INSERT INTO channels ' + \
    #         '(' + ', '.join(columns) + ')' + ' VALUES ' + \
    #           '(' + ', '.join(['%s']*len(values)) + ');'
    #     val = tuple(values)
    #     print('\n', sql)
    #     self.mycursor.execute(sql, val)
    #     self.conn.commit()
