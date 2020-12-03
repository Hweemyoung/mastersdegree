import numpy as np

class PaperScore:
    doi = None
    ytscore = None
    paper_meter = None

    def __init__(self, doi, df_scopus, paper_metric="Cited by", video_metric="viewCount", log_scale=True):
        self.doi = doi
        self.df_scopus = df_scopus
        # self.df_scopus = df_scopus[df_scopus[paper_metric].notna()]  # Drop na
        # print("[+]Length: %d" % len(self.df_scopus))
        self.paper_metric = paper_metric
        self.video_metric = video_metric
        self.log_scale = log_scale
        
        self.list_dict_videos = list()
        # Set paper meter.
        self.__set_paper_meter()

    def __set_paper_meter(self):
        _paper = self.df_scopus[self.df_scopus["DOI"] == self.doi]
        if len(_paper) > 1:
            raise ValueError("[-]Duplicates exist: %d papers found." % len(_paper))
        elif len(_paper) == 0:
            # raise ValueError("[-]Paper not found in df_scopus.")
            print("\t[-]DOI %s: not found in df_scopus." % self.doi)
        else:
            self.paper_meter = int(_paper[self.paper_metric]) if not self.log_scale else float(np.log10(int(_paper[self.paper_metric])))
        return self

    def append_video(self, dict_video):
        self.list_dict_videos.append(dict_video)
        return self

    def calc_ytscore(self, method="sum"):
        if method == "sum":
            self.__calc_ytscore_sum(video_metric=self.video_metric)
        return self
    
    def __calc_ytscore_sum(self, video_metric):
        self.ytscore = 0
        for _dict_video in self.list_dict_videos:
            self.ytscore += _dict_video[video_metric]
        if self.log_scale:
            self.ytscore = np.log10(self.ytscore)
        return self.ytscore
    
    def get_ytscore_meter(self):
        if None in (self.ytscore, self.paper_meter):
            # raise ValueError("[-]Either YTscore or paper meter is None.")
            print("\t[-]DOI %s: Either YTscore or paper meter is None." % self.doi)
            # return None
        return (self.ytscore, self.paper_meter)
