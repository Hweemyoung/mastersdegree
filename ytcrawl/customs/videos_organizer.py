import json
import calendar
from datetime import time, datetime, timedelta
from os import listdir, path
from db_handler import DBHandler


class VideosOrganizer(DBHandler):
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
    dict_msg_err = dict()
    msg_err = ''

    tup_cols_videos = ('idx', 'videoId', 'publishedAt', 'defaultLanguage', 'defaultAudioLanguage', 'channelId', 'duration',
                       'viewCount', 'dislikeCount', 'commentCount', 'favoriteCount', 'liveStreaming', 'content', 'idx_paper', 'queriedAt')
    tup_enum_content = ('paper_explanation', 'paper_supplementary', 'paper_application',
                        'paper_assessment', 'paper_reference', 'news', 'dialogue', 'routine')
    dict_count_content = dict(zip(tup_enum_content, [0]*len(tup_enum_content)))
    keys_videos = ['videoCount', 'durationCount', 'viewCount',
                   'dislikeCount', 'commentCount', 'favoriteCount', 'livesCount', 'content']

    dir_stats = './stats/videos'

    def __init__(self, table_name_videos, table_name_papers):
        super(VideosOrganizer, self).__init__()
        self.table_name_videos = table_name_videos
        self.table_name_papers = table_name_papers

    def set_list_idx_papers(self, list_idx_papers=None):
        if list_idx_papers == None:
            self.sql_handler.select(self.table_name_papers, 'idx').where(
                'subject_1', 'Computer Science').where('subject_2', 'Machine Learning')
            list_idx_papers = list(
                map(lambda _row: _row[0], self.execute().fetchall()))
        self.list_idx_papers = list_idx_papers
        return self

    def update_stats(self, list_idx_papers=None, overwrite='new'):
        if list_idx_papers == None:
            list_idx_papers = self.list_idx_papers
        _num_failed = 0
        _num_papers = len(list_idx_papers)
        print('# of papers:', _num_papers)

        for i, _idx_paper in enumerate(list_idx_papers):  # 2375
            print('%d out of %d papers' % (i+1, _num_papers))
            _dict_stats = self.__get_stats_from_idx_paper(_idx_paper)
            if _dict_stats == False:
                _num_failed += 1
                self.dict_msg_err[str(_idx_paper)] = self.msg_err
            else:
                self.__save_stats(_dict_stats, overwrite=overwrite)

        print('Completed: update_stats\t# of jobs inqueued: %d\t# of failed jobs: %d\n' % (
            _num_papers, _num_failed))
        if len(self.dict_msg_err):
            _fp = path.join(self.dir_stats, 'log_fail_%s.txt' %
                            datetime.now().strftime('%Y%m%d_%H%M%S'))
            with open(_fp, 'w+') as f:
                json.dump(self.dict_msg_err, f)
            print('Saved dict_msg_err at: %s' % _fp)

        return self

    def __save_stats(self, dict_stats, overwrite):
        _fp = path.join(self.dir_stats, dict_stats['idx_arxiv'] + '.txt')
        if overwrite != True:
            try:
                with open(_fp, 'r') as f:
                    _queriedAt_old = json.load(f)['queriedAt']
            except IOError:  # No such file or directory
                pass
            else:
                if overwrite == False:
                    return True
                elif overwrite == 'new':
                    if datetime.strptime(dict_stats['queriedAt'], self.dict_dt_format['datetime']) < datetime.strptime(_queriedAt_old, self.dict_dt_format['datetime']):
                        return True

        print('\tSaving dict_stats.')
        with open(_fp, 'w+') as f:
            json.dump(dict_stats, f)

        return True

    def __add_months(self, datetime_source, months):
        month = datetime_source.month - 1 + months
        year = datetime_source.year + month // 12
        month = month % 12 + 1
        day = min(datetime_source.day, calendar.monthrange(year, month)[1])
        return datetime_source.replace(year=year, month=month, day=day)

    def __get_video_from_db(self, idx_paper):
        self.sql_handler.select(self.table_name_videos, self.tup_cols_videos).where(
            'idx_paper', idx_paper, 'fulltext_list')
        return self.execute().fetchall()
    
    def __get_init_dict_count_videos(self):
        # return dict(
            # zip(self.keys_videos, [dict()]*len(self.keys_videos)))  # Assign empty dict to every key
        _dict_count_videos = dict()
        for key in self.keys_videos:
            _dict_count_videos[key] = dict()
        return _dict_count_videos


    def __get_stats_from_idx_paper(self, idx_paper, interval='month'):
        print('\tidx_paper: %s' % idx_paper)
        _list_videos = self.__get_video_from_db(idx_paper)
        if not _list_videos:  # No such records
            self.msg_err = "idx_paper not exist."
            return False

        # idx_paper, idx_arxiv, queriedAt, interval, dt_start, dt_end, publishedAt, videos: {}
        _dict_stats = dict()
        _dict_stats['idx_paper'] = idx_paper

        self.sql_handler.select(self.table_name_papers,
                                ['publishedAt', 'idx_arxiv']).where('idx', idx_paper)
        _result = self.execute().fetchall()[0]
        _date_paper = _result[0]
        _dict_stats['publishedAt'] = _date_paper.strftime(self.dict_dt_format['date'])
        _dict_stats['idx_arxiv'] = _result[1]

        _dict_stats['queriedAt'] = datetime.now().strftime(
            self.dict_dt_format['datetime'])
        _dict_stats['interval'] = interval
        _dict_stats['videos'] = self.__get_init_dict_count_videos()
        _dt_oldest = datetime.now()
        _dt_newest = datetime.now()

        for _row in _list_videos:
            _dict_video = dict(zip(self.tup_cols_videos, _row))
            # dt_video
            _dt_video = _dict_video['publishedAt']

            # Update _dt_oldest, _dt_newest
            _dt_oldest = min(_dt_oldest, _dt_video)
            _dt_newest = max(_dt_newest, _dt_video)

            # if dt not exists yet
            _key_dt = _dt_video.strftime(self.dict_dt_format[interval])
            if _key_dt not in _dict_stats['videos']['videoCount']:
                _dict_stats['videos'].update(self.__get_init_dict_count_videos_by_key_dt(_key_dt))
                
            # Add count
            _dict_stats['videos']['videoCount'][_key_dt] += 1
            _dict_stats['videos']['durationCount'][_key_dt] += int(
                _dict_video['duration'])
            _dict_stats['videos']['viewCount'][_key_dt] += int(
                _dict_video['viewCount'])
            _dict_stats['videos']['dislikeCount'][_key_dt] += int(
                _dict_video['dislikeCount'])
            _dict_stats['videos']['commentCount'][_key_dt] += int(
                _dict_video['commentCount'])
            _dict_stats['videos']['favoriteCount'][_key_dt] += int(
                _dict_video['favoriteCount'])
            _dict_stats['videos']['livesCount'][_key_dt] += int(
                _dict_video['liveStreaming']) # += 0 or 1
            _dict_stats['videos']['content'][_key_dt][_dict_video['content']] += 1

        # Fill out empty DTs
        _dt_paper = datetime.combine(_date_paper, time())
        _dt_oldest = min(_dt_oldest, _dt_paper)
        _dt_newest = max(_dt_newest, _dt_paper)

        _dict_stats['dt_start'] = _dt_oldest.strftime(
            self.dict_dt_format[interval])
        _dict_stats['dt_end'] = _dt_newest.strftime(
            self.dict_dt_format[interval])
        _dict_stats = self.__fill_empty_dts(
            _dict_stats, _dt_oldest, _dt_newest, interval)
        _dict_stats = self.__cast_to_str(_dict_stats)

        return _dict_stats

    def __get_init_dict_count_videos_by_key_dt(self, key_dt):
        _new_dict_count_videos = self.__get_init_dict_count_videos()
        _new_dict_count_videos['videoCount'][key_dt] = 0
        _new_dict_count_videos['durationCount'][key_dt] = 0
        _new_dict_count_videos['viewCount'][key_dt] = 0
        _new_dict_count_videos['dislikeCount'][key_dt] = 0
        _new_dict_count_videos['commentCount'][key_dt] = 0
        _new_dict_count_videos['favoriteCount'][key_dt] = 0
        _new_dict_count_videos['livesCount'][key_dt] = 0
        _new_dict_count_videos['content'][key_dt] = dict(zip(self.tup_enum_content, [0]*len(self.tup_enum_content)))

        # _dict_count_content = dict(zip(self.tup_enum_content, [0]*len(self.tup_enum_content))).copy()
        # _new_dict_count_videos['content'][key_dt] = _dict_count_content
        return _new_dict_count_videos

    def __fill_empty_dts(self, dict_stats, dt_oldest, dt_newest, interval):
        while dt_oldest < dt_newest:
            _key_dt = dt_oldest.strftime(self.dict_dt_format[interval])

            # Add key
            if _key_dt not in dict_stats['videos']['videoCount']:
                dict_stats['videos'].update(self.__get_init_dict_count_videos_by_key_dt(_key_dt))

            # DT increment
            if interval not in ['day', 'week']:
                dt_oldest = self.__add_months(
                    dt_oldest, self.dict_interval[interval])
            else:
                dt_oldest = dt_oldest + \
                    timedelta(days=self.dict_interval[interval])

        return dict_stats

    def __cast_to_str(self, data):
        if type(data) == list:
            for i, val in enumerate(data):
                data[i] = self.__cast_to_str(val)
        elif type(data) == dict:
            for _key in data:
                data[_key] = self.__cast_to_str(data[_key])
        elif type(data) == int:
            data = str(data)
        elif type(data) == str:
            pass
        else:
            raise TypeError(
                'Type in [list, dict, int, str] expected.', type(data), 'given.')

        return data


if __name__ == '__main__':
    videos_organizer = VideosOrganizer('temp_videos', 'temp_papers')
    videos_organizer.set_list_idx_papers().update_stats(overwrite='new')
