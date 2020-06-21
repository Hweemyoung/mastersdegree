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

        # pd.Series.astype(str) + ',' + pd.Series.astype(str)
        return self

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
                self.data["Redirection"][_i] = _url_redirected
                # _list_urls_redirected.append(_url_redirected.netloc + _url_redirected.path)
            self.__check_savepoint(_i, self.data)

        return self

    def __check_savepoint(self, enum, df):
        if (enum+1) % self.savepoint_interval == 0:
            df.astype(str).to_csv(self.fpath_scopus_csv, index=False)
        return self


if __name__ == "__main__":
    fpath = "scopus/scopus_social_2014.csv"
    scopus_preprocessor = ScopusPreprocessor(fpath)
    scopus_preprocessor.preprocess_scopus_csv()
