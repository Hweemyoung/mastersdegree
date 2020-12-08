import numpy as np

class PaperScore:
    doi = None
    ytscore = None
    paper_meter = None
    label = None

    dict_content_detail_to_simple = {
        "paper_explanation": "paper_explanation",
        "paper_application": "paper_explanation",
        "paper_assessment": "paper_explanation",
        "paper_supplementary": "paper_supplementary",
        "paper_linked_supplementary": "paper_supplementary",
        "paper_reference": "paper_reference",
        "news": "news",
    }

    dict_content_calib_coef = {
        "paper_explanation": 1.2,
        "paper_supplementary": 0.8,
        "paper_reference": 0.9,
        "news": 0.3,
        "Mixed": 1.0,
    }

    def __init__(self, doi, df_scopus, paper_metric="Cited by", video_metric="viewCount", label_by=None, log_scale=True):
        self.doi = doi
        self.df_scopus = df_scopus
        # self.df_scopus = df_scopus[df_scopus[paper_metric].notna()]  # Drop na
        # print("[+]Length: %d" % len(self.df_scopus))
        self.paper_metric = paper_metric
        self.video_metric = video_metric
        self.label_by = label_by
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
        if type(self.label_by) != type(None):
            self.__set_label()
        
        if method == "sum":
            self.__calc_ytscore_sum()
        elif method == "calibrated-sum":
            self.__calc_ytscore_calib_sum()
        
        return self
    
    def __calc_ytscore_sum(self):
        self.ytscore = 0
        for _dict_video in self.list_dict_videos:
            self.ytscore += _dict_video[self.video_metric]
        if self.log_scale:
            self.ytscore = np.log10(self.ytscore)
        return self.ytscore

    def __calc_ytscore_calib_sum(self):
        self.__calc_ytscore_sum()
        # Multiply coefficient.
        self.ytscore = self.ytscore * self.dict_content_calib_coef[self.label]
        return self.ytscore
    
    def __set_label(self):
        if self.label_by == "content-simple":
            self.set_labels = set(map(lambda _dict_video: self.dict_content_detail_to_simple[_dict_video["content"]], self.list_dict_videos))

        # elif self.label_by == "content-simple":
        #     _list_labels = ["paper_explanation", "paper_supplementary", "paper_reference", "news",]
        #     for _video in self.list_dict_videos.values():
        #         self.dict_content_detail_to_simple[_video["content"]]
        if len(self.set_labels) == 1:
            self.label = list(self.set_labels)[0]
        elif len(self.set_labels) > 1:
            self.label = "Mixed"
        else:
            print("\t[-]DOI %s: Label not found." % self.doi)
            self.label = None
        return self

    def get_ytscore_meter(self):
        if None in (self.ytscore, self.paper_meter):
            # raise ValueError("[-]Either YTscore or paper meter is None.")
            print("\t[-]DOI %s: Either YTscore or paper meter is None." % self.doi)
            # return None
        return (self.ytscore, self.paper_meter)


