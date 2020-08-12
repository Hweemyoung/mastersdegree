import pandas as pd
import json
import argparse

# from urllib.request import urlopen
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlparse
from urllib.error import URLError
from selenium import webdriver
from time import sleep
from datetime import datetime
import socket

from preprocessor import Preprocessor


class ScopusPreprocessor(Preprocessor):
    tup_new_columns = ("Redirection", "Redirection_pdf",)
    tup_domains_exception = ("doi.apa.org",)

    opener = build_opener(HTTPCookieProcessor())
    # driver = webdriver.Chrome("./chromedriver_83")
    num_pass = 0
    num_fail = 0
    num_skip = 0
    num_new_domains = 0
    fp_driver = "./chromedriver_83"
    source_titles_by_driver = ("Briefings in Bioinformatics",
                               "Database",
                               "Bioinformatics",
                               "Bulletin of the American Meteorological Society",
                               "Molecular Biology and Evolution",
                               "Systematic Biology",)

    fp_dict_redirection_domains = "read_only/dict_redirection_domains.json"
    with open(fp_dict_redirection_domains, "r") as f:
        dict_redirection_domains = json.load(f)

    def __init__(
            self,
            fpath_scopus_csv,
            savepoint_interval=10,
            process_interval=60.0,
            overwrite=False,
            set_redirection=False,
            set_pdf=False,
            shuffle=False,
            postprocess_redirections=False,
            use_driver=True):
        # super(ScopusPreprocessor, self).__init__()
        self.fpath_scopus_csv = fpath_scopus_csv
        self.process_interval = process_interval
        self.savepoint_interval = savepoint_interval
        self.overwrite = overwrite
        self.set_redirection = set_redirection
        self.set_pdf = set_pdf
        self.shuffle = shuffle
        self.postprocess_redirections = postprocess_redirections
        self.use_driver = use_driver
        if use_driver:
            print("[+]Opening Driver.")
            self.driver = webdriver.Chrome(self.fp_driver)

        self.data = pd.read_csv(fpath_scopus_csv, header=0, sep=",", dtype=str)
        self.data = self.data.astype(str)
        self.num_papers = len(self.data)
        if shuffle:
            print("[+]Shuffling records.")
            self.data = self.data.sample(frac=1).reset_index(drop=True)

        with open("read_only/source_pub_dict.txt") as f:
            self.dict_source_pub = json.load(f)

    def preprocess_scopus_csv(self):
        # Create columns
        for _col in self.tup_new_columns:
            try:
                self.data[_col]
            except KeyError:
                self.data[_col] = "None"

        # Preprocess given columns
        self.__preprocess_default_columns()

        # Get youtube search queries
        self.__add_yt_direct_queries()

        # Close _driver
        if self.use_driver:
            self.driver.close()

        return self

    def __preprocess_default_columns(self):
        print("[+]Preprocessing DOIs.")
        # DOI
        for _i, _doi in enumerate(self.data["DOI"]):
            # TCYB
            # 10.1109/TCYB.2017.2765343Y
            if "/TCYB" in _doi and _doi.endswith("Y"):
                self.data["DOI"][_i] = _doi[:-1]  # 10.1109/TCYB.2017.2765343

            # TPDS
            # 10.1109/TPDS.2018.2864184Y
            elif "/TPDS" in _doi and _doi.endswith("Y"):
                self.data["DOI"][_i] = _doi[:-1]  # 10.1109/TPDS.2018.2864184

            # TIP
            # 10.1109/TIP.2018.2883554Y
            elif "/TIP" in _doi and _doi.endswith("Y"):
                self.data["DOI"][_i] = _doi[:-1]  # 10.1109/TIP.2018.2883554

        return self

    def __add_yt_direct_queries(self):
        # DOI
        # _S_doi = data["DOI"]
        # Redirected urls
        self.__set_redirections()
        print("\n# papers: %d\t# fail: %d\t# pass: %d\t# skip: %d\t# new domains: %d" %
              (self.num_papers, self.num_fail, self.num_pass, self.num_skip, self.num_new_domains))

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

            # Case12: International Journal of Bio-Inspired Computation
            elif self.dict_source_pub[_source_title] == "Inderscience":
                # http://www.inderscience.com/offer.php?id=64989
                return ("inderscience.com/offer.php?id=" + str(int(self.data["DOI"][i].split(".")[-1])),  # inderscience.com/offer.php?id=66365
                        "nan")

            # Case: Evolutionary Computation
            elif self.dict_source_pub[_source_title] == "MIT Press":
                # https://www.mitpressjournals.org/doi/10.1162/EVCO_a_00116
                return ("mitpressjournals.org/doi/" + self.data["DOI"][i],  # mitpressjournals.org/doi/10.1162/EVCO_a_00116
                        "nan")

            # Case: "Annual Reviews Inc."
            elif self.dict_source_pub[_source_title] == "Annual Reviews Inc.":
                # https://www.annualreviews.org/doi/10.1146/annurev-ento-011613-162056
                return ("annualreviews.org/doi/" + self.data["DOI"][i],  # annualreviews.org/doi/10.1146/annurev-ento-011613-162056
                        "nan")

            # Case: "Environmental Health Perspectives"
            elif self.dict_source_pub[_source_title] == "Environmental Health Perspectives":
                # https://ehp.niehs.nih.gov/doi/10.1289/ehp.122-A20
                return ("ehp.niehs.nih.gov/doi/" + self.data["DOI"][i],  # mitpressjournals.org/doi/10.1162/EVCO_a_00116
                        "nan")

            # Case: "Institute of Physics Publishing"
            elif self.dict_source_pub[_source_title] == "Institute of Physics Publishing":
                # https://iopscience.iop.org/article/10.1088/0004-637X/781/2/60
                return ("iopscience.iop.org/article/" + self.data["DOI"][i],  # mitpressjournals.org/doi/10.1162/EVCO_a_00116
                        "nan")

            # Case: "University of Chicago Press"
            elif self.dict_source_pub[_source_title] == "University of Chicago Press":
                # https://www.journals.uchicago.edu/doi/10.1086/674992
                return ("journals.uchicago.edu/doi/" + self.data["DOI"][i],  # journals.uchicago.edu/doi/10.1086/674992
                        "nan")

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
        # elif _source_title in ("International Journal of Bio-Inspired Computation",):
        #     # http://www.inderscience.com/offer.php?id=64989
        #     return ("inderscience.com/offer.php?id=" + str(int(self.data["DOI"][i].split(".")[-1])),  # content.iospress.com/articles/argument-and-computation/869766
        #             "nan")

        # Case12: Journal of Information Technology
        # elif _source_title in ("Journal of Information Technology",):
        #     # https://journals.sagepub.com/doi/10.1057/jit.2013.29
        #     return ("inderscience.com/offer.php?id=" + str(int(self.data["DOI"][i].split(".")[-1])),  # content.iospress.com/articles/argument-and-computation/869766
        #             "nan")

        # Case13: Journal of Environmental Informatics
        elif _source_title in ("Journal of Environmental Informatics",):
            # 10.3808/jei.201400255
            return ("jeionline.org/index.php?journal=mys&page=article&op=view&path%5B%5D=" + self.data["DOI"][i].split(".")[-1],  # jeionline.org/index.php?journal=mys&page=article&op=view&path%5B%5D=201400255
                    "nan")
        # http://www.jeionline.org/index.php?journal=mys&page=article&op=view&path%5B%5D=201400255

        elif _source_title in ("PLoS Biology",):
            # 10.1371/journal.pbio.1001817
            return ("journals.plos.org/plosbiology/article?id=" + self.data["DOI"][i],  # https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1001817
                    "nan")

        elif _source_title in ("PLoS Genetics",):
            # "10.1371/journal.pgen.1004148"
            return ("journals.plos.org/plosgenetics/article?id=" + self.data["DOI"][i],  # https://journals.plos.org/plosgenetics/article?id=10.1371/journal.pgen.1004148
                    "nan")

        elif _source_title in ("Environmental Health Perspectives",):
            # 10.1289/ehp.1206324
            return ("ehp.niehs.nih.gov/doi/" + self.data["DOI"][i],  # https://ehp.niehs.nih.gov/doi/10.1289/ehp.1306656
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
                self.__check_savepoint(_i)
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
                    if self.data["Source title"][_i] in self.source_titles_by_driver:
                        if self.use_driver:
                            self.__write_redirection_by_driver(_i, _url)
                        else:
                            print("\t[-]Driver required but not available.")
                            self.num_pass += 1
                    else:
                        self.__write_redirection_by_open(_i, _url)
                    # self.__write_redirection_by_driver(
                    #     _i, _url) if self.data["Source title"][_i] in self.source_titles_by_driver else self.__write_redirection_by_open(_i, _url)

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

            self.__check_savepoint(_i)

        # Save
        self.__save()

        return self

    def __write_redirection_by_driver(self, i, url):
        # print("\t[+]Opening Driver.")
        # _driver = webdriver.Chrome(self.fp_driver)
        print("\t[+]Opening url:")
        print("\t\t%s" % url)
        self.driver.get(url)
        # Get raw url
        # print("\t[+]Raw redirection:")
        # print("\t\t%s" % self.driver.current_url)
        # Postprocess redirection
        _redirected_abs = self.__postprocess_redirected_url(
            self.driver.current_url)
        # Write
        self.__write_redirection(i, _redirected_abs)
        # Close _driver
        # _driver.close()
        # Sleep
        if self.process_interval != None:
            print("\t[+]Sleeping for %f secs." % self.process_interval)
            sleep(self.process_interval)

        return self

    def __write_redirection_by_open(self, i, url):
        try:
            print("\t[+]Opening url:")
            print("\t\t%s" % url)
            _res = self.opener.open(url, timeout=30)
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
        finally:
            # Postprocess redirection
            _redirected_abs = self.__postprocess_redirected_url(
                _redirected_abs)
            self.__write_redirection(i, _redirected_abs)

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
                # nature.com/articles/am201467
                if _redirected_abs.startswith("nature.com/articles"):
                    return _redirected_abs + ".pdf"  # https://www.nature.com/articles/am201467.pdf

                # sciencedirect.com/science/article/pii/S1532046413001536
                elif _redirected_abs.startswith("sciencedirect.com/science/article"):
                    # sciencedirect.com/science/article/pii/S1532046413001536/pdf
                    return "/".join((_redirected_abs, "pdf"))

                # ieeexplore.ieee.org/document/6620957
                elif _redirected_abs.startswith("ieeexplore.ieee.org/document"):
                    # https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=6620957
                    return "ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=" + _redirected_abs.split("/")[-1]

                # link.springer.com/article/10.1007/s10994-013-5398-8
                elif _redirected_abs.startswith("link.springer.com/article"):
                    _ = _redirected_abs.split("/")
                    # "https://link.springer.com/content/pdf/10.1007/s10994-013-5398-8.pdf"
                    return "/".join(("link.springer.com/content/pdf", _[-2], _[-1] + ".pdf"))

                # bmcsystbiol.biomedcentral.com/articles/10.1186/1752-0509-8-9
                elif _redirected_abs.startswith("bmcsystbiol.biomedcentral.com/articles"):
                    # "https://bmcsystbiol.biomedcentral.com/track/pdf/10.1186/1752-0509-8-9"
                    return _redirected_abs.replace("articles", "track/pdf")

                # bmcbioinformatics.biomedcentral.com/articles/10.1186/1471-2105-15-23
                elif _redirected_abs.startswith("bmcbioinformatics.biomedcentral.com/articles"):
                    # "https://bmcbioinformatics.biomedcentral.com/track/pdf/10.1186/1471-2105-15-23"
                    return _redirected_abs.replace("articles", "track/pdf")

                # gmd.copernicus.org/articles/7/175/2014
                elif _redirected_abs.startswith("gmd.copernicus.org/articles"):
                    _ = _redirected_abs.split("/")
                    # https://gmd.copernicus.org/articles/7/175/2014/gmd-7-175-2014.pdf
                    return "-".join((_redirected_abs + "/gmd", _[-3], _[-2], _[-1] + ".pdf"))

                # https://academic.oup.com/bib/article/15/1/108/187383
                elif _redirected_abs.startswith("academic.oup.com"):
                    return "nan"  # Cannot be regularized...

                else:
                    return "None"

    def __write_redirection(self, i, redirected_abs):
        print("\t[+]Redirection: %s" % redirected_abs)
        self.data["Redirection"][i] = redirected_abs

    def __write_pdf(self, i, redirected_pdf):
        print("\t[+]Redirection_pdf: %s" % redirected_pdf)
        self.data["Redirection_pdf"][i] = redirected_pdf

    def __postprocess_redirected_url(self, url_redirected):
        if url_redirected == "Err":
            return url_redirected
        
        # Remove protocol(https?://www.), query, hash, ...
        url_redirected = urlparse(url_redirected)

        # Append
        url_redirected = url_redirected.netloc + url_redirected.path
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
        # linkinghub.elsevier.com/retrieve/pii/S1364815213002338
        if url_redirected.startswith("linkinghub.elsevier"):
            _ = url_redirected.split("/")
            # sciencedirect.com/science/article/pii/S1364815213002338
            url_redirected = "/".join(
                ("sciencedirect.com/science/article", _[-2], _[-1]))
        
        # Add to dict_redirection_domains.json
        self.__append_to_domains(url_redirected.split("/")[0])

        return url_redirected
    
    def __append_to_domains(self, domain_name):
        if domain_name in self.tup_domains_exception:
            pass
        elif domain_name not in self.dict_redirection_domains:
            _datetime = datetime.now().strftime("%Y-%m-%dT%XZ")
            self.dict_redirection_domains[domain_name] = {"datetime": _datetime}
            self.num_new_domains += 1
            print("\t[+]Domain added.")
            print("\t\tDomain: %s\tDatetime: %s" % (domain_name, _datetime))
        
        return self

    def __check_savepoint(self, enum):
        if (enum+1) % self.savepoint_interval == 0:
            self.__save()

        return self

    def __save(self):
        # data
        self.data.astype(str).to_csv(self.fpath_scopus_csv, index=False)

        # redirection domains
        with open(self.fp_dict_redirection_domains, "w") as f:
            json.dump(self.dict_redirection_domains, f)


if __name__ == "__main__":
    # fpath = "scopus/scopus_math+comp_top5perc_1401.csv"
    # scopus_preprocessor = ScopusPreprocessor(fpath, overwrite=True, shuffle=True)
    # scopus_preprocessor.preprocess_scopus_csv()

    parser = argparse.ArgumentParser()
    parser.add_argument('--fpath', default=None)
    parser.add_argument('--overwrite', action="store_true", default="Err")
    parser.add_argument('--redirection', action="store_true", default=False)
    parser.add_argument('--pdf', action="store_true", default=False)
    parser.add_argument('--shuffle', action="store_true", default=False)
    parser.add_argument('--savepoint_interval', type=int, default=10)
    parser.add_argument('--process_interval', type=float, default=60.0)
    parser.add_argument('--postprocess_redirections',
                        action="store_true", default=False)
    parser.add_argument('--no_driver', action="store_false", default=True)

    args = parser.parse_args()

    if args.fpath != None:
        scopus_preprocessor = ScopusPreprocessor(args.fpath,
                                                 overwrite=args.overwrite,
                                                 shuffle=args.shuffle,
                                                 set_redirection=args.redirection,
                                                 set_pdf=args.pdf,
                                                 savepoint_interval=args.savepoint_interval,
                                                 process_interval=args.process_interval,
                                                 postprocess_redirections=args.postprocess_redirections,
                                                 use_driver=args.no_driver)
        scopus_preprocessor.preprocess_scopus_csv()

    else:
        # _list_fpath = ["scopus/scopus_math+comp_top5perc_1905.csv",
        #             "scopus/scopus_math+comp_top5perc_1906.csv",
        #             ]
        for _fpath in _list_fpath:
            args.fpath = _fpath
            print("[+]fpath: %s" % args.fpath)
            scopus_preprocessor = ScopusPreprocessor(args.fpath,
                                                     overwrite=args.overwrite,
                                                     shuffle=args.shuffle,
                                                     set_redirection=args.redirection,
                                                     set_pdf=args.pdf,
                                                     savepoint_interval=args.savepoint_interval,
                                                     process_interval=args.process_interval,
                                                     postprocess_redirections=args.postprocess_redirections)
            scopus_preprocessor.preprocess_scopus_csv()
