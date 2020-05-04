from preprocessor import Preprocessor
from db_handler import DBHandler

class SQLHandler(DBHandler):
    command = ''
    command_set = False
    list_where_clauses = []
    dict_where_conj = {'and': ' AND ', 'or': ' OR '}

    def __init__(self):
        pass

    def select(self, table, columns='*'):
        if type(columns) in (list, tuple):
            columns = map(lambda column: '`' + column + '`', columns)
            columns = ', '.join(columns)
        self.command = "SELECT %s FROM %s" % (columns, table)
        print('Command set:', self.command)
        return self

    def init_list_where_clauses(self):
        self.list_where_clauses = []

    def get_sql(self, command, mode_where='and'):
        if not self.command_set:
            raise ValueError('Command not set.')
        sql = "%s WHERE %s;" % (
            self.command, self.get_where_from_list(self.list_where_clauses, mode_where))
        print('sql:', sql)
        return sql

    def where(self, column, value, mode='equal'):
        # Param 'mode' could be: 'equal', 'match'
        if mode == 'equal':
            clause = "`%s`=%d" % (column, value) \
                if type(value) != str else "`%s`='%s'" % (column, value)
        elif mode == 'fulltext_list':
            self.check_type(value, str)
            list_clauses = []

            list_clauses.append(
                "match(%s) against (%s, in boolean mode)" % (column, value))
            list_clauses.append(
                "match(%s) against ( %s in boolean mode)" % (column, value))
            list_clauses.append(
                "`%s`=%s" % (column, value))

            clause = self.get_where_from_list(list_clauses, 'or')
        elif mode == 'fulltext':
            clause = "match(%s) against (%s in boolean mode)" % (column, value)
        else:
            raise ValueError()

        if clause not in self.list_where_clauses:
            self.list_where_clauses.append(clause)
        print('Current list_where_clauses:', self.list_where_clauses)
        return self

    def check_type(self, value, type_targets):
        if type(type_targets) not in (list, tuple):
            if type(value) != type_targets:
                raise TypeError(value, '- Type expected:',
                            type_targets, '; Type given:', type(value))
        else:
            if type(value) not in type_targets:
                raise TypeError(value, '- Type expected:',
                                type_targets, '; Type given:', type(value))
        return self

    def get_where_from_list(self, list_clauses, mode='and'):
        if len(list_clauses):
            conj = self.dict_where_conj[mode]
            where = '(' + conj.join(list_clauses) + ')'
        else:
            where = '1'
        print('Where:', where)
        return where
