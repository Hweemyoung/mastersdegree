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
            postprocess_redirections=False):
        # super(ScopusPreprocessor, self).__init__()
        self.fpath_scopus_csv = fpath_scopus_csv
        self.savepoint_interval = savepoint_interval
        self.overwrite = overwrite
        self.set_redirection = set_redirection
        self.set_pdf = set_pdf
        self.shuffle = shuffle
        self.postprocess_redirections = postprocess_redirections

        self.data = pd.read_csv(fpath_scopus_csv, header=0, sep=",", dtype=str)
        self.data = self.data.astype(str)
        self.num_papers = len(self.data)
        if shuffle:
            print("[+]Shuffling records.")
            self.data = self.data.sample(frac=1).reset_index(drop=True)

        with open("read_only/source_pub_dict-math+comp.txt") as f:
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
        if self.data["DOI"][i] == "nan":
            return ("nan", "nan")
        
        # Cannot be automated: "Briefings in Bioinformatics,Database,Bioinformatics"
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
            
            # Case9: World Scientific
            elif self.dict_source_pub[_source_title] == "World Scientific":
                # https://www.worldscientific.com/doi/abs/10.1142/S0129065714500051
                return ("worldscientific.com/doi/abs/" + self.data["DOI"][i], "nan")
        
        # Case8: Princeton
        if _source_title in ("Annals of Mathematics",):
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
                    "journals.plos.org/ploscompbiol/article/file?id=" + self.data["DOI"][i])  # journals.plos.org/ploscompbiol/article/file?id=10.1371/journal.pcbi.1003378

        # Case4: The University of Chicago Press Journal
        elif _source_title in ("American Journal of Sociology",):
            return "journals.uchicago.edu/doi/" + self.data["DOI"][i]

        # Case5: American Psychological Association
        elif _source_title in ("Journal of Personality and Social Psychology",):
            return "doi.apa.org/doiLanding?doi=" + self.data["DOI"][i].replace('/', "%2F")
            # 10.1037/a0036148
            # return "doi.apa.org/doiLanding?doi=10.1037%2Fa0036148"

        # Case11: Argument and Computation
        elif _source_title in ("Argument and Computation",):
            # https://content.iospress.com/articles/argument-and-computation/869766
            # https://content.iospress.com/download/argument-and-computation/869766?id=argument-and-computation%2F869766
            return ("content.iospress.com/articles/argument-and-computation/" + self.data["DOI"][i].split(".")[-1],  # content.iospress.com/articles/argument-and-computation/869766
                    "content.iospress.com/download/argument-and-computation/" + self.data["DOI"][i].split(".")[-1])  # content.iospress.com/download/argument-and-computation/869766

        # Case12: Vascular Cell
        elif _source_title in ("Vascular Cell",):
            # https://vascularcell.com/index.php/vc/article/view/10.1186-2045-824X-6-1
            # https://vascularcell.com/public/journals/1/articles/13221-06-01-135/13221-06-01.pdf # ???
            _ = self.data["DOI"][i].split("/")
            return ("vascularcell.com/index.php/vc/article/view/" + _[0] + "-" + _[1],  # content.iospress.com/articles/argument-and-computation/869766
                    "nan")
        
        # Case12: International Journal of Bio-Inspired Computation
        elif _source_title in ("International Journal of Bio-Inspired Computation",):
            # http://www.inderscience.com/offer.php?id=64989
            return ("inderscience.com/offer.php?id=" + str(int(self.data["DOI"][i].split(".")[-1])),  # content.iospress.com/articles/argument-and-computation/869766
                    "nan")

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
                if self.postprocess_redirections:
                    self.data["Redirection"][_i] = self.__postprocess_redirected_url(
                        self.data["Redirection"][_i])
                print("\t[+]Passing.")
                self.num_pass += 1
                self.__check_savepoint(_i, self.data)
                continue

            # Skip opening?
            _url_redirected = self.__url_without_open(_i)
            if _url_redirected != False:
                self.num_skip += 1
                print("\t[+]Skip opening.")
                if self.set_redirection:
                    self.__write_redirection(_i, _url_redirected[0])
                if self.set_pdf:
                    self.__write_pdf(_i, _url_redirected[1])
            else:
                if self.set_redirection:
                    # Build up url
                    _url = "https://www.doi.org/" + self.data["DOI"][_i]
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
                        # Postprocess redirection
                        _redirected_abs = self.__postprocess_redirected_url(
                            _redirected_abs)
                        self.__write_redirection(_i, _redirected_abs)

                if self.set_pdf:
                    _redirected_pdf = self.__get_redirected_pdf(_i)
                    self.__write_pdf(_i, _redirected_pdf)

            # Write on DataFrame
            # if self.set_redirection:
            #     print("\t[+]Redirection: %s" % _redirected_abs)
            #     self.data["Redirection"][_i] = _redirected_abs
            # if self.set_pdf:
            #     print("\t[+]Redirection_pdf: %s" % _redirected_pdf)
            #     self.data["Redirection_pdf"][_i] = _redirected_pdf

            self.__check_savepoint(_i, self.data)
        # Save
        self.data.astype(str).to_csv(self.fpath_scopus_csv, index=False)

        return self
    
    def __get_redirected_pdf(self, i):        
        if self.data["Access Type"][i] == "nan":
            return "nan"
        
        else:
            # Check format from Redirection
            _redirected_abs = self.data["Redirection"][i]
            if _redirected_abs in ("None", "Err"):
                return "None"

            else:
                if _redirected_abs.startswith("nature.com/articles"): # nature.com/articles/am201467
                    return _redirected_abs + ".pdf" # https://www.nature.com/articles/am201467.pdf
                
                elif _redirected_abs.startswith("sciencedirect.com/science/article"): # sciencedirect.com/science/article/pii/S1532046413001536
                    return "/".join((_redirected_abs, "pdf")) # sciencedirect.com/science/article/pii/S1532046413001536/pdf

                elif _redirected_abs.startswith("ieeexplore.ieee.org/document"): # ieeexplore.ieee.org/document/6620957
                    return "ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=" + _redirected_abs.split("/")[-1] # https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6620957

                elif _redirected_abs.startswith("link.springer.com/article"): # link.springer.com/article/10.1007/s10994-013-5398-8
                    _ = _redirected_abs.split("/")
                    return "/".join(("link.springer.com/content/pdf", _[-2], _[-1] + ".pdf")) # "https://link.springer.com/content/pdf/10.1007/s10994-013-5398-8.pdf"

                elif _redirected_abs.startswith("bmcsystbiol.biomedcentral.com/articles"): # bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-8-9
                    return _redirected_abs.replace("articles", "track/pdf") # "https://bmcsystbiol.biomedcentral.com/track/pdf/10.1186/1752-0509-8-9"

                elif _redirected_abs.startswith("bmcbioinformatics.biomedcentral.com/articles"): # bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-15-23
                    return _redirected_abs.replace("articles", "track/pdf") # "https://bmcbioinformatics.biomedcentral.com/track/pdf/10.1186/1471-2105-15-23"

                elif _redirected_abs.startswith("gmd.copernicus.org/articles"): # gmd.copernicus.org/articles/7/175/2014
                    _ = _redirected_abs.split("/")
                    return "-".join((_redirected_abs + "/gmd", _[-3], _[-2], _[-1] + ".pdf")) # https://gmd.copernicus.org/articles/7/175/2014/gmd-7-175-2014.pdf

                else:
                    return "None"
    
    def __write_redirection(self, i, redirected_abs):
        print("\t[+]Redirection: %s" % redirected_abs)
        self.data["Redirection"][i] = redirected_abs
    
    def __write_pdf(self, i, redirected_pdf):
        print("\t[+]Redirection_pdf: %s" % redirected_pdf)
        self.data["Redirection_pdf"][i] = redirected_pdf

    def __postprocess_redirected_url(self, url_redirected):
        # Remove www.
        if url_redirected.startswith("www."):
            url_redirected = url_redirected[4:]
        # Remove /
        if url_redirected.endswith('/'):
            url_redirected = url_redirected[:-1]
        
        # Replace %2F to /
        # url_redirected = url_redirected.replace("%2F", "/")
        # url_redirected = url_redirected.replace("%2f", "/")
        url_redirected = url_redirected.replace(r"%2[fF]", "/")

        # linkinghub
        if url_redirected.startswith("linkinghub.elsevier"): # linkinghub.elsevier.com/retrieve/pii/S1364815213002338
            _ = url_redirected.split("/")
            url_redirected = "/".join(("sciencedirect.com/science/article", _[-2], _[-1])) # sciencedirect.com/science/article/pii/S1364815213002338
        
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
    parser.add_argument('--postprocess_redirections',
                        action="store_true", default=False)

    args = parser.parse_args()

    scopus_preprocessor = ScopusPreprocessor(args.fpath,
                                             overwrite=args.overwrite,
                                             shuffle=args.shuffle,
                                             set_redirection=args.redirection,
                                             set_pdf=args.pdf,
                                             savepoint_interval=args.savepoint_interval,
                                             postprocess_redirections=args.postprocess_redirections)
    scopus_preprocessor.preprocess_scopus_csv()
