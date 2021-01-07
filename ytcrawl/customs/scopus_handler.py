import random
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
from sklearn.manifold import TSNE


class ScopusHandler:
    videos = None
    idx_papers = None
    subjects_total = None
    subjects_w_videos = None
    subjects_total_w_videos = None
    list_target_videos = None

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
    

    def __init__(self, df_scopus, df_sources, table_name, title=None, verbose=True, preset_dois=True, preset_videos=True):
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
        
        self._tup_idx_2014_comp = (1, 2, 3, 4, 6, 7, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 24, 25, 27, 28, 29, 30, 31, 33, 34, 36, 38, 39, 41, 43, 46, 48, 50, 51, 52, 53, 55, 56, 57, 58, 62, 64, 65, 69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 84, 85, 87, 88, 89, 91, 92, 95, 96, 97, 98, 99, 101, 102, 103, 105, 106, 107, 109, 111, 114, 115, 118, 119, 120, 121, 122, 124, 125, 127, 128, 129, 131, 132, 135, 137, 138, 142, 143, 144, 145, 147, 148)
        self._tup_idx_2019_comp = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80)
        self._tup_idx_2014_life = (1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 61, 62, 63, 65, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 109, 110, 111, 112)
        self._tup_idx_2019_life = (2, 3, 6, 10, 12, 17, 18, 38, 43, 50, 55, 56, 59, 67, 72, 73, 78, 86, 88, 90, 93, 94, 101, 108, 109, 110, 113, 116, 120, 122, 124, 128, 129, 130, 139, 140, 142, 145, 150, 153, 158, 159, 161, 163, 165, 166, 171, 175, 178, 181, 184, 190, 195, 199, 208, 209, 214, 217, 222, 223, 230, 232, 233, 238, 246, 247, 254, 256, 258, 264, 267, 270, 271, 275, 277, 281, 284, 286, 291, 292, 297, 298, 299, 300, 303, 305, 310, 311, 314, 316, 317, 318, 324, 326, 327, 330, 333, 334, 340, 343)
        # self._tup_idx_2014_comp = sorted(random.sample(range(1, 149), 100))
        # self._tup_idx_2019_comp = sorted(random.sample(range(1, 81), 80))
        # self._tup_idx_2014_life = sorted(random.sample(range(1, 113), 100))
        # self._tup_idx_2019_life = (2, 3, 6, 10, 12, 17, 18, 38, 43, 50, 55, 56, 59, 67, 72, 73, 78, 86, 88, 90, 93, 94, 101, 108, 109, 110, 113, 116, 120, 122, 124, 128, 129, 130, 139, 140, 142, 145, 150, 153, 158, 159, 161, 163, 165, 166, 171, 175, 178, 181, 184, 190, 195, 199, 208, 209, 214, 217, 222, 223, 230, 232, 233, 238, 246, 247, 254, 256, 258, 264, 267, 270, 271, 275, 277, 281, 284, 286, 291, 292, 297, 298, 299, 300, 303, 305, 310, 311, 314, 316, 317, 318, 324, 326, 327, 330, 333, 334, 340, 343)
        
        self.tup_idx = None
        if preset_videos:
            if self.table_name == "scopus_videos_2014_comp":
                self.tup_idx = self._tup_idx_2014_comp
            elif self.table_name == "scopus_videos_2019_comp":
                self.tup_idx = self._tup_idx_2019_comp
            elif self.table_name == "scopus_videos_2014_life":
                self.tup_idx = self._tup_idx_2014_life
            elif self.table_name == "scopus_videos_2019_life":
                self.tup_idx = self._tup_idx_2019_life
        self.dois_targets = None
        self.dois_counterparts = None

        self.dois_targets_2019_comp = ['10.1145/3298981', '10.1371/journal.pcbi.1006826', '10.1016/j.future.2018.01.055', '10.1021/acs.jctc.8b00975', '10.1109/TII.2018.2870662', '10.1016/j.chb.2018.08.022', '10.1016/j.chb.2018.09.023', '10.1016/j.robot.2019.01.013', '10.1093/bib/bby034', '10.1145/3241737', '10.1109/TVCG.2019.2898822', '10.1109/TVCG.2019.2898742', '10.1371/journal.pcbi.1006846', '10.1371/journal.pcbi.1006792', '10.1016/j.ijinfomgt.2018.09.005', '10.1109/TVCG.2018.2865192', '10.1016/j.compedu.2019.02.005', '10.1016/j.ins.2018.08.062', '10.1109/TMI.2018.2856464', '10.1177/0278364919845054', '10.1371/journal.pcbi.1006907', '10.1089/soro.2018.0008', '10.1109/TVCG.2019.2899187', '10.1016/j.cpc.2019.01.017', '10.1016/j.chb.2018.03.001', '10.1371/journal.pcbi.1006922', '10.1016/j.ijhcs.2018.08.002', '10.1016/j.cosrev.2019.01.001', '10.1016/j.chb.2018.10.001', '10.1016/j.ejor.2018.04.039', '10.1109/TII.2018.2847736', '10.1109/TVCG.2018.2808969', '10.1371/journal.pcbi.1006895', '10.1109/TVCG.2018.2864817', '10.25300/MISQ/2019/14812', '10.1002/rob.21857', '10.1021/acs.jctc.8b01176', '10.1016/j.isprsjprs.2019.02.014', '10.1109/TNNLS.2018.2852711', '10.1109/TRO.2018.2868804', '10.1109/TMECH.2019.2909081', '10.1016/j.compind.2019.03.004', '10.1016/j.neunet.2018.11.009', '10.1177/0278364918796267', '10.1016/j.adhoc.2018.11.004', '10.1109/TVCG.2018.2864509', '10.1109/TMECH.2018.2874647', '10.1016/j.ejor.2018.10.005', '10.1109/MSP.2018.2875863', '10.1109/TMECH.2019.2907802', '10.1093/bioinformatics/bty871', '10.1016/j.future.2017.08.009', '10.1007/s11263-018-1138-7', '10.1109/MCOM.2018.1701370', '10.1016/j.compedu.2018.09.012', '10.1109/TRO.2019.2897858', '10.1109/TRO.2018.2887356', '10.1007/s11831-017-9241-4', '10.1109/THMS.2019.2895753', '10.1016/j.plrev.2019.03.003']
        self.dois_targets_2014_comp = ['10.1007/s10514-013-9339-y', '10.1016/j.chb.2013.07.014', '10.1016/j.plrev.2013.08.002', '10.1007/s11263-013-0655-7', '10.1016/j.patcog.2013.08.011', '10.1177/0278364913506757', '10.1016/j.plrev.2013.11.003', '10.1371/journal.pcbi.1003542', '10.1016/j.chb.2013.12.009', '10.1371/journal.pcbi.1003619', '10.1016/j.cviu.2013.10.003', '10.1016/j.knosys.2014.01.003', '10.1093/bioinformatics/btu031', '10.1109/TVT.2013.2270315', '10.1007/s10237-013-0491-2', '10.1021/ct4010307', '10.1109/TSE.2013.2295827', '10.1109/TSE.2014.2302433', '10.1371/journal.pcbi.1003496', '10.1109/TPAMI.2013.141', '10.1016/j.chb.2014.03.003', '10.1016/j.chb.2014.02.047', '10.1016/j.chb.2014.01.036', '10.1371/journal.pcbi.1003584', '10.1371/journal.pcbi.1003588', '10.1098/rsta.2013.0285', '10.1021/ct500287c', '10.1177/0278364913518997', '10.1177/0278364913507612', '10.1177/0278364913501212', '10.1177/0278364913507325', '10.1177/0278364913509126', '10.1109/TMC.2013.35', '10.1186/1471-2105-15-182', '10.1109/JBHI.2013.2283268', '10.1098/rsta.2013.0164', '10.1016/j.plrev.2013.11.014', '10.1016/j.patcog.2013.08.008', '10.1109/TMECH.2013.2273435', '10.1109/TIP.2013.2292332', '10.1109/TII.2014.2299233', '10.1109/TPDS.2013.284', '10.1109/JBHI.2013.2282816', '10.1109/TII.2014.2306383', '10.1098/rsta.2013.0090', '10.1109/TPDS.2013.132', '10.1109/TSE.2013.2297712', '10.1109/TKDE.2013.109', '10.1109/TII.2014.2305641', '10.1109/TITS.2013.2291241', '10.1109/MIC.2014.19', '10.1109/TKDE.2013.41', '10.1109/TSC.2013.3', '10.1177/0278364913519148', '10.1177/0278364914522141', '10.1016/j.cviu.2013.12.006', '10.1371/journal.pcbi.1003439', '10.1109/TSE.2013.48', '10.1109/TPDS.2013.122', '10.1109/TKDE.2013.88', '10.1109/TII.2014.2306329', '10.1109/TVT.2014.2310394', '10.1109/JBHI.2013.2282827', '10.1016/j.knosys.2013.12.005', '10.1109/TKDE.2013.124', '10.1109/TNNLS.2013.2285242', '10.1109/TRO.2013.2283927', '10.1371/journal.pcbi.1003446', '10.1109/TPDS.2013.299', '10.1109/TRO.2013.2280831', '10.1016/j.compedu.2013.12.002', '10.1109/TITS.2013.2294723', '10.1109/TKDE.2013.123', '10.1109/TKDE.2013.11']

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
        
        if self.tup_idx != None:
            self.db_handler.sql_handler.where("idx", self.tup_idx, "in")
        # if self.table_name == "scopus_videos_2019_life":
        #     self.db_handler.sql_handler.where("idx", self._tup_idx_2019_life, "in")
        # elif self.table_name == "scopus_videos_2014_life":
        #     self.db_handler.sql_handler.where("idx", self._tup_idx_2014_life, "in")
        # elif self.table_name == "scopus_videos_2019_comp":
        #     self.db_handler.sql_handler.where("idx", self._tup_idx_2019_comp, "in")
        # elif self.table_name == "scopus_videos_2014_comp":
        #     self.db_handler.sql_handler.where("idx", self._tup_idx_2014_comp, "in")

        self.list_videos_total = self.db_handler.execute().fetchall()
        # self.list_videos_total = self.__parse_fetches(self.list_videos_total)

        self.list_target_videos = list()

        if type(df_scopus) == type(None):
            df_scopus = self.df_scopus
        print("Total videos: %d" % len(self.list_videos_total))
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
        if _num_total_videos == 0:
            print("No videos found.")
            return self

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

    def cluster_scopus(self, target_column="Abstract", num_clusters=None, train_kmeans=True, reductor="TSNE", reduction_components=2, pretrained_model="distilbert-base-nli-stsb-mean-tokens", videos_where=None, videos_only=True):
        if type(reduction_components) != int or reduction_components > 3 or reduction_components < 2:
            raise ValueError(
                "[-]Argument 'reduction_components' must be either 2 or 3.")

        if self.embedder == None or self.pretrained_model != pretrained_model:
            print("[+]Assigning new embedder instance.")
            self.embedder = SentenceTransformer(pretrained_model)
            self.pretrained_model = pretrained_model

        if target_column == "Abstract":
            _df_scopus_filtered = self.df_scopus[self.df_scopus["Abstract"]
                                                 != "[No abstract available]"]
        elif target_column == "Author Keywords":
            _df_scopus_filtered = self.df_scopus.dropna(subset="Author Keywords")
        else:
            _df_scopus_filtered = self.df_scopus.copy()

        self.set_target_videos(_df_scopus_filtered, where=videos_where)

        # Papers w/ videos
        _target_scopus = _df_scopus_filtered[_df_scopus_filtered["DOI"].isin(self.idx_papers)].reset_index(drop=True) \
            if videos_only else _df_scopus_filtered.reset_index(drop=True)
        _list_corpus = list(_target_scopus[target_column])
        _list_corpus = list(map(lambda abs: abs.split("©")[0], _list_corpus))
        _list_titles = list(_target_scopus["Title"])
        _list_subjects = list(_target_scopus["Scopus Sub-Subject Area"])
        _list_dois = list(_target_scopus["DOI"])

        print("# Total elements in plot: %d" % len(_list_corpus))

        # Encode corpus
        self.corpus_embeddings = self.embedder.encode(_list_corpus)

        # Perform kmean clustering
        if self.clustering_model == None or num_clusters != None:
            self.num_clusters = num_clusters
            self.clustering_model = KMeans(n_clusters=self.num_clusters)
        if train_kmeans:
            self.clustering_model.fit(self.corpus_embeddings)

        # Reductor
        if reductor == "PCA":
            self.reductor = PCA(n_components=reduction_components)
        elif reductor == "TSNE":
            self.reductor = TSNE(n_components=reduction_components)
        elif reductor == "UMAP":
            from umap import UMAP
            from scipy.sparse.csgraph import connected_components
            self.reductor = UMAP()

        _reduced_embeddings = self.reductor.fit_transform(self.corpus_embeddings)

        self.clustered_abs = [[] for i in range(self.num_clusters)]
        self.clustered_embeddings = [[] for i in range(self.num_clusters)]
        self.clustered_pca = [[] for i in range(self.num_clusters)]
        self.clustered_titles = [[] for i in range(self.num_clusters)]
        self.clustered_subjects = [[] for i in range(self.num_clusters)]
        self.clustered_dois = [[] for i in range(self.num_clusters)]
        self.clustered_indices = [[] for i in range(self.num_clusters)]

        # Array of cluster index
        for sentence_id, cluster_id in enumerate(self.clustering_model.labels_):
            self.clustered_abs[cluster_id].append(_list_corpus[sentence_id])
            self.clustered_embeddings[cluster_id].append(
                self.corpus_embeddings[sentence_id])
            self.clustered_pca[cluster_id].append(_reduced_embeddings[sentence_id])
            self.clustered_titles[cluster_id].append(_list_titles[sentence_id])
            self.clustered_subjects[cluster_id].append(
                _list_subjects[sentence_id])
            self.clustered_dois[cluster_id].append(_list_dois[sentence_id])
            self.clustered_indices[cluster_id].append(sentence_id)

        # Describe clusters
        # self.desc_clusters("titles")

        if reduction_components == 2:
            plt.scatter(_reduced_embeddings[:, 0], _reduced_embeddings[:, 1],
                        c=self.clustering_model.labels_)
            plt.show()

        elif reduction_components == 3:
            fig = plt.figure(figsize=(14, 14))
            ax = fig.add_subplot(111, projection="3d")
            ax.scatter(_reduced_embeddings[:, 0], _reduced_embeddings[:, 1],
                       _reduced_embeddings[:, 2], c=self.clustering_model.labels_)
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

    def model_metrics(self, paper_metric="Cited by", video_metric="viewCount", method="sum", label_by=None, regression=False, where=None, log_scale=True, list_exclude_labels=[], xlim=None, ylim=(0, 4)):
        # label_by: "content-simple", "content-detail", "video_visual", "user_type"
        from paper_score import PaperScore
        self._dict_paper_scores_by_doi = None
        self._xs = None
        self._ys = None
        _dict_reg_data_by_label = dict()
        # Get videos
        _list_columns = ["idx", "videoId", "content",
                         "idx_paper", "channelId", "viewCount"]
        if self.tup_idx != None:
            self.db_handler.sql_handler.select(self.table_name, _list_columns).where("idx", self.tup_idx, "in")
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
            # Append points to the corresponding list
            for _instance in self._dict_paper_scores_by_doi.values():
                if None in _instance.get_ytscore_meter():
                    continue
                dict_x[_instance.label].append(_instance.ytscore)
                dict_y[_instance.label].append(_instance.paper_meter)
            
            self._dict_paper_scores_valid_by_doi = dict()
            for _instance in self._dict_paper_scores_by_doi.values():
                if None in _instance.get_ytscore_meter():
                    continue
                if len(dict_x[_instance.label]) > 1:
                    self._dict_paper_scores_valid_by_doi[_instance.doi] = _instance
            
            # if calib-w-sum
            if method == "calibrated-weighed-sum":
                _dict_data_by_label = dict()
                _dict_content_calib_coef = dict()
                for _i, _label in enumerate(_set_labels_valid):
                    if len(dict_x[_label]) > 1:
                        # Calc b0, b1, r, N
                        _coef = np.polyfit(dict_x[_label], dict_y[_label], 1)
                        _poly1d_fn = np.poly1d(_coef)
                        _corr = np.corrcoef(dict_x[_label], dict_y[_label])[0, 1]
                        _dict_data_by_label[_label] = (_corr, len(dict_x[_label]), _coef[0], _coef[1])  # r, N, b0(slope), b1(y-offset)
                
                        # Calc calib-coef
                        _dict_content_calib_coef[_label] = _dict_data_by_label[_label][0] * np.log10(_dict_data_by_label[_label][1])
                    else:  # For labels which have a single point each
                        pass  # Those are ignored in self._dict_paper_scores_valid_by_doi
                    
                # Calc target b0, b1
                _b0_target = np.sum(np.array(list(map(lambda _label: _dict_content_calib_coef[_label] * _dict_data_by_label[_label][2], _dict_data_by_label.keys())))) /\
                    np.sum(np.array(list(map(lambda _label: _dict_data_by_label[_label][2], _dict_data_by_label.keys()))))
                _b1_target = np.sum(np.array(list(map(lambda _label: _dict_content_calib_coef[_label] * _dict_data_by_label[_label][3], _dict_data_by_label.keys())))) /\
                    np.sum(np.array(list(map(lambda _label: _dict_data_by_label[_label][2], _dict_data_by_label.keys()))))
                    
                # Recalc ytscore, paper metric per PaperScore
                _list_paper_scores_recalc = list(map(lambda _paper_score: _paper_score.transform_x_y(
                        method=method,
                        target_b0=_b0_target,
                        b0=_dict_data_by_label[_paper_score.label][2],
                        target_b1=_b1_target,
                        b1=_dict_data_by_label[_paper_score.label][3]
                    ),
                    self._dict_paper_scores_valid_by_doi.values()
                ))

                # Renew xs, ys
                for _label in _set_labels_valid:
                    dict_x[_label] = list()
                    dict_y[_label] = list()
                for _paper_score in _list_paper_scores_recalc:
                    dict_x[_paper_score.label].append(_paper_score.ytscore)
                    dict_y[_paper_score.label].append(_paper_score.paper_meter)
            
            elif method == "sum":
                # dict_x, dict_y already ready.
                pass

            # Sort x, y
            for _label in _set_labels_valid:
                dict_x[_label], dict_y[_label] = self.__sort_xs_ys(dict_x[_label], dict_y[_label])
            
            _list_legends = list()
            _list_plts = list()
            _list_colors =  ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            # Exclude labels?
            if len(list_exclude_labels):
                for _label in list_exclude_labels:
                    _set_labels_valid.remove(_label)
            
            # Sort set_labels_vaild
            _list_labels_valid = sorted(list(_set_labels_valid))

            # Regression
            if regression:
                _xs = list()
                _ys = list()
                for _i, _label in enumerate(_list_labels_valid):
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
                        # _text = "%s(R=%.2f, b0=%.2f, b1=%.2f, N=%d)" % (_label, _corr, _coef[0], _coef[1], len(dict_x[_label]))
                        _text = _label
                        _dict_reg_data_by_label[_label] = [len(dict_x[_label]), _corr, _coef[0], _coef[1]]  # [N, R, b0, b1]
                        plt.text(dict_x[_label][-1] - len(_text) / 25.0, _poly1d_fn(dict_x[_label])[-1] + .1, _text, c=_color)
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
                _text = "%s(N=%d, R=%.2f, b0=%.2f, b1=%.2f)" % (_label, len(_xs), _corr, _coef[0], _coef[1])
                plt.text(_xs[-1] - len(_text) / 25.0, _poly1d_fn(_xs)[-1] + .05, _text, c=_color)

            _num_total = 0
            for _label in _list_labels_valid:
                _num_total += len(dict_x[_label])
                print(f"{_label}:")
                print("\txs:", sorted(dict_x[_label]))
                print("\tys:", sorted(dict_y[_label]))
            # plt.title("%s(N=%d)" % (self.title, _num_total))
            # plt.title("Math & Computer\n(N=%d)" % _num_total)
            plt.title("Life & Earth 2014")
            
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
        
        # Plot
        for _i, _label in enumerate(_list_labels_valid):    
            _list_plts.append(plt.scatter(x=dict_x[_label], y=dict_y[_label], s=12, marker="o", c=_list_colors[_i % len(_list_colors)]))
            
            _legend = "%s(N=%d, R=%.2f, b0=%.2f, b1=%.2f)" % tuple([_label] + _dict_reg_data_by_label[_label]) if _label in _dict_reg_data_by_label else\
                "%s(N=%d)" % (_label, len(dict_x[_label]))
            _list_legends.append(_legend)
            # _list_legends.append("%s(N=%d, c=%.2f, a=%.2f, b=%.2f)" \
            #     % (_label, len(dict_y[_label]), _dict_content_calib_coef[_label], _dict_data_by_label[_label][2] / _b0_target, (_dict_data_by_label[_label][3] - _b1_target) / _b0_target)) \
            #         if "calibrated" in method and _label in _dict_data_by_label else \
            #             _list_legends.append("%s(N=%d)" % (_label, len(dict_y[_label])))
        
        # Legend
        plt.legend(tuple(_list_plts),
            tuple(_list_legends),
            scatterpoints=1,
            loc='upper right',
            fontsize=8,
            framealpha=0.3
        )

        if type(xlim) != type(None):
            plt.xlim(*xlim)
        if type(ylim) != type(None):
            plt.ylim(*ylim)
        plt.xlabel("YTscore")
        if log_scale:
            plt.ylabel("log10(Citation)") if paper_metric == "Cited by" else plt.ylabel(f"log10({paper_metric})")
        else:
            plt.ylabel("Citation") if paper_metric == "Cited by" else plt.ylabel(paper_metric)
        plt.show()

        # xs, ys distribution
        _list_x = [dict_x[_label] for _label in _list_labels_valid]
        _list_y = [dict_y[_label] for _label in _list_labels_valid]
        _list_labels = [f"{_label}\n(N={len(dict_x[_label])}" for _label in _list_labels_valid]
        
        # plt.figure(figsize=(8,4))
        # plt.boxplot(
        #     _list_x,
        #     labels=_list_labels,
        #     showmeans=True
        # )
        # plt.ylabel("YTscore")
        # plt.show()

        # plt.figure(figsize=(8,4))
        # plt.boxplot(
        #     _list_y,
        #     labels=_list_labels,
        #     showmeans=True
        # )
        # plt.ylabel("log10(%s)" % paper_metric) if log_scale else plt.ylabel(paper_metric)
        # plt.show()

        import functools
        dict_x["total_valid"] = functools.reduce(lambda a, b: a + b, _list_x)
        dict_y["total_valid"] = functools.reduce(lambda a, b: a + b, _list_y)
        self.dict_x = dict_x
        self.dict_y = dict_y
        self.list_labels_valid = _list_labels_valid
        
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
