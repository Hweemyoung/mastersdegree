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

    def __init__(self, df_scopus, df_sources, table_name):
        self.df_scopus = df_scopus
        self.df_sources = df_sources
        self.table_name = table_name
    
    def __parse_fetches(self, fetches):
        _new_fetches = list()
        for _fetch in fetches:
            for _doi in _fetch[0].split(", "):
                _new_fetches.append(
                    (_doi, _fetch[1])
                )
        return _new_fetches
    
    def set_target_videos(self, where=None, days_from=None, days_until=None):
        _list_columns = ["idx", "videoId", "idx_paper", "publishedAt"]
        self.db_handler.sql_handler.select(self.table_name, _list_columns)
        if type(where) == tuple:
            self.db_handler.sql_handler.where(*where)
        self.list_videos_total = self.db_handler.execute().fetchall()
        # self.list_videos_total = self.__parse_fetches(self.list_videos_total)
        
        self.list_target_videos = list()
        for _row in self.list_videos_total:
            # Select by DOI
            _target_paper = self.df_scopus[self.df_scopus["DOI"] == _row[2]]
            # If Multiple rows with same DOI
            if len(_target_paper) > 1:
                _target_paper = _target_paper.iloc[0]
            
            # Filter by DT
            _dt_publish = datetime(_target_paper["Year"], _target_paper["Month"], 1)
            if days_from != None:
                _dt_video_from = _dt_publish + timedelta(days=days_from)
                if _row[3] < _dt_video_from:
                    continue
            if days_until != None:
                _dt_video_until = _dt_publish + timedelta(days=days_until)
                if _row[3] > _dt_video_until:
                    continue
            
            self.list_target_videos.append(_row)
        
        self.__set_stats()
        
        return self

    def __set_stats(self, where=None, days_from=None, days_until=None):
        self.idx_papers = set(map(lambda _row: _row[2], self.list_target_videos))
        _num_total_dois = len(set(self.df_scopus["DOI"]))
        print("# Total DOIs: %d\t# DOIs w/ videos: %d\tRatio: %.3f" % (_num_total_dois, len(self.idx_papers), len(self.idx_papers) / _num_total_dois))

        self.sources_w_videos = set(self.df_scopus[self.df_scopus["DOI"].isin(self.idx_papers)]["Source title"])
        # _num_total_sources = len(set(self.df_scopus["Source title"]))
        # _num_total_sources = len(set(self.df_scopus["Source title"]))
        # print("# Total sources: %d\t# Sources w/ videos: %d\tRatio: %.3f" % (_num_total_sources, len(self.idx_papers), len(self.idx_papers) / _num_total_sources))

        self.target_videos = set(map(lambda _row: _row[1], self.list_target_videos))
        _num_total_videos = len(set(map(lambda _row: _row[1], self.list_videos_total)))
        print("# Total videos: %d\t# Target videos: %d\tRatio: %.3f" % (_num_total_videos, len(self.target_videos), len(self.target_videos) / _num_total_videos))

        self.__set_value_counts()
        
        return self

    def __set_value_counts(self):
        self.subjects_total = self.df_scopus["Scopus Sub-Subject Area"].value_counts()
        self.subjects_w_videos = self.df_scopus[self.df_scopus["DOI"].isin(self.idx_papers)]["Scopus Sub-Subject Area"].value_counts()
        self.subjects_total_w_videos = self.subjects_w_videos.reindex(self.subjects_total.index, fill_value=0)
        print("# Total subjects: %d\t# subjects w/ videos: %d\tRatio: %.3f" % (len(self.subjects_total.index), len(self.subjects_w_videos.index), len(self.subjects_w_videos.index) / len(self.subjects_total.index)))
        self.ratio_by_subject = self.subjects_total_w_videos / self.subjects_total

        # self.df_sources_in_scopus = self.df_sources[self.df_sources["Source title"].isin(set(self.df_scopus["Source title"]))]
        # self.df_citescores = pd.DataFrame(self.df_sources_in_scopus["CiteScore"], index=self.df_sources_in_scopus["Source title"])
        self.df_sources_in_scopus = self.df_sources[self.df_sources["Source title"].isin(set(self.df_scopus["Source title"]))]

        self.journals_total = self.df_scopus["Source title"].value_counts()
        self.journals_w_videos = self.df_scopus[self.df_scopus["DOI"].isin(self.idx_papers)]["Source title"].value_counts()
        self.journals_total_w_videos = self.journals_w_videos.reindex(self.journals_total.index, fill_value=0)
        print("# Total journals: %d\t# journals w/ videos: %d\tRatio: %.3f" % (len(self.journals_total.index), len(self.journals_w_videos.index), len(self.journals_w_videos.index) / len(self.journals_total.index)))
        self.ratio_by_journal = self.journals_total_w_videos / self.journals_total
        
        self.journals_scores = pd.Series(self.df_sources_in_scopus["CiteScore"].values, index=self.df_sources_in_scopus["Source title"])
        # self.journals_w_videos = self.df_scopus[self.df_scopus["DOI"].isin(self.idx_papers)]["Source title"].value_counts()
        self.journals_papers_w_videos = self.journals_w_videos.reindex(self.journals_scores.index, fill_value=0)
        # print("# Total journals: %d\t# journals w/ videos: %d\tRatio: %.3f" % (len(self.journals_scores.index), len(self.journals_w_videos.index), len(self.journals_w_videos.index) / len(self.journals_scores.index)))
        # self.ratio_by_journal = self.journals_papers_w_videos / self.journals_scores

        self.df_papers_w_video_scores = pd.DataFrame([self.journals_w_videos, self.journals_scores], index=["# Papers w/ videos", "CiteScore"]).T.dropna()
        
        return self

    def plot_sub_subjects_chart(self, where=None, days_from=None, days_until=None):
        # self.set_videos()
        # self.set_idx_papers(where, days_from, days_until)
        self.set_target_videos(where, days_from, days_until)
        
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
    
    def plot_journals_papers(self, where=None, days_from=None, days_until=None):
        # self.set_videos()
        # self.set_idx_papers(where, days_from, days_until)
        self.set_target_videos(where, days_from, days_until)
        
        plt.figure(figsize=(12, 6))
        
        plt.fill_between(
            np.arange(len(self.journals_total)),
            self.journals_total,
            color="skyblue",
            alpha=0.4,
            label='# Papers(Total)'
        )

        plt.bar(
            np.arange(len(self.journals_total_w_videos)),
            self.journals_total_w_videos,
            width=0.4,
            label='# Papers(w/ videos)'
        )

        plt.tick_params(labelsize=12)
        plt.xticks(np.arange(len(self.journals_total)), self.journals_total.index, rotation=90)
        plt.xlabel('Journal', size=12)
        plt.ylabel('Count', size=12)
        plt.yscale("log")
        # plt.ylim(bottom=0)
    #     plt.legend(labels=['# Papers(Total)', '# Papers(w/ videos)'])
        plt.legend()

        plt.show()

        return self
    
    def plot_journals_scores(self, where=None, days_from=None, days_until=None):
        # self.set_videos()
        # self.set_idx_papers(where, days_from, days_until)
        self.set_target_videos(where, days_from, days_until)
        
        plt.figure(figsize=(12, 6))
        
        plt.fill_between(
            np.arange(len(self.journals_scores)),
            self.journals_scores,
            color="skyblue",
            alpha=0.4,
            label='Journal CiteScores'
        )

        plt.bar(
            np.arange(len(self.journals_papers_w_videos)),
            self.journals_papers_w_videos,
            width=0.4,
            label='# Papers w/ videos'
        )

        plt.tick_params(labelsize=12)
        plt.xticks(np.arange(len(self.journals_scores)), self.journals_scores.index, rotation=90)
        plt.xlabel('Journal', size=12)
        plt.ylabel('Score|Count', size=12)
        plt.yscale("log")
        # plt.ylim(bottom=0)
    #     plt.legend(labels=['# Papers(Total)', '# Papers(w/ videos)'])
        plt.legend()

        plt.show()

        return self
    