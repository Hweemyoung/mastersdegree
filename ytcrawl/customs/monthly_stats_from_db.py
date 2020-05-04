from db_handler import DBHandler

class StatsOrganizer(DBHandler):
    def get_videos_from_db(self, where={'equal':{'idx': 3}, 'match':{'q': 'url'}}):
        where('q', 'url', 'match')
        where('idx', 3, 'equal')

        where
        sql = "SELECT * FROM VIDEOS WHERE "