from preprocessor import Preprocessor


class SQLHandler:
    command = None
    command_set = False
    list_where_clauses = []
    # get_where_from_list()
    dict_where_conj = {'and': ' AND ', 'or': ' OR '}
    # check_type()
    dict_types = {str: 'str', int: 'int', list: 'list', tuple: 'tuple'}

    def __init__(self):
        pass

    def set_command_set(self):
        self.command_set = True
        print('Command set:', self.command)
        return self

    def select(self, table, columns='*'):
        if type(columns) in (list, tuple):
            columns = map(lambda column: '`' + column + '`', columns)
            columns = ', '.join(columns)
        self.command = "SELECT %s FROM %s" % (columns, table)
        self.set_command_set()
        return self

    def update(self, table, columns=None, values=None, dict_columns_values=None):
        if dict_columns_values != None:
            columns = dict_columns_values.keys()
            values = dict_columns_values.values()

        key_val_pairs = list()
        for col, val in zip(columns, values):
            key_val_pairs.append("%s='%s'" % (col, val))\
                if type(val) == str else key_val_pairs.append("%s=%d" % (col, val))
        key_val_pairs = ', '.join(key_val_pairs)

        self.command = "UPDATE %s SET %s" % (table, key_val_pairs)
        self.set_command_set()
        return self

    def init_command(self):
        self.command = None
        self.command_set = False
        return self

    def init_list_where_clauses(self, index=None):
        if index != None:
            pop = self.list_where_clauses.pop(index)
            print('list_where_cluases[%d] popped:' % index, pop)
        else:
            self.list_where_clauses = []
        return self

    def get_sql(self, mode_where='and'):
        if not self.command_set:
            raise ValueError('Command not set.')
        self.last_sql = "%s WHERE %s;" % (
            self.command, self.get_where_from_list(self.list_where_clauses, mode_where))
        print('sql:', self.last_sql)
        return self.last_sql

    def where(self, column, value, mode='equal'):
        # Param 'mode' could be: 'equal', 'match'
        if mode == 'equal':
            clause = "`%s`=%d" % (column, value) \
                if type(value) != str else "`%s`='%s'" % (column, value)
        elif mode == 'fulltext_list':
            self.check_type(value, 'str')
            list_clauses = []
            list_clauses.append(
                "match(%s) against ('%s,' in boolean mode)" % (column, value))
            list_clauses.append(
                "match(%s) against (' %s' in boolean mode)" % (column, value))
            list_clauses.append(
                "`%s`='%s'" % (column, value))

            clause = self.get_where_from_list(list_clauses, 'or')
        elif mode == 'fulltext':
            clause = "match(%s) against (%s in boolean mode)" % (column, value)
        else:
            raise ValueError()

        if clause not in self.list_where_clauses:
            self.list_where_clauses.append(clause)
        print('Current list_where_clauses:', self.list_where_clauses)
        return self

    def check_type(self, value, type_targets='str'):
        str_value_type = self.dict_types[type(value)]
        if type(type_targets) not in (list, tuple):
            if str_value_type != type_targets:
                raise TypeError(value, ': Type %s expected, %s given.:' % (
                    type_targets, str_value_type))
        else:
            if str_value_type not in type_targets:
                raise TypeError(value, ': Type %s expected, %s given.:' % (
                    ' or '.join(type_targets), str_value_type))
        return self

    def get_where_from_list(self, list_clauses, mode='and'):
        if len(list_clauses):
            conj = self.dict_where_conj[mode]
            where = '(' + conj.join(list_clauses) + ')'
        else:
            where = '1'
        print('Where:', where)
        return where
