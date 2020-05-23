from preprocessor import Preprocessor


class SQLHandler:
    command = None
    command_set = False
    values = None
    list_where_clauses = []
    list_order_clauses = []
    # get_where_from_list()
    dict_where_conj = {'and': ' AND ', 'or': ' OR '}
    dict_order = {'asc': 'ASC', 'desc': 'DESC'}
    # __check_type()
    dict_types = {str: 'str', int: 'int', list: 'list', tuple: 'tuple'}

    def __init__(self):
        pass

    def set_command_set(self):
        self.command_set = True
        print('\tCommand set:', self.command)
        return self

    def select(self, table, columns='*'):
        if type(columns) in (list, tuple):
            columns = tuple(map(lambda column: '`' + column + '`', columns))
            columns = ', '.join(columns)
        self.command = "SELECT %s FROM %s" % (columns, table)
        self.set_command_set()
        return self

    def update(self, table, columns=None, values=None, dict_columns_values=None):
        if dict_columns_values != None:
            columns = list(dict_columns_values.keys())
            # values = list(dict_columns_values.values())
            self.values = tuple(dict_columns_values.values())

        # self.values = self.__preprocess_list_values(values)

        # key_val_pairs = list()
        # for col, val in zip(columns, values):
            # key_val_pairs.append("%s=%s" % (col, val))
        # key_val_pairs = ', '.join(key_val_pairs)

        key_val_pairs = ', '.join(tuple(map(lambda col: col + '=%s', columns)))

        self.command = "UPDATE %s SET %s" % (table, key_val_pairs)
        self.set_command_set()
        return self

    def insert(self, table, columns=None, values=None, dict_columns_values=None):
        if dict_columns_values != None:
            columns = list(dict_columns_values.keys())
            self.values = tuple(dict_columns_values.values())

        # self.values = self.__preprocess_list_values(values)
        self.command = "INSERT INTO %s (%s) VALUES (" % (table, ', '.join(columns))\
            + ', '.join(['%s'] * len(columns))\
            + ")"
        self.set_command_set()
        return self

    def __preprocess_list_values(self, values):
        for i, val in enumerate(values):
            if type(val) == str:
                values[i] = "'%s'" % val
            elif type(val) == int:
                values[i] = str(val)
            elif val == None:
                values[i] = "NULL"
            else:
                raise TypeError(
                    'Type of value cannot be processed:', val, type(val))
        print('Preprocessed values:', values)
        return values

    def reset(self):
        self.init_command()
        self.init_list_where_clauses()
        self.init_list_order_clauses()

    def init_command(self):
        self.command = None
        self.command_set = False
        self.values = None
        return self

    def init_list_where_clauses(self, index=None):
        if index != None:
            pop = self.list_where_clauses.pop(index)
            print('\tlist_where_clauses[%d] popped:' % index, pop)
        else:
            self.list_where_clauses = []
        return self

    def init_list_order_clauses(self, index=None):
        if index != None:
            pop = self.list_order_clauses.pop(index)
            print('\tlist_order_clauses[%d] popped:' % index, pop)
        else:
            self.list_order_clauses = []
        return self

    def get_sql_vals(self, mode_where='and', reset=True):
        if not self.command_set:
            raise ValueError('Command not set.')

        # Start sql
        self.last_sql = self.command

        # WHERE
        if self.list_where_clauses:
            self.last_sql = "%s WHERE %s" % (
                self.command, self.get_where_from_list(self.list_where_clauses, mode_where))

        # ORDER BY
        if self.list_order_clauses:
            self.last_sql = "%s ORDER BY %s" % (
                self.last_sql, self.get_order_by_from_list(self.list_order_clauses))

        # End sql
        self.last_sql += ';'

        self.last_values = self.values
        print('\tsql:', self.last_sql)
        if reset:
            self.reset()
        return (self.last_sql, self.last_values)

    def where(self, column, value, mode='='):
        # Param 'mode' could be: '=', 'match'
        if mode == '=':
            if value == None:
                clause = "`%s` IS NULL" % column
            else:
                clause = "`%s`=%d" % (column, value) \
                    if type(value) != str else "`%s`='%s'" % (column, value)
        
        elif mode == '>':
            clause = "`%s`>%d" % (column, value) \
                if type(value) != str else "`%s`>'%s'" % (column, value)

        elif mode == '<':
            clause = "`%s`<%d" % (column, value) \
                if type(value) != str else "`%s`<'%s'" % (column, value)
                
        elif mode == 'fulltext_list':
            self.__check_type(value, 'str')
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
        print('\tCurrent list_where_clauses:', self.list_where_clauses)
        return self

    def order_by(self, columns=None, orders=None, dict_columns_orders=None):
        if dict_columns_orders != None:
            columns = tuple(dict_columns_orders.keys())
            # print('dict_columns_orders.values(): ', dict_columns_orders.values())
            orders = tuple(
                map(lambda order: self.dict_order[order], dict_columns_orders.values()))
            # print('orders: ', orders)

        for col, order in zip(columns, orders):
            clause = '%s %s' % (col, order)
            if clause not in self.list_order_clauses:
                self.list_order_clauses.append(clause)
        print('\tCurrent list_order_clauses:', self.list_order_clauses)
        return self

    def __check_type(self, value, type_targets='str'):
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
        # print('\tWhere:', where)
        return where

    def get_order_by_from_list(self, list_clauses):
        # if len(list_clauses):
        # order_by = 'ORDER BY ' + ' '.join(list_clauses)
        # else:
        # order_by = ''
        return ' '.join(list_clauses)
