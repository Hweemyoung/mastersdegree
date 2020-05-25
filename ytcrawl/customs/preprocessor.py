import datetime
import re
from datetime import timedelta


class Preprocessor:
    regex_abs = re.compile(r'https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
    regex_pdf = re.compile(r'https?://arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf')
    regex_http = re.compile(r'^http://')
    regex_https = re.compile(r'^https://')

    def __init__(self, items=None):
        self.items = items

    def preprocess(self, items):
        dict_cases = {
            'datetime': {'target_columns': ['publishedAt'],
                         'method': self.preprocess_datetime},
            'list': {'target_columns': ['tags'],
                     'method': self.preprocess_list},
            'duration': {'target_columns': ['duration'],
                         'method': self.preprocess_duration}
        }
        items = self.preprocess_recursive(items, dict_cases)

        return items

    def preprocess_recursive(self, iterable, dict_cases):
        if type(iterable) == dict:
            for key in iterable:
                # if iterable[key] is dict
                if type(iterable[key]) == dict:
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
                elif type(value) == str:
                    iterable[i] = self.preprocess_ascii(iterable[i])

        else:
            raise TypeError('Dict or list expected')

        return iterable

    def preprocess_datetime(self, value):
        if type(value) == str:
            # Datetime
            try:
                # len(value) == 19
                datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
            else:
                return value
            try:
                # len(value) == 20
                d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                pass
            else:
                return d.strftime('%Y-%m-%d %H:%M:%S')
            try:
                d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                pass
            else:
                return d.strftime('%Y-%m-%d %H:%M:%S')
            
            # Date
            try:
                # len(value) == 10
                datetime.datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                pass
            else:
                return value
            
            raise Exception('Datetime format not understood:', value)

            # if len(value) == 19:
                # d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
                # return value
            # elif len(value) == 20:
                # d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
            # else:
                # d = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            # return d.strftime('%Y-%m-%d %H:%M:%S')

        else:
            raise TypeError('Type str expected, not given.')

    def preprocess_duration(self, duration):
        regex = re.compile(
            r'PT((?P<hours>\d+?)H)?((?P<minutes>\d+?)M)?((?P<seconds>\d+?)S)?')
        parts = regex.match(duration)
        if not parts:
            raise SyntaxError('Cannot compile duration: %s' % duration)
        parts = parts.groupdict()
        for key in parts:
            parts[key] = int(parts[key]) if parts[key] else 0
        # time_params = {}
        # for (name, param) in parts.iteritems():
        # for (name, param) in iter(parts):
        #     if param:
        #         time_params[name] = int(param)
        # return timedelta(**time_params)
        return int(timedelta(**parts).total_seconds())

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

    def url_http_to_https(self, url):
        # Convert only if url matches pdf
        if bool(self.regex_https.match(url)):
            # Pattern: https
            pass
        elif not bool(self.regex_http.match(url)):
            raise SyntaxError(
                'URL pattern not understood as http(s).')
        else:
            # Pattern: http
            url = 'https' + url[4:]
        return url

    def url_https_to_http(self, url):
        # Convert only if url matches pdf
        if bool(self.regex_http.match(url)):
            # Pattern: http
            pass
        elif not bool(self.regex_https.match(url)):
            raise SyntaxError(
                'URL pattern not understood as http(s).')
        else:
            # Pattern: https
            url = 'http' + url[5:]
        return url

    def url_pdf_to_abs(self, url):
        # Convert only if url matches pdf
        if bool(self.regex_abs.match(url)):
            # Pattern: ABS
            pass
        elif not bool(self.regex_pdf.match(url)):
            raise SyntaxError(
                'URL pattern not understood as arXiv PDF.')
        else:
            # Pattern: PDF
            url = url[:-4].replace('pdf', 'abs')
        return url

    def url_abs_to_pdf(self, url):
        # Convert only if url matches abs
        if bool(self.regex_pdf.match(url)):
            # Pattern: ABS
            pass
        elif not bool(self.regex_abs.match(url)):
            raise SyntaxError(
                'URL pattern not understood as arXiv ABS.')
        else:
            url = url.replace('abs', 'pdf') + '.pdf'
        return url
