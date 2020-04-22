import datetime


class Preprocessor:
    def __init__(self, items=None):
        self.items = items

    def preprocess(self, items):
        dict_cases = {
            'datetime': {'target_columns': ['publishedAt'],
                         'method': self.preprocess_datetime},
            'list': {'target_columns': ['tags'],
                     'method': self.preprocess_list}
        }
        items = self.preprocess_recursive(items, dict_cases)

        return items

    def preprocess_recursive(self, iterable, dict_cases):
        if type(iterable) == dict:
            for key in iterable:
                # if iterable[key] is iter
                if type(iterable[key]) in (dict, list):
                    iterable[key] = self.preprocess_recursive(
                        iterable[key], dict_cases)
                    continue

                # if str: Make sure of ASCII
                elif type(iterable[key]) == str:
                    iterable[key] = self.preprocess_ascii(iterable[key])

                for case in dict_cases:
                    if key in dict_cases[case]['target_columns']:
                        iterable[key] = dict_cases[case]['method'](
                            iterable[key])
                        # Go on to next key in iterable
                        break

        elif type(iterable) == list:
            for i, value in enumerate(iterable):
                # if iterable[key] is iter
                if type(value) in (dict, list):
                    iterable[i] = self.preprocess_recursive(
                        iterable[i], dict_cases)
                    continue

                # if str: Make sure of ASCII
                elif type(iterable[key]) == str:
                    iterable[i] = self.preprocess_ascii(iterable[i])

                for case in dict_cases:
                    if key in dict_cases[case]['target_columns']:
                        iterable[i] = dict_cases[case]['method'](iterable[i])
                        # Go on to next key in iterable
                        break

        else:
            raise TypeError('Dict or list expected')

        return iterable

    def preprocess_datetime(self, value):
        if type(value) == str:
            if len(value) == 19:
                return value
            elif len(value) == 20:
                d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            else:
                d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            return d.strftime('%Y-%m-%d %H:%M:%S')

        else:
            raise TypeError('Type str expected, not given.')

    def preprocess_list(self, value):
        return ', '.join(value)

    def preprocess_ascii(self, value):
        if type(value) == str:
            return self.deEmojify(value)

    def wrap_columns(self, columns):
        return list(map(lambda s: '`' + s + '`', columns))

    def wrap_values(self, values):
        return list(map(lambda s: '\'' + s + '\'', values))

    def deEmojify(self, inputString):
        return inputString.encode('ascii', 'ignore').decode('ascii')
