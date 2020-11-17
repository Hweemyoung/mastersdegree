from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from time import sleep
import json
from random import randint


class YouTube:
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'
    list_projects = [
        # 'ytcrawl',
        # 'ytcrawl1',
        # 'ytcrawl2',
        # 'ytcrawl03',
        # 'ytcrawl04',
        # 'ytcrawl05',
        # 'ytcrawl06',
        # 'ytcrawl07',
        # 'ytcrawl08',
        # 'ytcrawl09',
        # 'ytcrawl10',
        # 'ytcrawl11',
        # 'ytcrawl12',
        # 'ytcrawl13',
        # 'ytcrawl14',
        # 'ytcrawl15',
        # 'ytcrawl16',
        # 'ytcrawl17',
        # 'ytcrawl18',
        # 'ytcrawl19',
        # 'ytcrawl20',
        'ytcrawl21',
        # 'ytcrawl22',
        'ytcrawl23',
        'ytcrawl24',
        'ytcrawl25',
        'ytcrawl26',
        # 'ytcrawl27',
        # 'ytcrawl28',
        # 'ytcrawl29',
        # 'ytcrawl30',
        'ytcrawl31',
        'ytcrawl32',
        'ytcrawl33',
        'ytcrawl34',
        'ytcrawl35',
        'ytcrawl36',
        'ytcrawl37',
        'ytcrawl38',
        'ytcrawl39',
        'ytcrawl40',
        # 'ytcrawl41',
        # 'ytcrawl42',
        # 'ytcrawl43',
        # 'ytcrawl44',
        # 'ytcrawl45',
        # 'ytcrawl46',
        # 'ytcrawl47',
        # 'ytcrawl48',
        # 'ytcrawl49',
        # 'ytcrawl50',
        # 'ytcrawl51',
        # 'ytcrawl52',
        # 'ytcrawl53',
        # 'ytcrawl54',
        # 'ytcrawl55',
        # 'ytcrawl56',
        # 'ytcrawl57',
        # 'ytcrawl58',
        # 'ytcrawl59',
        # 'ytcrawl60',
        # 'ytcrawl61',
        # 'ytcrawl62',
        # 'ytcrawl63',
        # 'ytcrawl64',
        # 'ytcrawl65',
        # 'ytcrawl66',
        # 'ytcrawl67',
        # 'ytcrawl68',
        # 'ytcrawl69',
        # 'ytcrawl70',
        # 'ytcrawl71',
        # 'ytcrawl72',
        # 'ytcrawl73',
        # 'ytcrawl74',
        # 'ytcrawl75',
        # 'ytcrawl76',
        # 'ytcrawl77',
        # 'ytcrawl78',
        # 'ytcrawl79',
        # 'ytcrawl80',
    ]
    dict_api_keys = {
        
    }
    list_projects_unavailable = list()
    list_responses = list()

    args = dict()
    method_name = 'unknown'

    def __init__(self, args, method_name):
        # self.list_api_keys = args['list_api_keys']
        # Update with new args
        self.build_youtube()
        self.method_name = method_name
        # 'fields':'items(id(channelId, videoId), snippet(title, channelId, liveBroadcastContent, channelTitle, description))'
        # 'fields':'items(snippet(channelTitle, title, description))'
        # 'fields':'nextPageToken, items(id(videoId), snippet(channelTitle))',
        # 'fields': options.fields
        self.reset_props(args)
    
    def reset_props(self, args):
        self.args.update(args)
        self.fname = datetime.now().strftime('%Y%m%d_%H%M%S')
        

    def build_youtube(self):
        try:
            if "random_project" in self.args.keys() and self.args["random_project"]:
                _new_project = self.list_projects.pop(randint(0, len(self.list_projects) - 1))
            else:
                _new_project = self.list_projects.pop(0)
        except (ValueError, IndexError):
            # ValueError: randint
            # IndexError: dict.pop
            print('[-]No available project.')
            self.save_task(self.list_responses, self.args)
            quit()

        _new_api_key = self.dict_api_keys.pop(_new_project)
        print('[+]New project: %s\tAPI key: %s\tRemaining projects: %d' %
              (_new_project, _new_api_key, len(self.list_projects)))
        try:
            self.youtube = build(self.YOUTUBE_API_SERVICE_NAME,
                                 self.YOUTUBE_API_VERSION, developerKey=_new_api_key)
        except HttpError as e:
            print(e)
            self.save_task(self.list_responses, self.args)
            quit()

        self.list_projects_unavailable.append(_new_project)
        sleep(1.0)
        return self

    def save_task(self, list_responses, args):
        self.__save_list_responses(list_responses, self.fname)
        self.__save_log(args, self.fname)
        sleep(1.0)  # Prevent duplicating fname
        return self

    def __save_list_responses(self, list_responses, fname):
        _p = './results/%s/%s_%s.txt' % (self.method_name,
                                         self.method_name, fname)
        print('[+]Saving list_responses: %s' % _p)
        with open(_p, 'w+') as fp:
            json.dump(list_responses, fp)
        return self

    def __save_log(self, args, fname):
        _p = './logs/%s/log_%s_%s.txt' % (self.method_name,
                                          self.method_name, fname)
        print('[+]Saving log: %s' % _p)
        # print('\targs:', args)
        with open(_p, 'w+') as fp:
            json.dump(args, fp)
        return self

