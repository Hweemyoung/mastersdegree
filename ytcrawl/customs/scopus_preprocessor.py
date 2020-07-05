import pandas as pd

# from urllib.request import urlopen
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlparse
from urllib.error import URLError
from selenium import webdriver
import socket

from preprocessor import Preprocessor


class ScopusPreprocessor(Preprocessor):
    tup_new_columns = ("Redirection",)
    opener = build_opener(HTTPCookieProcessor())
    # driver = webdriver.Chrome("./chromedriver_83")

    def __init__(
            self,
            fpath_scopus_csv,
            savepoint_interval=10):
        # super(ScopusPreprocessor, self).__init__()
        self.fpath_scopus_csv = fpath_scopus_csv
        self.savepoint_interval = savepoint_interval

        self.data = pd.read_csv(fpath_scopus_csv, header=0, sep=",", dtype=str)
        self.data = self.data.astype(str)

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

        return self.data

    def __add_yt_direct_queries(self):
        # DOI
        # _S_doi = data["DOI"]
        # Redirected urls
        self.__set_redirections()
        # Adjust Err values

        # pd.Series.astype(str) + ',' + pd.Series.astype(str)
        return self

    def __url_without_open(self, i):
        # Case1: SagePub
        if self.data["Source title"][i] in ("Journal of Peace Research","Progress in Human Geography",):
            # https://journals.sagepub.com/doi/10.1177/0022343314534458
            return "journals.sagepub.com/doi/" + self.data["DOI"][i]
        # Case2: Taylor&Francis Online
        elif self.data["Source title"][i] in ("Journal of Business and Economic Statistics", "Research on Language and Social Interaction",):
            # https://www.tandfonline.com/doi/abs/10.1080/07350015.2014.917979
            return "tandfonline.com/doi/abs/" + self.data["DOI"][i]
        # Case3: Wiley Online Library
        elif self.data["Source title"][i] in ("Criminology",):
            return "onlinelibrary.wiley.com/doi/abs/" + self.data["DOI"][i]
        # Case4: The University of Chicago Press Journal
        elif self.data["Source title"][i] in ("American Journal of Sociology",):
            return "journals.uchicago.edu/doi/" + self.data["DOI"][i]
        # Case5: American Psychological Association
        elif self.data["Source title"][i] in ("Journal of Personality and Social Psychology",):
            return "doi.apa.org/doiLanding?doi=" + self.data["DOI"][i].replace('/', "%2F")
            # 10.1037/a0036148
            # return "doi.apa.org/doiLanding?doi=10.1037%2Fa0036148"
        
        return False
            
    def __set_redirections(self):
        print("[+]Getting redirected urls...")
        # S_DOI == data["DOI"]
        _list_urls_redirected = list()
        _num_papers = len(self.data)
        for _i in range(_num_papers):
            print("[+]Processing %d out of %d papers..." % (_i+1, _num_papers))
            # Hasn't been processed?
            if self.data["Redirection"][_i] != "None":
                print("\t[+]Already processed. Skipping...")
                continue
            _doi = self.data["DOI"][_i]
            # Skip opening?
            _url_redirected = self.__url_without_open(_i)
            if _url_redirected != False:
                print("\t[+]Skip opening.")
            else:
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
                    _url_redirected = "Err"
                except socket.timeout:
                    # Timeout
                    print("\t[-]Timed out.")
                    _url_redirected = "Err"
                except ConnectionResetError:
                    # Connection reset
                    print("\t[-]Connection reset error. Passing...")
                    _url_redirected = "None"
                else:
                    print("\t[+]Opening url successful.")
                    _url_redirected = _res.geturl()
                    # Close response
                    _res.close()
                    # _url_redirected = self.driver.current_url
                finally:
                    # Remove protocol(https?://www.), query, hash, ...
                    _url_redirected = urlparse(_url_redirected)
                    # Append
                    print("\t[+]Setting redirected url:")
                    _url_redirected = _url_redirected.netloc + _url_redirected.path
                    print("\t\t%s" % _url_redirected)
            # Write on DataFrame
            self.data["Redirection"][_i] = _url_redirected
            # _list_urls_redirected.append(_url_redirected.netloc + _url_redirected.path)
            self.__check_savepoint(_i, self.data)
        # Save
        self.data.astype(str).to_csv(self.fpath_scopus_csv, index=False)

        return self

    def __check_savepoint(self, enum, df):
        if (enum+1) % self.savepoint_interval == 0:
            df.astype(str).to_csv(self.fpath_scopus_csv, index=False)
        return self


if __name__ == "__main__":
    fpath = "scopus/social-science,top11-20journals,2014.csv"
    scopus_preprocessor = ScopusPreprocessor(fpath)
    scopus_preprocessor.preprocess_scopus_csv()
