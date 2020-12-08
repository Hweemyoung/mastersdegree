import numpy as np
import pandas as pd
from db_handler import DBHandler
# import matplotlib
# matplotlib.use( 'tkagg' )
from matplotlib import pyplot as plt
from scipy import stats
from datetime import datetime, timedelta
from calendar import monthrange
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


class ScopusHandler:
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
    
    _tup_idx_2019_life = (2, 3, 6, 10, 12, 17, 18, 38, 43, 50, 55, 56, 59, 67, 72, 73, 78, 86, 88, 90, 93, 94, 101, 108, 109, 110, 113, 116, 120, 122, 124, 128, 129, 130, 139, 140, 142, 145, 150, 153, 158, 159, 161, 163, 165, 166, 171, 175, 178, 181, 184, 190, 195, 199, 208, 209, 214, 217, 222, 223, 230, 232, 233, 238, 246, 247, 254, 256, 258, 264, 267, 270, 271, 275, 277, 281, 284, 286, 291, 292, 297, 298, 299, 300, 303, 305, 310, 311, 314, 316, 317, 318, 324, 326, 327, 330, 333, 334, 340, 343)

    def __init__(self, df_scopus, df_sources, table_name, title=None, verbose=True):
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
        self.title = title
        self.db_handler = DBHandler(verbose=verbose)

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
            elif len(_target_paper) == 0:
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
            axes[_i].set_xticklabels(_xticklabels, fontsize=10)
            axes[_i].set_xlabel(_values[0].replace(" ", "\n"), fontsize=10)
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

    def model_metrics(self, paper_metric="Cited by", video_metric="viewCount", method="sum", label_by=None, regression=False, where=None, log_scale=True):
        # label_by: "content-simple", "content-detail", "video_visual", "user_type"
        from paper_score import PaperScore
        self._dict_paper_scores_by_doi = None
        self._xs = None
        self._ys = None
        # Get videos
        _list_columns = ["idx", "videoId", "content",
                         "idx_paper", "channelId", "viewCount"]
        self.db_handler.sql_handler.select(self.table_name, _list_columns)
        if type(where) != type(None):
            self.db_handler.sql_handler.where(*where)
        _list_videos = self.db_handler.execute().fetchall()

        # Transform rows into dicts
        _list_dict_videos = list(
            map(lambda _row: dict(zip(_list_columns, _row)), _list_videos))
        # Instantiate PaperScores
        _set_dois = set(map(lambda _row: _row[3], _list_videos))
        print("[+]Target DOIs: %d" % len(_set_dois))
        _temp_df_scopus = self.df_scopus[self.df_scopus[paper_metric].notna()]
        _temp_df_scopus = _temp_df_scopus[_temp_df_scopus[paper_metric] != "None"]
        self._dict_paper_scores_by_doi = dict(zip(_set_dois, tuple(map(lambda _doi: PaperScore(
            _doi, _temp_df_scopus, paper_metric=paper_metric, video_metric=video_metric, label_by=label_by, log_scale=log_scale), _set_dois))))  # {_doi: PaperScore(_doi), ...}
        # Append videos to corresponding instances
        for _dict_video in _list_dict_videos:
            self._dict_paper_scores_by_doi[_dict_video["idx_paper"]].append_video(
                _dict_video)        
        
        # Plot by labels
        plt.figure(figsize=(10, 6))
        if type(label_by) != type(None):
            dict_x = dict()
            dict_y = dict()
            _set_labels_valid = set(map(lambda _paper_score: _paper_score.calc_ytscore(method=method).label, self._dict_paper_scores_by_doi.values()))
            for _label in _set_labels_valid:
                dict_x[_label] = list()
                dict_y[_label] = list()
            
            for _instance in self._dict_paper_scores_by_doi.values():
                if None in _instance.get_ytscore_meter():
                    continue
                dict_x[_instance.label].append(_instance.ytscore)
                dict_y[_instance.label].append(_instance.paper_meter)
            # Sort x, y
            for _label in _set_labels_valid:
                dict_x[_label], dict_y[_label] = self.__sort_xs_ys(dict_x[_label], dict_y[_label])
            
            _list_legends = list()
            _list_plts = list()
            _list_colors =  ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            # Plot
            for _i, _label in enumerate(_set_labels_valid):    
                _list_plts.append(plt.scatter(x=dict_x[_label], y=dict_y[_label], s=12, marker="o", c=_list_colors[_i % len(_list_colors)]))
                _list_legends.append("%s(N=%d, c=%.2f)" % (_label, len(dict_y[_label]), PaperScore.dict_content_calib_coef[_label])) if "calibrated" in method else \
                    _list_legends.append("%s(N=%d)" % (_label, len(dict_y[_label])))
            # Legend
            plt.legend(tuple(_list_plts),
                tuple(_list_legends),
                scatterpoints=1,
                loc='upper right',
                fontsize=8,
                framealpha=0.3
            )
            # Regression
            if regression:
                _xs = list()
                _ys = list()
                for _i, _label in enumerate(_set_labels_valid):
                    _xs += dict_x[_label]
                    _ys += dict_y[_label]
                    
                    if len(dict_x[_label]) > 2:
                        _color = _list_colors[_i % len(_list_colors)]
                        # print("\tlen x: %d\tlen y: %d" % (len(dict_x[_label]), len(dict_y[_label])))
                        # print("\tx:", dict_x[_label])
                        # print("\ty:", dict_y[_label])
                        _coef = np.polyfit(dict_x[_label], dict_y[_label], 1)
                        _poly1d_fn = np.poly1d(_coef)
                        _corr = np.corrcoef(dict_x[_label], dict_y[_label])[0, 1]
                        plt.plot([dict_x[_label][0], dict_x[_label][-1]], [_poly1d_fn(dict_x[_label])[0], _poly1d_fn(dict_x[_label])[-1]], '--', color=_color)
                        _text = "%s(R=%.2f, b0=%.2f, b1=%.2f, N=%d)" % (_label, _corr, _coef[0], _coef[1], len(dict_x[_label]))
                        plt.text(dict_x[_label][-1] - len(_text) / 30.0, _poly1d_fn(dict_x[_label])[-1] + .1, _text, c=_color)
                        # print("%s: %s" % (_label, _color))
                
                # Sort xs, ys
                _xs, _ys = self.__sort_xs_ys(_xs, _ys)
                # Regression for total points
                _label = "Total"
                _color = "#000000"
                _coef = np.polyfit(_xs, _ys, 1)
                _poly1d_fn = np.poly1d(_coef)
                _corr = np.corrcoef(_xs, _ys)[0, 1]
                plt.plot([_xs[0], _xs[-1]], [_poly1d_fn(_xs)[0], _poly1d_fn(_xs)[-1]], '--', color=_color)
                _text = "%s(R=%.2f, b0=%.2f, b1=%.2f, N=%d)" % (_label, _corr, _coef[0], _coef[1], len(_xs))
                plt.text(_xs[-1] - len(_text) / 40.0, _poly1d_fn(_xs)[-1] + .05, _text, c=_color)

            _num_total = 0
            for _label in dict_x:
                _num_total += len(dict_x[_label])
            plt.title("%s(N=%d)" % (self.title, _num_total))
            
        else:  # No label # No?!
            # Calc paper scores
            _list_points = list(map(lambda _instance: _instance.calc_ytscore(method=method).get_ytscore_meter(
            ), tuple(self._dict_paper_scores_by_doi.values())))  # [(ytscore, paper_meter), ...]
            # Get xs, ys
            self._xs = [_point[0] for _point in _list_points if None not in _point]
            self._ys = [_point[1] for _point in _list_points if None not in _point]
            # Sort
            self._xs, self._ys = self.__sort_xs_ys(self._xs, self._ys)

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
            # Regression for total points
            if regression:
                _label = "Total"
                _color = "#000000"
                _coef = np.polyfit(self._xs, self._ys, 1)
                _poly1d_fn = np.poly1d(_coef)
                plt.plot([self._xs[0], self._xs[-1]], [_poly1d_fn(self._xs)[0], _poly1d_fn(self._xs)[-1]], '--', color=_color)
                _corr = np.corrcoef(self._xs, self._ys)[0, 1]
                _text = "%s(R=%.2f, b0=%.2f, b1=%.2f, N=%d)" % (_label, _corr, _coef[0], _coef[1], len(self._xs))
                plt.text(self._xs[-1] - len(_text) / 40.0 - 1, _poly1d_fn(self._xs)[-1] + .05, _text, c=_color)
            
            # Show
            plt.title("%s(N=%d)" % (self.title, len(self._xs)))
        
        plt.xlim(0, 7)
        plt.ylim(0, 4.0)
        plt.xlabel("YTscore\n(%s, %s)" % (video_metric, method))
        plt.ylabel("log10(%s)" % paper_metric) if log_scale else plt.ylabel(paper_metric)
        plt.show()
        
        return self
    
    def __sort_xs_ys(self, xs, ys, desc=False):
        # Sort xs, ys
        _xs_new = list()
        _ys_new = list()
        for _x, _y in sorted(zip(xs, ys), reverse=desc):
            _xs_new.append(_x)
            _ys_new.append(_y)
        return _xs_new, _ys_new

    def __cl(self, xs, ys):
        # _color = _list_colors[_i % len(_list_colors)]
        # print("\tlen x: %d\tlen y: %d" % (len(dict_x[_label]), len(dict_y[_label])))
        # print("\tx:", dict_x[_label])
        # print("\ty:", dict_y[_label])
        _coef = np.polyfit(xs, ys, 1)
        _poly1d_fn = np.poly1d(_coef)
        # _dx = xs[0] - xs[-1]
        # _dy = _poly1d_fn(xs)[0] - _poly1d_fn(xs)[-1]
        # _b0 = (_poly1d_fn(xs)[0] * _dx - _dy * xs[0]) / _dx
        # _b1 = _dy / _dx
        _corr = np.corrcoef(xs, ys)[0, 1]
        return _corr, _b0, _b1
        _text = "%s(R=%.2f, N=%d)" % (_label, _corr, len(xs))
        plt.plot([xs[0], xs[-1]], [_poly1d_fn(xs)[0], _poly1d_fn(xs)[-1]], '--', color=_color)
        plt.text(xs[-1] - len(_text) / 30.0, _poly1d_fn(xs)[-1] + .1, _text, c=_color)        
