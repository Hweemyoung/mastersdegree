import numpy as np
import pandas as pd
from db_handler import DBHandler
from matplotlib import pyplot as plt
from scipy import stats
from datetime import datetime, timedelta
from calendar import monthrange
class ScopusHandler:
    db_handler = DBHandler()
    videos = None
    idx_papers = None
    subjects_total = None
    subjects_w_videos = None
    subjects_total_w_videos = None

    def __init__(self, df, table_name):
        self.df = df
        self.table_name = table_name
    
    def parse_fetches(self, fetches):
        _new_fetches = list()
        for _fetch in fetches:
            for _doi in _fetch[0].split(", "):
                _new_fetches.append(
                    (_doi, _fetch[1])
                )
        return _new_fetches
    
    def get_dois_with_videos_within_days_from_publish(self, df, table_name, where=None, days_from=None, days_until=None):
    #     複数の動画が与えられる論文の場合、複数のsetに含まれることがある。
        _set_target_dois = set()
        self.db_handler.sql_handler.select(table_name, ["idx_paper", "publishedAt"])
        if type(where) == tuple:
            self.db_handler.sql_handler.where(*where)
        fetches = self.db_handler.execute().fetchall()
        fetches = self.parse_fetches(fetches)
        
        for _row in fetches:
    #         print("DOI:", _row[0])
            _target_paper = df[df["DOI"] == _row[0]]
    #         if len(_target_paper) == 0:
    #             continue
            if len(_target_paper) > 1:
                _target_paper = _target_paper.iloc[0]
    #         print(_target_paper)
            _dt_publish = datetime(_target_paper["Year"], _target_paper["Month"], 1)
            
            if days_from != None:
                _dt_video_from = _dt_publish + timedelta(days=days_from)
                if _row[1] < _dt_video_from:
                    continue
            
            if days_until != None:
                _dt_video_until = _dt_publish + timedelta(days=days_until)
                if _row[1] > _dt_video_until:
                    continue
            
            _set_target_dois.add(_row[0])
        
    #     if days_until == None:
    #         _set_target_dois = set(map(lambda _row: _row[0], fetches))
    #     else:
    #         for _row in fetches:
    #             _target_paper = df[df["DOI"] == _row[0]]
    #             if len(_target_paper) > 1:
    #                 _target_paper = _target_paper.iloc[0]
    #             _dt_publish = datetime(_target_paper["Year"], _target_paper["Month"], 1)
                
    #             _dt_video_from = _dt_publish + timedelta(days=days_from)
    #             _dt_video_until = _dt_publish + timedelta(days=days_until)
                
    #             if _row[1] < _dt_video_deadline:
    #                 _set_target_dois.add(_row[0])
        
        return _set_target_dois
    
    def set_videos(self):
        self.db_handler.sql_handler.select(self.table_name, ["idx_paper", "publishedAt"])
        self.videos = self.db_handler.execute().fetchall()
        return self

    def set_idx_papers(self, where=None, days_from=None, days_until=None):
        self.idx_papers = self.get_dois_with_videos_within_days_from_publish(self.df, self.table_name, where, days_from, days_until)
        print("# Total papers: %d\t# papers w/ videos: %d\tRatio: %.3f" % (len(set(self.df["DOI"])), len(self.idx_papers), len(self.idx_papers) / len(set(self.df["DOI"]))))
        return self

    def set_value_counts(self):
        self.subjects_total = self.df["Scopus Sub-Subject Area"].value_counts()
        self.subjects_w_videos = self.df[self.df["DOI"].isin(self.idx_papers)]["Scopus Sub-Subject Area"].value_counts()
        self.subjects_total_w_videos = self.subjects_w_videos.reindex(self.subjects_total.index, fill_value=0)
        print("# Total subjects: %d\t# subjects w/ videos: %d\tRatio: %.3f" % (len(self.subjects_total.index), len(self.subjects_w_videos.index), len(self.subjects_w_videos.index) / len(self.subjects_total.index)))
        return self

    def plot_area_chart(self, where=None, days_from=None, days_until=None):
        self.set_videos()
        self.set_idx_papers(where, days_from, days_until)
        self.set_value_counts()
        
        plt.figure(figsize=(12, 6))
        
        plt.fill_between(
            np.arange(len(self.subjects_total)),
            self.subjects_total,
            color="skyblue",
            alpha=0.4,
            label='# Papers(Total)'
        )

        plt.bar(
            np.arange(len(self.subjects_total_w_videos)),
            self.subjects_total_w_videos,
            width=0.4,
            label='# Papers(w/ videos)'
        )
        
    #     plt.plot(
    #         np.arange(len(self.subjects_total)),
    #         self.subjects_total,
    #         color="Slateblue",
    #         alpha=0.6,
    #         linewidth=2
    #     )

    #     plt.fill_between(
    #         np.arange(len(self.subjects_total_w_videos)),
    #         self.subjects_total_w_videos,
    #         color="lightpink",
    #         alpha=0.5,
    #         label='# Papers(w/ videos)'
    #     )

    #     plt.plot(
    #         np.arange(len(self.subjects_total_w_videos)),
    #         self.subjects_total_w_videos,
    #         color="pink",
    #         alpha=0.6,
    #         linewidth=2
    #     )

        plt.tick_params(labelsize=12)
        plt.xticks(np.arange(len(self.subjects_total)), self.subjects_total.index, rotation=90)
        plt.xlabel('Sub-Subject', size=12)
        plt.ylabel('Count', size=12)
        plt.yscale("log")
        # plt.ylim(bottom=0)
    #     plt.legend(labels=['# Papers(Total)', '# Papers(w/ videos)'])
        plt.legend()

        plt.show()

        return self