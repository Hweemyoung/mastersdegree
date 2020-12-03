import numpy as np
import pandas as pd
from db_handler import DBHandler
from matplotlib import pyplot as plt
from scipy import stats
from datetime import datetime, timedelta
from calendar import monthrange
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


class ScopusHandler:
    db_handler = DBHandler()
    videos = None
    idx_papers = None
    subjects_total = None
    subjects_w_videos = None
    subjects_total_w_videos = None

    # Clustering
    embedder = None
    pretrained_model = None
    corpus_embeddings = None
    pca = None
    num_clusters = None
    clustering_model = None
    clustered_abs = None
    clustered_embeddings = None
    clustered_pca = None
    clustered_titles = None
    clustered_subjects = None
    dict_key_clusters = {
        "abs": None,
        "embeddings": None,
        "pca": None,
        "titles": None,
        "subjects": None
    }

    def __init__(self, df_scopus, df_sources, table_name):
        self.df_scopus = df_scopus.drop_duplicates(subset=["DOI"])
        print("[+]Duplicates have been dropped from df_scopus.\tBefore: %d\tAfter: %d" %
              (len(df_scopus), len(self.df_scopus)))
        self.df_sources = df_sources
        self.table_name = table_name
        self.dict_key_clusters = {
            "abs": self.clustered_abs,
            "embeddings": self.clustered_embeddings,
            "pca": self.clustered_pca,
            "titles": self.clustered_titles,
            "subjects": self.clustered_subjects
        }

    def __parse_fetches(self, fetches):
        _new_fetches = list()
        for _fetch in fetches:
            for _doi in _fetch[0].split(", "):
                _new_fetches.append(
                    (_doi, _fetch[1])
                )
        return _new_fetches

    def set_target_videos(self, df_scopus=None, where=None, days_from=None, days_until=None):
        _list_columns = ["idx", "videoId", "idx_paper", "publishedAt"]
        self.db_handler.sql_handler.select(self.table_name, _list_columns)
        if type(where) == tuple:
            self.db_handler.sql_handler.where(*where)
        elif type(where) == list:
            for _where in where:
                if type(_where) == tuple:
                    self.db_handler.sql_handler.where(*_where)

        self.list_videos_total = self.db_handler.execute().fetchall()
        # self.list_videos_total = self.__parse_fetches(self.list_videos_total)

        self.list_target_videos = list()

        if type(df_scopus) == type(None):
            df_scopus = self.df_scopus

        for _row in self.list_videos_total:
            # Select by DOI
            _target_paper = df_scopus[df_scopus["DOI"] == _row[2]]
            # print(_target_paper)
            # If Multiple rows with same DOI
            if len(_target_paper) > 1:
                _target_paper = _target_paper.iloc[0]
            elif len(_target_paper) == 0:  # Could be filtered before the method
                continue

            # Filter by DT
            _dt_publish = datetime(
                _target_paper["Year"], _target_paper["Month"], 1)
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
        self.idx_papers = set(
            map(lambda _row: _row[2], self.list_target_videos))
        _num_total_dois = len(set(self.df_scopus["DOI"]))
        print("# Total DOIs: %d\t# DOIs w/ videos: %d\tRatio: %.3f" %
              (_num_total_dois, len(self.idx_papers), len(self.idx_papers) / _num_total_dois))

        self.sources_w_videos = set(
            self.df_scopus[self.df_scopus["DOI"].isin(self.idx_papers)]["Source title"])
        # _num_total_sources = len(set(self.df_scopus["Source title"]))
        # _num_total_sources = len(set(self.df_scopus["Source title"]))
        # print("# Total sources: %d\t# Sources w/ videos: %d\tRatio: %.3f" % (_num_total_sources, len(self.idx_papers), len(self.idx_papers) / _num_total_sources))

        self.target_videos = set(
            map(lambda _row: _row[1], self.list_target_videos))
        _num_total_videos = len(
            set(map(lambda _row: _row[1], self.list_videos_total)))
        print("# Total videos: %d\t# Target videos: %d\tRatio: %.3f" % (
            _num_total_videos, len(self.target_videos), len(self.target_videos) / _num_total_videos))

        self.__set_value_counts()

        return self

    def __set_value_counts(self):
        self.subjects_total = self.df_scopus["Scopus Sub-Subject Area"].value_counts()
        self.subjects_w_videos = self.df_scopus[self.df_scopus["DOI"].isin(
            self.idx_papers)]["Scopus Sub-Subject Area"].value_counts()
        self.subjects_total_w_videos = self.subjects_w_videos.reindex(
            self.subjects_total.index, fill_value=0)
        print("# Total subjects: %d\t# subjects w/ videos: %d\tRatio: %.3f" % (len(self.subjects_total.index),
                                                                               len(self.subjects_w_videos.index), len(self.subjects_w_videos.index) / len(self.subjects_total.index)))
        self.ratio_by_subject = self.subjects_total_w_videos / self.subjects_total

        # self.df_sources_in_scopus = self.df_sources[self.df_sources["Source title"].isin(set(self.df_scopus["Source title"]))]
        # self.df_citescores = pd.DataFrame(self.df_sources_in_scopus["CiteScore"], index=self.df_sources_in_scopus["Source title"])
        self.df_sources_in_scopus = self.df_sources[self.df_sources["Source title"].isin(
            set(self.df_scopus["Source title"]))]

        self.journals_total = self.df_scopus["Source title"].value_counts()
        self.journals_w_videos = self.df_scopus[self.df_scopus["DOI"].isin(
            self.idx_papers)]["Source title"].value_counts()
        self.journals_total_w_videos = self.journals_w_videos.reindex(
            self.journals_total.index, fill_value=0)
        print("# Total journals: %d\t# journals w/ videos: %d\tRatio: %.3f" % (len(self.journals_total.index),
                                                                               len(self.journals_w_videos.index), len(self.journals_w_videos.index) / len(self.journals_total.index)))
        self.ratio_by_journal = self.journals_total_w_videos / self.journals_total

        self.journals_scores = pd.Series(
            self.df_sources_in_scopus["CiteScore"].values, index=self.df_sources_in_scopus["Source title"])
        # self.journals_w_videos = self.df_scopus[self.df_scopus["DOI"].isin(self.idx_papers)]["Source title"].value_counts()
        self.journals_papers_w_videos = self.journals_w_videos.reindex(
            self.journals_scores.index, fill_value=0)
        # print("# Total journals: %d\t# journals w/ videos: %d\tRatio: %.3f" % (len(self.journals_scores.index), len(self.journals_w_videos.index), len(self.journals_w_videos.index) / len(self.journals_scores.index)))
        # self.ratio_by_journal = self.journals_papers_w_videos / self.journals_scores

        self.df_papers_w_video_scores = pd.DataFrame([self.journals_w_videos, self.journals_scores], index=[
                                                     "# Papers w/ videos", "CiteScore"]).T.dropna()

        return self

    def plot_box_by_video(self, where=None, days_from=None, days_until=None, scopus_column="Cited by"):
        self.db_handler.sql_handler.select(
            self.table_name, ["idx_paper", "publishedAt"])
        _videos = self.db_handler.execute().fetchall()
        _idx_papers = self.set_target_videos(
            self.df_scopus, where=where, days_from=days_from, days_until=days_until)

        _wo_videos_cit = np.log10(self.df_scopus[~self.df_scopus.DOI.isin(
            _idx_papers)][scopus_column].dropna().astype(int))
        _w_videos_cit = np.log10(self.df_scopus[self.df_scopus.DOI.isin(
            _idx_papers)][scopus_column].dropna().astype(int))

        plt.figure(figsize=(10, 6))
        plt.title("Citation")
        # plt.yscale("log")
        # plt.ylim([0, 200])
        plt.ylabel("log10(Citation)")
        plt.boxplot([
            _wo_videos_cit,
            _w_videos_cit
        ],
            labels=[
                "w/o videos\n(N=%s)" % len(_wo_videos_cit),
                "w/ videos\n(N=%s)" % len(_w_videos_cit)
        ]
        )

    def plot_box_by_journals(self, where=None, days_from=None, days_until=None, scopus_column="Cited by", ncols=10):
        self.set_target_videos(self.df_scopus, where=where,
                               days_from=days_from, days_until=days_until)
        _idx_papers = list(
            map(lambda _row: _row[2], self.list_target_videos))  # Get DOIs

        # Set subsubjects
        self._set_subsubjects = set(self.df_sources["Scopus Sub-Subject Area"])
        self._dict_subsubjects_values = dict()
        self._list_subsubjects_values = list()
        for _subsubject in self._set_subsubjects:
            self._target_sources = set(
                self.df_sources[self.df_sources["Scopus Sub-Subject Area"] == _subsubject]["Source title"])
            self._target_papers = self.df_scopus[self.df_scopus["Source title"].isin(
                self._target_sources)]
            if not len(self._target_papers[self._target_papers["DOI"].isin(_idx_papers)]):
                continue
            self._list_subsubjects_values.append(
                (
                    _subsubject,
                    np.log10(self._target_papers[~self._target_papers["DOI"].isin(
                        _idx_papers)][scopus_column].dropna().astype(int)),
                    np.log10(self._target_papers[self._target_papers["DOI"].isin(
                        _idx_papers)][scopus_column].dropna().astype(int))
                )
            )

        # Sort
        # self._list_subsubjects_values = sorted(self._list_subsubjects_values, key=lambda _list: np.mean(_list[1]), reverse=True)  # Sort by mean values of w/o group
        self._list_subsubjects_values = sorted(self._list_subsubjects_values, key=lambda _list: len(
            _list[2]), reverse=True)  # Sort by number of w/ group

        # Plot top values only
        if type(ncols) != type(None):
            self._list_subsubjects_values = self._list_subsubjects_values[:ncols]

        fig, axes = plt.subplots(
            ncols=len(self._list_subsubjects_values), figsize=(16, 6), sharey=True)
        fig.subplots_adjust(wspace=0)

        for _i, _values in enumerate(self._list_subsubjects_values):
            axes[_i].boxplot(_values[1:3], showmeans=True)
            _xticklabels = ["w/o\n(N=%d)" % len(_values[1]),
                            "w/\n(N=%d)" % len(_values[2])]
            axes[_i].set_xticklabels(_xticklabels, fontsize=12)
            axes[_i].set_xlabel(_values[0].replace(" ", "\n"), fontsize=12)
            axes[_i].margins(0.05)  # Optional

        fig.suptitle(scopus_column)
        fig.add_subplot(111, frameon=False)
        plt.tick_params(labelcolor='none', top=False,
                        bottom=False, left=False, right=False)
        plt.ylabel("log10(%s)" % scopus_column)
    #     plt.xlabel(label_by)
    #     plt.yscale("log")
        plt.show()

    def cluster_scopus(self, target_column="Abstract", num_clusters=None, train_kmeans=True, pca_components=2, pretrained_model="distilbert-base-nli-stsb-mean-tokens", videos_only=True):
        if type(pca_components) != int or pca_components > 3 or pca_components < 2:
            raise ValueError(
                "[-]Argument 'pca_components' must be either 2 or 3.")

        if self.embedder == None or self.pretrained_model != pretrained_model:
            print("[+]Assigning new embedder instance.")
            self.embedder = SentenceTransformer(pretrained_model)
            self.pretrained_model = pretrained_model

        if target_column == "Abstract":
            _df_scopus_filtered = self.df_scopus[self.df_scopus["Abstract"]
                                                 != "[No abstract available]"]
        else:
            _df_scopus_filtered = self.df_scopus.copy()

        self.set_target_videos(_df_scopus_filtered)

        # Papers w/ videos
        _target_scopus = _df_scopus_filtered[_df_scopus_filtered["DOI"].isin(
            self.idx_papers)] if videos_only else _df_scopus_filtered
        _list_corpus = list(_target_scopus[target_column])
        _list_corpus = list(map(lambda abs: abs.split("©")[0], _list_corpus))
        _list_titles = list(_target_scopus["Title"])
        _list_subjects = list(_target_scopus["Scopus Sub-Subject Area"])

        print("# Total elements in plot: %d" % len(_list_corpus))

        # Encode corpus
        self.corpus_embeddings = self.embedder.encode(_list_corpus)

        # Perform kmean clustering
        if self.clustering_model == None or num_clusters != None:
            self.num_clusters = num_clusters
            self.clustering_model = KMeans(n_clusters=self.num_clusters)
        if train_kmeans:
            self.clustering_model.fit(self.corpus_embeddings)

        # PCA
        self.pca = PCA(n_components=pca_components)
        _corpus_pca = self.pca.fit_transform(self.corpus_embeddings)

        self.clustered_abs = [[] for i in range(self.num_clusters)]
        self.clustered_embeddings = [[] for i in range(self.num_clusters)]
        self.clustered_pca = [[] for i in range(self.num_clusters)]
        self.clustered_titles = [[] for i in range(self.num_clusters)]
        self.clustered_subjects = [[] for i in range(self.num_clusters)]

        # Array of cluster index
        for sentence_id, cluster_id in enumerate(self.clustering_model.labels_):
            self.clustered_abs[cluster_id].append(_list_corpus[sentence_id])
            self.clustered_embeddings[cluster_id].append(
                self.corpus_embeddings[sentence_id])
            self.clustered_pca[cluster_id].append(_corpus_pca[sentence_id])
            self.clustered_titles[cluster_id].append(_list_titles[sentence_id])
            self.clustered_subjects[cluster_id].append(
                _list_subjects[sentence_id])

        # Describe clusters
        # self.desc_clusters("titles")

        if pca_components == 2:
            plt.scatter(_corpus_pca[:, 0], _corpus_pca[:, 1],
                        c=self.clustering_model.labels_)
            plt.show()

        elif pca_components == 3:
            fig = plt.figure(figsize=(14, 14))
            ax = fig.add_subplot(111, projection="3d")
            ax.scatter(_corpus_pca[:, 0], _corpus_pca[:, 1],
                       _corpus_pca[:, 2], c=self.clustering_model.labels_)
            plt.show()

        return self

    def desc_clusters(self, cluster_key):
        _set_titles = set(self.df_scopus[self.df_scopus["DOI"].isin(
            self.idx_papers)]["Title"])  # For subjects only

        for _i, _cluster in enumerate(self.dict_key_clusters[cluster_key]):
            print("Cluster %d(N=%d)" % (_i+1, len(_cluster)))
            if cluster_key == "subjects":
                # Intersection
                _intersection = set(
                    self.clustered_titles[_i]).intersection(_set_titles)
                print("\t# intersection: %d" % len(_intersection))
                if len(_intersection):
                    print("\t\t", _intersection)

                # Subject counts
                _dict_subject_count = dict()
                for _subject in set(_cluster):
                    _dict_subject_count[_subject] = _cluster.count(_subject)
                for _subject, _count in sorted(_dict_subject_count.items(), key=lambda _item: _item[1]):
                    print("\t%s\t%d" % (_subject, _count))

            else:
                print(_cluster)
                print("")

        return self

    def plot_sub_subjects_chart(self, where=None, days_from=None, days_until=None):
        # self.set_videos()
        # self.set_idx_papers(where, days_from, days_until)
        self.set_target_videos(self.df_scopus, where, days_from, days_until)

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
        plt.xticks(np.arange(len(self.subjects_total)),
                   self.subjects_total.index, rotation=90)
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
        self.set_target_videos(self.df_scopus, where, days_from, days_until)

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
        plt.xticks(np.arange(len(self.journals_total)),
                   self.journals_total.index, rotation=90)
        plt.xlabel('Journal', size=12)
        plt.ylabel('Count', size=12)
        plt.yscale("log")
        # plt.ylim(bottom=0)
    #     plt.legend(labels=['# Papers(Total)', '# Papers(w/ videos)'])
        plt.legend()

        plt.show()

        return self

    def plot_journals_scores(self, where=None, days_from=None, days_until=None, figsize=(12, 6)):
        # self.set_videos()
        # self.set_idx_papers(where, days_from, days_until)
        self.set_target_videos(self.df_scopus, where, days_from, days_until)

        self.__desc_journals_scores()

    #     plt.figure(figsize=figsize)

    #     plt.fill_between(
    #         np.arange(len(self.journals_scores)),
    #         self.journals_scores,
    #         color="skyblue",
    #         alpha=0.4,
    #         label='Journal CiteScores'
    #     )

    #     plt.bar(
    #         np.arange(len(self.journals_papers_w_videos)),
    #         self.journals_papers_w_videos,
    #         width=0.4,
    #         label='# Papers w/ videos'
    #     )

    #     plt.tick_params(labelsize=12)
    #     plt.xticks(np.arange(len(self.journals_scores)), self.journals_scores.index, rotation=90)
    #     plt.xlabel('Journal', size=12)
    #     plt.ylabel('Score|Count', size=12)
    #     plt.yscale("log")
    #     # plt.ylim(bottom=0)
    # #     plt.legend(labels=['# Papers(Total)', '# Papers(w/ videos)'])
    #     plt.legend()

    #     plt.show()
        fig, ax1 = plt.subplots(figsize=figsize)

        _fill = ax1.fill_between(
            np.arange(len(self.journals_scores)),
            self.journals_scores,
            color="skyblue",
            alpha=0.4,
            label='Journal CiteScores(Left)'
        )
        ax1.tick_params(labelsize=12)
        ax1.set_xticks(np.arange(len(self.journals_scores)))
        ax1.set_xticklabels(self.journals_scores.index, size=12, rotation=90)
        ax1.set_xlabel('Journal', size=12)
        ax1.set_ylabel('Score', size=12)
        ax1.set_ylim(1)
        ax1.set_yscale("log")

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

        _bar = ax2.bar(
            np.arange(len(self.journals_papers_w_videos)),
            self.journals_papers_w_videos,
            width=0.4,
            label='# Papers w/ videos(Right)'
        )
        ax2.tick_params(labelsize=12)
        ax2.set_ylabel('Count', size=12)
        ax2.set_yscale("log")
        ax2.set_ylim(0.9, 30)

        # fig.tight_layout()  # otherwise the right y-label is slightly clipped
        # _plots = _fill + _bar
        ax1.legend([_fill, _bar], [_fill.get_label(), _bar.get_label()])
        # ax2.legend()
        plt.show()

        return self

    def __desc_journals_scores(self, partition=5):
        _size = len(self.journals_papers_w_videos) / partition
        _list_sum_journals, _list_sum_papers = list(), list()
        for _i in range(0, partition):
            _target = self.journals_papers_w_videos.iloc[int(
                _size * _i): int(_size * (_i + 1))]
            _list_sum_journals.append(len(_target[_target != 0]))
            _list_sum_papers.append(_target.sum())

        print("Journals:\tMean: %.1f\tStd: %.2f" %
              (np.mean(_list_sum_journals), np.std(_list_sum_journals)))
        print("Papers:\tMean: %.1f\tStd: %.2f" %
              (np.mean(_list_sum_papers), np.std(_list_sum_papers)))

        _norm_journals, _norm_papers = stats.zscore(
            _list_sum_journals), stats.zscore(_list_sum_papers)
        for _i in range(0, partition):
            print("Partition %d of %d" % (_i + 1, partition))
            print("# journals w/ videos(Z-value): %d(%.2f)\t# papers w/ videos(Z-value): %d(%.2f)" %
                  (_list_sum_journals[_i], _norm_journals[_i], _list_sum_papers[_i], _norm_papers[_i]))

        return self

    def model_metrics(self, paper_metric="Cited by", video_metric="viewCount", method="sum", log_scale=True):
        from paper_score import PaperScore
        # Get videos
        _list_columns = ["idx", "videoId", "content",
                         "idx_paper", "channelId", "viewCount"]
        self.db_handler.sql_handler.select(self.table_name, _list_columns)
        _list_videos = self.db_handler.execute().fetchall()

        # Transform rows into dicts
        _list_dict_videos = list(
            map(lambda _row: dict(zip(_list_columns, _row)), _list_videos))
        # Instantiate PaperScores
        _set_dois = set(map(lambda _row: _row[3], _list_videos))
        _temp_df_scopus = self.df_scopus[self.df_scopus[paper_metric].notna()]
        self._dict_paper_scores_by_doi = dict(zip(_set_dois, tuple(map(lambda _doi: PaperScore(
            _doi, _temp_df_scopus, paper_metric=paper_metric, video_metric=video_metric, log_scale=log_scale), _set_dois))))  # {_doi: PaperScore(_doi), ...}
        # Append videos to corresponding instances
        for _dict_video in _list_dict_videos:
            self._dict_paper_scores_by_doi[_dict_video["idx_paper"]].append_video(
                _dict_video)
        # Calc paper scores
        _list_points = list(map(lambda _instance: _instance.calc_ytscore(method=method).get_ytscore_meter(
        ), tuple(self._dict_paper_scores_by_doi.values())))  # [(ytscore, paper_meter), ...]
        # Get xs, ys
        self._xs = [_point[0] for _point in _list_points if None not in _point]
        self._ys = [_point[1] for _point in _list_points if None not in _point]
        # self._xs = list(map(lambda _point: _point[0], _list_points))
        # self._ys = list(map(lambda _point: _point[1], _list_points))
        
        # self._xs = list()
        # self._ys = list()
        # for _instance in self._dict_paper_scores_by_doi.values():
        #     _point = _instance.get_ytscore_meter()
        #     if type(_point) == type(None):
        #         continue
        #     self._xs.append(_point[0])
        #     self._ys.append(_point[1])
        # Scatter plot
        plt.scatter(self._xs, self._ys)
        plt.title("Modeling(N=%d)" % len(self._xs))
        plt.xlabel("YTscore\n(%s, %s)" % (video_metric, method))
        plt.ylabel("log10(%s)" % paper_metric) if log_scale else plt.ylabel(paper_metric)
        plt.show()
        
        return self
