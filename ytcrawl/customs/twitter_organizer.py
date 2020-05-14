import json
import calendar
from datetime import datetime, timedelta
from os import listdir
from db_handler import DBHandler


class TwitterOrganizer(DBHandler):
    # 1 Load json -> citation_id.txt
    # 2
    dict_dt_format = {
        'datetime': '%Y-%m-%d %H:%M:%S',
        'date': '%Y-%m-%d',
        'month': '%Y-%m',
        # 'quarter': ,
        'year': '%Y'
    }
    dict_interval = {
        'day': 1,
        'week': 7,
        'month': 1,
        'quarter': 3,
        'half': 6,
        'year': 12
    }

    def __init__(self):
        pass

    def update_stats(self, target=None):
        if target==None:
            # Get .txt files
            _list_fnames = [_fname for _fname in listdir(
                './altmetricit/twitter') if _fname.endswith('.txt')]
            _num_files = len(_list_fnames)
            print('# of result files:', _num_files)

            _num_failed = 0

            for i, _fname in enumerate(_list_fnames):  # 65248654.txt
                print('%d out of %d result files' % (i+1, _num_files))
                _dict_stats = self.__get_stats_from_citation_id(_fname[:-4])
                if _dict_stats == False:
                    _num_failed += 1
                else:
                    self.__save_stats(_dict_stats)
    
    def __save_stats(self, dict_stats):
        print('Saving dict_stats')
        with open('./stats/twitter/%s.txt' % dict_stats['citation_id'], 'w+') as f:
            json.dump(dict_stats, f)

    def __add_months(self, datetime_source, months):
        month = datetime_source.month - 1 + months
        year = datetime_source.year + month // 12
        month = month % 12 + 1
        day = min(datetime_source.day, calendar.monthrange(year,month)[1])
        return datetime_source.replace(year=year, month=month, day=day)

    def __get_stats_from_citation_id(self, citation_id):
        _dict_tweets = self.__get_dict_tweets_from_citation_id(citation_id)
        if _dict_tweets == False:
            return False
        return self.__get_stats_from_dict_tweets(_dict_tweets)
        
    def __get_dict_tweets_from_citation_id(self, citation_id):
        with open('./altmetricit/twitter/%s.txt' % citation_id) as f:
            _dict_tweets = json.load(f)
        if _dict_tweets['completed'] == '0':
            return False
        return _dict_tweets

    def __get_stats_from_dict_tweets(self, dict_tweets, interval='month'):
        # _dict_stats = {
            # 'citation_id': '34476745',
            # 'tab': 'twitter',
            # 'queriedAt': 'xxxx-xx-xx',
            # 'interval': 'month',
            # 'twitter': {
                # 'count_tweets': {..., '2019-02': '0', '2019-03': '426', '2019-04': '2894', ...},
                # 'count_followers': {...}
            # }
        # }
        print('\tCitation_id: %s\tProcessing: %d tweets'%(dict_tweets['citation_id'], len(dict_tweets)))

        _dict_stats = dict()

        # Get publishedAt
        _citation_id = dict_tweets['citation_id']
        self.sql_handler.select('papers', 'publishedAt').where('altmetric_id', _citation_id)
        _sql = self.sql_handler.get_sql()
        self.mycursor.execute(_sql)
        _result = self.mycursor.fetchall()
        _dict_stats['publishedAt'] = _result[0][0] if len(_result) else None
        
        # Copy from dict_tweets
        _dict_stats['citation_id'] = _citation_id
        _dict_stats['tab'] = dict_tweets['tab']
        _dict_stats['queriedAt'] = dict_tweets['queriedAt']
        _dict_stats['interval'] = dict_tweets['interval']
        
        # New item
        _dict_stats['twitter'] = dict()
        _dict_stats['twitter']['count_tweets'] = dict()
        _dict_stats['twitter']['count_followers'] = dict()
        _dt_oldest = datetime.now()
        _dt_newest = datetime.now()

        for _tweet_id in dict_tweets['twitter']:
            _dict_tweet = dict_tweets['twitter'][_tweet_id]

            # datetime
            _dt_tweet = datetime.strptime(
                _dict_tweet['datetime'],
                self.dict_dt_format['datetime']
            )
            # Update _dt_oldest, _dt_newest
            _dt_oldest = min(_dt_oldest, _dt_tweet)
            _dt_newest = max(_dt_newest, _dt_tweet)
            
            # if dt not exists yet
            _key_dt = _dt_tweet.strftime(self.dict_dt_format[interval])
            if _key_dt not in _dict_stats['twitter']['count_tweets']:
                _dict_stats['twitter']['count_tweets'][_key_dt] = 0
                _dict_stats['twitter']['count_followers'][_key_dt] = 0
            
            # Add count
            _dict_stats['twitter']['count_tweets'][_key_dt] += 1
            _dict_stats['twitter']['count_followers'][_key_dt] += int(_dict_tweet['followers'])
        
        # Fill out empty DTs
        _dt_publish = datetime.strptime(_dict_stats['publishedAt'], self.dict_dt_format['date'])
        _dt_oldest = min(_dt_oldest, _dt_publish)
        _dt_newest = max(_dt_newest, _dt_publish)
        
        _dict_stats = self.__fill_empty_dts(_dict_stats, _dt_oldest, _dt_newest, interval)

        return _dict_stats

    def __fill_empty_dts(self, dict_stats, dt_oldest, dt_newest, interval):
        while dt_oldest < dt_newest:
            _key_dt = dt_oldest.strftime(self.dict_dt_format[interval])
            
            # Add key
            if _key_dt not in dict_stats['twitter']['count_tweets']:
                dict_stats['twitter']['count_tweets'][_key_dt] = 0
                dict_stats['twitter']['count_followers'][_key_dt] = 0
            
            # DT increment
            if interval not in ['day', 'week']:
                dt_oldest = self.__add_months(dt_oldest, self.dict_interval[interval])
            else:
                dt_oldest = dt_oldest + timedelta(days=self.dict_interval[interval])

        return dict_stats

        
        
        
        



