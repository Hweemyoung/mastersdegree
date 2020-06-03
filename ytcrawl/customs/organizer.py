from db_handler import DBHandler
import collections.abc


class Organizer(DBHandler):
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

    def __init__(self):
        super(Organizer, self).__init__()

    def update_dict_recursive(self, d, u):
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self.update_dict_recursive(d.get(k, {}), v)
            else:
                d[k] = v
        return d
