import pandas as pd
import json

# from urllib.request import urlopen
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlparse
from urllib.error import URLError
from selenium import webdriver
import socket

from preprocessor import Preprocessor


class ScopusPreprocessor(Preprocessor):
    tup_new_columns = ("Redirection", "Redirection_pdf")
    opener = build_opener(HTTPCookieProcessor())
    # driver = webdriver.Chrome("./chromedriver_83")
    num_pass = 0
    num_fail = 0
    num_skip = 0

    def __init__(
            self,
            fpath_scopus_csv,
            savepoint_interval=10,
            overwrite=False,
            set_redirection=False,
            set_pdf=False,
            shuffle=False,
            preprocess_redirected_urls=False):
        # super(ScopusPreprocessor, self).__init__()
        self.fpath_scopus_csv = fpath_scopus_csv
        self.savepoint_interval = savepoint_interval
        self.overwrite = overwrite
        self.set_redirection = set_redirection
        self.set_pdf = set_pdf
        self.shuffle = shuffle
        self.preprocess_redirected_urls = preprocess_redirected_urls

        self.data = pd.read_csv(fpath_scopus_csv, header=0, sep=",", dtype=str)
        self.data = self.data.astype(str)
        self.num_papers = len(self.data)
        if shuffle:
            print("[+]Shuffling records.")
            self.data = self.data.sample(frac=1).reset_index(drop=True)

        with open("scopus/source_pub_dict-math+comp.txt") as f:
            self.dict_source_pub = json.load(f)

    def preprocess_scopus_csv(self):
        # Create columns
        for _col in self.tup_new_columns:
            try:
                self.data[_col]
            except KeyError:
                self.data[_col] = "None"

        # Get youtube search queries
        self.__add_yt_direct_queries()
        # self.driver.close()

        # Report

        return self.data

    def __add_yt_direct_queries(self):
        # DOI
        # _S_doi = data["DOI"]
        # Redirected urls
        self.__set_redirections()
        print("\n# papers: %d\t# fail: %d\t# pass: %d\t# skip: %d" %
              (self.num_papers, self.num_fail, self.num_pass, self.num_skip))
        print("Done.")

        # pd.Series.astype(str) + ',' + pd.Series.astype(str)
        return self

    def __url_without_open(self, i):
        _source_title = self.data["Source title"][i]
        # If source title is in dict_source_pub keys:
        if _source_title in self.dict_source_pub:
            # Case1: SagePub
            # if _source_title in ("Journal of Peace Research", "Progress in Human Geography","International Journal of Robotics Research"):
            if self.dict_source_pub[_source_title] == "SAGE":
                # https://journals.sagepub.com/doi/10.1177/0022343314534458
                return ("journals.sagepub.com/doi/" + self.data["DOI"][i], "nan")

            # Case2: Taylor&Francis Online
            # elif _source_title in ("Journal of Business and Economic Statistics", "Research on Language and Social Interaction",):
            elif self.dict_source_pub[_source_title] == "Taylor & Francis":
                # https://www.tandfonline.com/doi/abs/10.1080/07350015.2014.917979
                return ("tandfonline.com/doi/abs/" + self.data["DOI"][i], "nan")

            # Case3: Wiley Online Library
            elif self.dict_source_pub[_source_title] == "Wiley-Blackwell":
                # elif _source_title in ("Criminology", "Journal of Field Robotics", "Journal of Computational Chemistry", "Journal of Chemical Theory and Computation", "Wiley Interdisciplinary Reviews: Computational Molecular Science"):
                # onlinelibrary.wiley.com/doi/abs/10.1002/rob.21489
                return ("onlinelibrary.wiley.com/doi/abs/" + self.data["DOI"][i], "nan")

            # Case6: ACM
            elif self.dict_source_pub[_source_title] == "ACM":
                # elif _source_title in ("ACM Computing Surveys", "Communications of the ACM"):
                # https://dl.acm.org/doi/10.1145/2506375
                return ("dl.acm.org/doi/" + self.data["DOI"][i], "nan")

            # Case7: American Chemical Society
            elif self.dict_source_pub[_source_title] == "American Chemical Society":
                # elif _source_title in ("Journal of Chemical Information and Modeling", "Journal of Chemical Theory and Computation"):
                # https://pubs.acs.org/doi/10.1021/ci400532b
                return ("pubs.acs.org/doi/" + self.data["DOI"][i], "nan")

            # Case9: The Royal Society
            elif self.dict_source_pub[_source_title] == "The Royal Society":
                # https://royalsocietypublishing.org/doi/10.1098/rsta.2012.0511
                return ("royalsocietypublishing.org/doi/" + self.data["DOI"][i], "royalsocietypublishing.org/doi/pdf/" + self.data["DOI"][i])

        # Case8: Princeton
        elif _source_title in ("Annals of Mathematics",):
            # https://annals.math.princeton.edu/2014/179-1/p06
            # https://annals.math.princeton.edu/wp-content/uploads/annals-v179-n2-p04-s.pdf
            _ = self.data["DOI"][i].split(".")
            return ("/".join(["annals.math.princeton.edu", _[-4], _[-3] + "-" + _[-2], "p" + _[-1].zfill(2)]),
                    "-".join(["annals.math.princeton.edu/wp-content/uploads/annals", "v" + _[-3], "n" + _[-2], "p" + _[-1].zfill(2)]))
        # Case10: PLoS
        elif _source_title in ("PLoS Computational Biology",):
            # https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1003378
            # https://journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1003378&type=printable
            return ("journals.plos.org/ploscompbiol/article?id=" + self.data["DOI"][i],
                    "journals.plos.org/ploscompbiol/article/file?id=" + self.data["DOI"][i] + "&type=printable")
        # Case4: The University of Chicago Press Journal
        elif _source_title in ("American Journal of Sociology",):
            return "journals.uchicago.edu/doi/" + self.data["DOI"][i]
        # Case5: American Psychological Association
        elif _source_title in ("Journal of Personality and Social Psychology",):
            return "doi.apa.org/doiLanding?doi=" + self.data["DOI"][i].replace('/', "%2F")
            # 10.1037/a0036148
            # return "doi.apa.org/doiLanding?doi=10.1037%2Fa0036148"

        return False

    def __set_redirections(self):
        print("[+]Getting redirected urls...")
        # S_DOI == data["DOI"]
        _list_urls_redirected = list()
        self.num_pass = 0
        self.num_fail = 0
        self.num_skip = 0
        for _i in range(self.num_papers):
            print("[+]Processing %d out of %d papers..." %
                  (_i+1, self.num_papers))
            # Overwrite: False or "Err"
            if (self.overwrite == False and not ((self.set_redirection and self.data["Redirection"][_i] == "None") or (self.set_pdf and self.data["Redirection_pdf"][_i] == "None")))\
                    or (self.overwrite == "Err" and not ((self.set_redirection and self.data["Redirection"][_i] in ("None", "Err")) or (self.set_pdf and self.data["Redirection_pdf"][_i] in ("None", "Err")))):
                # if (self.overwrite == False and self.data["Redirection"][_i] != "None" and self.data["Redirection_pdf"][_i] != "None") or\
                #     (self.overwrite == "Err" and self.data["Redirection"][_i] not in ("None", "Err") and self.data["Redirection_pdf"][_i] not in ("None", "Err")):
                # Already done.
                # Preprocess?
                if self.preprocess_redirected_urls:
                    self.data["Redirection"][_i] = self.__preprocess_redirected_url(
                        self.data["Redirection"][_i])
                print("\t[+]Passing.")
                self.num_pass += 1
                self.__check_savepoint(_i, self.data)
                continue

            _doi = self.data["DOI"][_i]
            # Skip opening?
            _url_redirected = self.__url_without_open(_i)
            if _url_redirected != False:
                self.num_skip += 1
                print("\t[+]Skip opening.")
                _redirected_abs, _redirected_pdf = _url_redirected
            else:
                if self.set_redirection:
                    # Build up url
                    _url = "https://www.doi.org/" + _doi
                    # Get redirection
                    try:
                        print("\t[+]Opening url:")
                        print("\t\t%s" % _url)
                        _res = self.opener.open(_url, timeout=30)
                        # self.driver.get(_url)
                    except URLError:
                        # Invalid URL
                        print("\t[-]Invalid URL.")
                        _redirected_abs = "Err"
                        self.num_fail += 1
                    except socket.timeout:
                        # Timeout
                        print("\t[-]Timed out.")
                        _redirected_abs = "Err"
                        self.num_fail += 1
                    except ConnectionResetError:
                        # Connection reset
                        print("\t[-]Connection reset error.")
                        _redirected_abs = "Err"
                        self.num_fail += 1
                    else:
                        print("\t[+]Opening url successful.")
                        _redirected_abs = _res.geturl()
                        # Close response
                        _res.close()
                        # _redirected_abs = self.driver.current_url
                    finally:
                        # Remove protocol(https?://www.), query, hash, ...
                        _redirected_abs = urlparse(_redirected_abs)
                        # Append
                        _redirected_abs = _redirected_abs.netloc + _redirected_abs.path
                        # Preprocess redirection
                        _redirected_abs = self.__preprocess_redirected_url(
                            _redirected_abs)

                if self.set_pdf:
                    if self.data["Access Type"][_i] == "nan":
                        _redirected_pdf = "nan"
                    else:
                        _redirected_pdf = "None"

            # Write on DataFrame
            if self.set_redirection:
                print("\t[+]Redirection: %s" % _redirected_abs)
                self.data["Redirection"][_i] = _redirected_abs
            if self.set_pdf:
                print("\t[+]Redirection_pdf: %s" % _redirected_pdf)
                self.data["Redirection_pdf"][_i] = _redirected_pdf

            self.__check_savepoint(_i, self.data)
        # Save
        self.data.astype(str).to_csv(self.fpath_scopus_csv, index=False)

        return self

    def __preprocess_redirected_url(self, url_redirected):
        # Remove www.
        if url_redirected.startswith("www."):
            url_redirected = url_redirected[4:]
        # Remove /
        if url_redirected.endswith('/'):
            url_redirected = url_redirected[:-1]
        return url_redirected

    def __check_savepoint(self, enum, df):
        if (enum+1) % self.savepoint_interval == 0:
            df.astype(str).to_csv(self.fpath_scopus_csv, index=False)
        return self


if __name__ == "__main__":
    # fpath = "scopus/scopus_math+comp_top5perc_1401.csv"
    # scopus_preprocessor = ScopusPreprocessor(fpath, overwrite=True, shuffle=True)
    # scopus_preprocessor.preprocess_scopus_csv()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--fpath')
    parser.add_argument('--overwrite', action="store_true", default="Err")
    parser.add_argument('--redirection', action="store_true", default=False)
    parser.add_argument('--pdf', action="store_true", default=False)
    parser.add_argument('--shuffle', action="store_true", default=False)
    parser.add_argument('--savepoint_interval', type=int, default=10)
    parser.add_argument('--preprocess_redirected_urls',
                        action="store_true", default=False)
                        
    args = parser.parse_args()

    scopus_preprocessor = ScopusPreprocessor(args.fpath,
                                             overwrite=args.overwrite,
                                             shuffle=args.shuffle,
                                             set_redirection=args.redirection,
                                             set_pdf=args.pdf,
                                             savepoint_interval=args.savepoint_interval,
                                             preprocess_redirected_urls=args.preprocess_redirected_urls)
    scopus_preprocessor.preprocess_scopus_csv()
