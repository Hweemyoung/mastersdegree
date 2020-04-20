import mysql.connector


class DBUploader:
    def __init__(self, host='localhost', user='root', passwd='111111', database='ytcrawl0'):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd,
            database=database
        )
        self.mycursor = self.conn.cursor()
    
    def close(self):
        self.conn.close()