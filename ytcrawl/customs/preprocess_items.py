import datetime

def preprocess_datetime(items):
    target_columns = ['publishedAt']
    for part in items:
        for target_column in target_columns:
            if target_column in items[part]:
                # '2020-03-10T15:10:53.000Z'
                date_string = items[part][target_column]
                d = datetime.datetime.strptime(
                    date_string, '%Y-%m-%dT%H:%M:%S.%fZ')
                items[part][target_column] = d.strftime('%Y-%m-%d %H:%M:%S')

    return items


def preprocess_list(items):
    target_columns = ['tags']
    for part in items:
        for target_column in target_columns:
            if target_column in items[part]:
                l = items[part][target_column]
                if type(l) == list:
                    # ['bert', 'deep learning', 'attention']
                    items[part][target_column] = ', '.join(l)

    return items

def preprocess_ascii(items):
    # target_columns = ['tags']
    for part in items:
        for column in items[part]:
                val = items[part][column]
                if type(val) == str:
                    items[part][column] = deEmojify(val)

    return items


def wrap_columns(columns):
    return list(map(lambda s: '`' + s + '`', columns))


def wrap_values(values):
    return list(map(lambda s: '\'' + s + '\'', values))

def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')