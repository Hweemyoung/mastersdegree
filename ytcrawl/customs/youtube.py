from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from time import sleep
import json


class YouTube:
    YOUTUBE_API_SERVICE_NAME = 'youtube'
    YOUTUBE_API_VERSION = 'v3'
    list_projects = [
        'ytcrawl',
        'ytcrawl1',
        'ytcrawl2',
        'ytcrawl03',
        'ytcrawl04',
        'ytcrawl05',
        'ytcrawl06',
        'ytcrawl07',
        'ytcrawl08',
        'ytcrawl09',
        'ytcrawl10',
        'ytcrawl11',
        'ytcrawl12',
        'ytcrawl13',
        'ytcrawl14',
        'ytcrawl15',
        'ytcrawl16',
        'ytcrawl17',
        'ytcrawl18',
        'ytcrawl19',
        'ytcrawl20',
        'ytcrawl21',
        'ytcrawl22',
        'ytcrawl23',
        'ytcrawl24',
        'ytcrawl25',
        'ytcrawl26',
        'ytcrawl27',
        'ytcrawl28',
        'ytcrawl29',
        'ytcrawl30',
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
        'ytcrawl41',
        'ytcrawl42',
        'ytcrawl43',
        'ytcrawl44',
        'ytcrawl45',
        'ytcrawl46',
        'ytcrawl47',
        'ytcrawl48',
        'ytcrawl49',
        'ytcrawl50'
    ]
    dict_api_keys = {
        'ytcrawl': 'AIzaSyCVMEUGxxsSw-BKH4c06PHKr_F4qjSdwJw',
        'ytcrawl1': 'AIzaSyDuW2lWKYOc-tPjwcXso4LhR8_ZMEZOGKw',
        'ytcrawl2': 'AIzaSyBahI8vJbinh7itJs2hJRNW4spp0B2Dqpk',
        'ytcrawl03': 'AIzaSyAWMAqdS3DQLmgAJSJyXMyiajBveZgzlxo',
        'ytcrawl04': 'AIzaSyBdPXSVQKNeNkJPxqpZ8yZzrfAnFCB3yTc',
        'ytcrawl05': 'AIzaSyDTghJE9L_RwF6z6WyA109R4CqhLnFu3gY',
        'ytcrawl06': 'AIzaSyD7iqSQp2um_7k6_3UpNyK-SC1-CUWD4LU',
        'ytcrawl07': 'AIzaSyBPWVOP9sAGbNo0bFe5zPOjhxm82-9lKC4',
        'ytcrawl08': 'AIzaSyAyhb8jQtrnaFCMymT-cy5CTSYyuMOAGLg',
        'ytcrawl09': 'AIzaSyDJCSICBywbwjIjp8qtU1EHnxxBJo7LeAw',
        'ytcrawl10': 'AIzaSyCEf_6Fv_tUuP07XjZKhqbclKJKp--440M',
        'ytcrawl11': 'AIzaSyDQLu7sQCquRIVo4-SGVyVwaATJHJUlhY8',
        'ytcrawl12': 'AIzaSyDuKvBLkfNHBOSsUEzoWpC6hFiQwE1KN54',
        'ytcrawl13': 'AIzaSyCAfy3mfKrqA4wcj-bGlRiLjFLEhDlLKjg',
        'ytcrawl14': 'AIzaSyBaxDPHLeWz1GLRb5YwXWDqcUu0FRd7X1g',
        'ytcrawl15': 'AIzaSyDunShOaOvphsL8UkughrUtTyFkgPsR7Lo',
        'ytcrawl16': 'AIzaSyAw-YbLGooOAFeuh7IYNMQaZyMi8nQ8WNM',
        'ytcrawl17': 'AIzaSyDk5QkvNTEPveazGovCzoNGpr_g0B92Ih0',
        'ytcrawl18': 'AIzaSyACs7FFs4zsn5mUvfZY71-lGi4AywO1lU4',
        'ytcrawl19': 'AIzaSyD5yOMseJmlYZKjH5tH-iIwL6Q9IGMyMVM',
        'ytcrawl20': 'AIzaSyAd7qhESUmr07GuRZ3FkBnHWwVBiBQzMT8',
        'ytcrawl21': 'AIzaSyDqA_uzh1d8A-ictdbIsWMz9jK7iX1hH5Y',
        'ytcrawl22': 'AIzaSyBcgB5D6MQgo9QNFlLBelpxJkZ4wrY1kuo',
        'ytcrawl23': 'AIzaSyA2WK7vMfvLNKvybZQzweYZPRxUoXGXWDg',
        'ytcrawl24': 'AIzaSyDYIx8gJlpY0pkPDrKyWoeN3sKfUDPb_pY',
        'ytcrawl25': 'AIzaSyDr50YhsGMdt2Fc-Ytbw6LxJwb2l7raw_E',
        'ytcrawl26': 'AIzaSyCgZAZv4bdw-SUTzWb9Ympn4PNnoD-rjBQ',
        'ytcrawl27': 'AIzaSyAUT06XXPhYYx3_t4sfo4YfPvZ4hZYWPiA',
        'ytcrawl28': 'AIzaSyCy6HMLc2NVqjs84Ikj7XK_YiakLNRNPBI',
        'ytcrawl29': 'AIzaSyB7QfnFaFpoYV9GSSIyGljy0Zv7OCzIwB8',
        'ytcrawl30': 'AIzaSyCxbYC_yPyoDQy7lnkeZgQkFRQJWXX5bEg',
        'ytcrawl31': 'AIzaSyBWAW6Vs5lMcSGYKWdKDfHf0RhpYtvXzeM',
        'ytcrawl32': 'AIzaSyB0HV8fUJEdRcbKGNNhAjft1Kz96qZYTPg',
        'ytcrawl33': 'AIzaSyCSaEnm5j1BaoC1nUxRMnf7mBLwtPv1OUo',
        'ytcrawl34': 'AIzaSyCbBJG-dJyIREgYPUu7gD2q4Nt8k-rPn9g',
        'ytcrawl35': 'AIzaSyBGaneVYx40wauRBm4OMqsr5vku75phZjc',
        'ytcrawl36': 'AIzaSyD3SPPTy_Q_cL5XV5IJrGNImiG4m6Au0pc',
        'ytcrawl37': 'AIzaSyD3LtnJu4dEBYZQgvLdWhCU0buCE1Ko83g',
        'ytcrawl38': 'AIzaSyDDWblONcC7X5z4MkR2YsKibOPCygkkpmE',
        'ytcrawl39': 'AIzaSyBe6u5nNoSXldUOSXcfSeuJ-TxJxVTlDeU',
        'ytcrawl40': 'AIzaSyAG7LfsgOUoE2ymGqWL2y6rN1fTpMbH96E',
        'ytcrawl41': 'AIzaSyBNhNNIOdivlepkoYVXR2lCMQ1AbRfmYZM',
        'ytcrawl42': 'AIzaSyCwZ5i7E3dtbLjYGHU1SYaIS_VLkGMWVIs',
        'ytcrawl43': 'AIzaSyAajQ4kpKUCnqOpwbFYSPZ4zrm-VPOb5D8',
        'ytcrawl44': 'AIzaSyCbgbxUBGj-iRNr8H-eRfmljfxJL7bNnEw',
        'ytcrawl45': 'AIzaSyB-b37xz-54uKbj9Mrt3xDAWlcVMPntQfg',
        'ytcrawl46': 'AIzaSyCFnSbXRyOe2m53qKtOqdJ_0tOeubpv6Ic',
        'ytcrawl47': 'AIzaSyARDw8_uSTw4S8rJcV_NDQcLSFmBugHDQs',
        'ytcrawl48': 'AIzaSyA1ZNQ_Gt5bnPLEZ4p_bBmkK4hGvBKPv78',
        'ytcrawl49': 'AIzaSyBMJNQqmaaBZgUz0A99RqipLYhgVTyF4lM',
        'ytcrawl50': 'AIzaSyA3mLSfPq3O8zLdqtbuSsVbj1w0SkXFeSI',
    }
    list_projects_unavailable = list()
    list_responses = list()

    args = dict()
    method_name = 'unknown'

    def __init__(self, args, method_name):
        # self.list_api_keys = args['list_api_keys']
        # Update with new args
        self.method_name = method_name
        self.args.update(args)
        self.build_youtube()
        # 'fields':'items(id(channelId, videoId), snippet(title, channelId, liveBroadcastContent, channelTitle, description))'
        # 'fields':'items(snippet(channelTitle, title, description))'
        # 'fields':'nextPageToken, items(id(videoId), snippet(channelTitle))',
        # 'fields': options.fields

    def build_youtube(self):
        try:
            _new_project = self.list_projects.pop(0)
        except IndexError:
            print('No available project.')
            self.save_task(self.list_responses, self.args)
            quit()
        
        _new_api_key = self.dict_api_keys[_new_project]
        print('New project: %s\tAPI key: %s' % (_new_project, _new_api_key))
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
        _fname = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.__save_list_responses(list_responses, _fname)
        self.__save_log(args, _fname)
        return self

    def __save_list_responses(self, list_responses, fname):
        _p = './results/%s/%s_%s.txt' % (self.method_name,
                                         self.method_name, fname)
        print('Saving list_responses: %s' % _p)
        with open(_p, 'w+') as fp:
            json.dump(list_responses, fp)
        return self

    def __save_log(self, args, fname):
        _p = './logs/%s/log_%s_%s.txt' % (self.method_name,
                                          self.method_name, fname)
        print('Saving log: %s' % _p)
        print('args:', args)
        with open(_p, 'w+') as fp:
            json.dump(args, fp)
        return self
