import pandas as pd
import json
import argparse

# from urllib.request import urlopen
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.parse import urlparse
from urllib.error import URLError
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from time import sleep, time
from datetime import datetime
from random import randint
import socket

from preprocessor import Preprocessor
from altmetric_it import AltmetricIt


class ScopusPreprocessor(Preprocessor):

    tup_new_columns = ("Redirection", "Redirection_pdf", "Altmetric ID", "AAS")
    tup_fields_unprocessed = ("None", "Err")
    tup_domains_exception = ("doi.apa.org",)
    
    opener = build_opener(HTTPCookieProcessor())
    # driver = webdriver.Chrome("./chromedriver_83")

    num_pass = 0
    num_fail = 0
    num_skip = 0
    num_new_domains = 0
    num_processed = 0

    fp_driver = "./chromedriver_83"
    page_load_trial = 5

    domains_aas_unavailable = (
        "dl.acm.org/doi/",
        "ieeexplore.ieee.org/document/",
        "inderscience.com/offer.php?id=",
        "misq.org/",
    )

    fp_dict_redirection_domains = "read_only/dict_redirection_domains.json"
    with open(fp_dict_redirection_domains, "r") as f:
        dict_redirection_domains = json.load(f)
    
    script_altmetricit = 'javascript:((function(){var a;a=function(){var a,b,c,d,e;b=document,e=b.createElement("script"),a=b.body,d=b.location;try{if(!a)throw 0;c="d1bxh8uas1mnw7.cloudfront.net";if(typeof runInject!="function")return e.setAttribute("src",""+d.protocol+"//"+c+"/assets/content.js?cb="+Date.now()),e.setAttribute("type","text/javascript"),e.setAttribute("onload","runInject()"),a.appendChild(e)}catch(f){return console.log(f),alert("Please wait until the page has loaded.")}},a(),void 0})).call(this);'
    max_times_find = 10
    sec_sleep = 0.5

    dict_domain_by_source_title_by_driver = {
        "Briefings in Bioinformatics": "academic.oup.com",
        "Database": "academic.oup.com",
        "Bioinformatics": "academic.oup.com",
        "Bulletin of the American Meteorological Society": "journals.ametsoc.org",
        "Molecular Biology and Evolution": "academic.oup.com",
        "Systematic Biology": "academic.oup.com",
        "Astrophysical Journal, Supplement Series": "iopscience.iop.org",
        "Astrophysical Journal Letters": "iopscience.iop.org"
    }
    dict_queue_by_domains = dict()  # {<domain>: {"last_time": time, "queue": [i, ...]}, ...}

    def __init__(
            self,
            fpath_scopus_csv,
            savepoint_interval=10,
            process_interval=60.0,
            overwrite=False,
            set_redirection=False,
            set_pdf=False,
            set_aas=False,
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
        self.set_aas = set_aas
        self.shuffle = shuffle
        self.postprocess_redirections = postprocess_redirections
        self.use_driver = use_driver if not set_aas else True
        if use_driver:
            print("[+]Opening Driver.")
            self.driver = webdriver.Chrome(self.fp_driver)
            self.driver.set_page_load_timeout(30)
            if set_aas:
                self.__install_bookmarklet()
            
        self.data = pd.read_csv(fpath_scopus_csv, header=0, sep=",", dtype=str)
        self.data = self.data.astype(str)
        
        self.num_papers = len(self.data)
        self.iter_i = iter(range(self.num_papers))

        if shuffle:
            print("[+]Shuffling records.")
            self.data = self.data.sample(frac=1).reset_index(drop=True)

        with open("read_only/source_pub_dict.txt") as f:
            self.dict_source_pub = json.load(f)

    def preprocess_scopus_csv(self):
        self.time_start = time()
        # Create columns
        for _col in self.tup_new_columns:
            try:
                self.data[_col]
            except KeyError:
                self.data[_col] = "None"

        # Preprocess given columns
        self.__preprocess_default_columns()

        # Get youtube search queries
        self.__add_yt_direct_queries(overwrite=self.overwrite)

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
    
    def __add_yt_direct_queries(self, overwrite):
        while True:
            _i = self.__get_next_i(overwrite)
            print("[+]i = %s\t%d out of %d papers remaining." % (_i, self.num_papers - self.num_processed, self.num_papers))
            if _i == None:
                if len(self.dict_queue_by_domains) == 0:
                    # Done
                    # Save
                    self.__save()
                    # Report
                    print("\n# papers: %d\t# fail: %d\t# pass: %d\t# skip: %d\t# new domains: %d" %
                        (self.num_papers, self.num_fail, self.num_pass, self.num_skip, self.num_new_domains))
                    print("Done.")
                    # pd.Series.astype(str) + ',' + pd.Series.astype(str)
                    return self
                else:
                    print("[-]No available paper at the moment.")
                    sleep(1.0)
                    continue

            elif _i == "pass":
                print("\t[+]Passing.")

            else:
                if self.__write_data_by_i(_i, overwrite):
                    # flag_sleep
                    sleep(1.0)
            
            self.num_processed += 1
            self.__calc_remaining_time()
            # Checkpoint
            self.__check_savepoint(self.num_processed)
    
    def __write_data_by_i(self, i, overwrite):
        _flag_sleep = False
        _flag_driver_opened = False
        # Redirection & pdf
        # if (self.set_redirection or self.set_pdf)\
        #     and (self.data["Redirection"][i] in self.tup_fields_unprocessed or overwrite == True):
        if not (self.check_i_redirection_already_processed(i, overwrite) and self.check_i_pdf_already_processed(i, overwrite)):
            _url_redirected = self.__url_without_open(i)
            if _url_redirected != False:
                self.num_skip += 1
                print("\t[+]Skip opening.")
                if self.set_redirection:
                    self.__write_redirection(i, _url_redirected[0])
                if self.set_pdf:
                    self.__write_pdf(i, _url_redirected[1])
                if self.set_aas:
                    # Open url
                    self.__driver_get("http://" + _url_redirected[0])
                    # self.driver.get(_url_redirected[0])
                    _flag_driver_opened = True
        
            else:
                # Build up url
                _url = "https://www.doi.org/" + self.data["DOI"][i]
                # Get redirection
                if self.data["Source title"][i] in self.dict_domain_by_source_title_by_driver.keys() or self.set_aas:
                    if self.use_driver:
                        self.__write_redirection_by_driver(i, _url)
                        _flag_driver_opened = True
                    else:
                        print("\t[-]Driver required but not available.")
                        self.num_pass += 1
                else:
                    self.__write_redirection_by_open(i, _url)
                # self.__write_redirection_by_driver(
                #     i, _url) if self.data["Source title"][i] in self.dict_domain_by_source_title_by_driver.keys() else self.__write_redirection_by_open(i, _url)

            if self.set_pdf:
                _redirected_pdf = self.__get_redirected_pdf(i)
                self.__write_pdf(i, _redirected_pdf)
        
        # Altmetric ID & AAS
        # if self.set_aas\
        #     and (self.data["Altmetric ID"][i] in ("None", "Err") or overwrite == True):
        if not self.check_i_aas_already_processed(i, overwrite):
            _citation_id, _aas = self.__get_cid_aas(i, _flag_driver_opened)
            _flag_sleep = self.__write_altmetric_id(i, _citation_id)
            _flag_sleep = self.__write_aas(i, _aas)
            
            # if self.data["Source title"][i] in self.dict_domain_by_source_title_by_driver.keys():
            #     self.__sleep_process()

        return _flag_sleep
    
    def check_i_redirection_already_processed(self, i, overwrite):
        print("\t[+]Redirection: %s\tAlready processed: %s" % (self.data["Redirection"][i], not (self.set_redirection and (self.data["Redirection"][i] in self.tup_fields_unprocessed or overwrite == True))))
        return not (self.set_redirection and (self.data["Redirection"][i] in self.tup_fields_unprocessed or overwrite == True))
    
    def check_i_pdf_already_processed(self, i, overwrite):
        print("\t[+]PDF: %s\tAlready processed: %s" % (self.data["Redirection_pdf"][i], not (self.set_pdf and (self.data["Redirection_pdf"][i] in self.tup_fields_unprocessed or overwrite == True))))
        return not (self.set_pdf and (self.data["Redirection_pdf"][i] in self.tup_fields_unprocessed or overwrite == True))
    
    def check_i_aas_already_processed(self, i, overwrite):
        print("\t[+]Altmetric ID: %s\tAlready processed: %s" % (self.data["Altmetric ID"][i], not (self.set_aas and (self.data["Altmetric ID"][i] in self.tup_fields_unprocessed or overwrite == True))))
        return not (self.set_aas and (self.data["Altmetric ID"][i] in self.tup_fields_unprocessed or overwrite == True))

    def check_i_already_processed(self, i, overwrite):
        return self.check_i_redirection_already_processed(i, overwrite) and self.check_i_pdf_already_processed(i, overwrite) and self.check_i_aas_already_processed(i, overwrite)
    
    def __get_next_i(self, overwrite):
        _current_time = time()
        _i = self.__get_next_i_from_queue(_current_time)
        if _i == None:
            try:
                _i = next(self.iter_i)
            except StopIteration:
                # Only queues remain.
                return None
            else:
                if self.check_i_already_processed(_i, overwrite):
                    return "pass"
                _next_source_title = self.data["Source title"][_i]
                # print("\tNext title: %s" % _next_source_title)
                if _next_source_title in self.dict_domain_by_source_title_by_driver:
                    _next_domain = self.dict_domain_by_source_title_by_driver[_next_source_title]
                    print("\tNext domain: %s" % _next_domain)
                    if _next_domain in self.dict_queue_by_domains:
                        # Append
                        self.dict_queue_by_domains[_next_domain]["queue"].append(_i)
                        return None
                    else:
                        # Create empty queue
                        print("\t[+]Create empty queue.")
                        self.dict_queue_by_domains[_next_domain] = {
                            "last_time": _current_time,
                            "queue": list()
                        }
        return _i
    
    def __calc_remaining_time(self):
        if self.num_processed == 0:
            return self
        _sec_per_paper = (time() - self.time_start) / self.num_processed
        _min_remaining = int((self.num_papers - self.num_processed) * _sec_per_paper // 60)
        print("Progress: %2.1f \tAve. time per paper: %.2f secs\tRemaining time estimated: %d mins" % (100 * self.num_processed / self.num_papers, _sec_per_paper, _min_remaining))
        return self
        
    
    def __get_cid_aas(self, i, flag_driver_opened):
        _redirection = self.data["Redirection"][i]
        if _redirection in ("Err", "None", "nan"):
            print("\t[-]Cannot Altmetric-it as Redirection not available.")
            return "None", "None"
        
        # Check altmetric available for redirection
        for _domain in self.domains_aas_unavailable:
            if _redirection.startswith(_domain):
                print("\t[-]Altmetric-it unavailable for domain: %s" % _domain)
                return "None", "None"

        if not flag_driver_opened:
            print("\t[+]Opening: %s" % _redirection)
            # self.driver.get("http://" + _redirection)
            self.__driver_get("http://" + _redirection)
        
        return self.__get_cid_aas_from_current_page()
    
    def __get_cid_aas_from_current_page(self):        
        # Get div.wrapper
        _div_wrapper = self.__get_div_wrapper_from_current_page()
        if _div_wrapper == False:
            return "Err", "Err"

        # Get Altmetric ID, AAS
        _citation_id, _aas = self.__get_cid_aas_from_div_wrapper(_div_wrapper)
        if _citation_id == False:  # Cannot altmetric-it.
            self.msg_error = '[-]Cannot altmetric-it.'
            print('\t%s' % self.msg_error)

        return _citation_id, _aas

    def __get_div_wrapper_from_current_page(self):
        self.driver.execute_script(self.script_altmetricit)

        _div_wrapper = self.__find_recursive(
            self.driver, 'altmetric-wrapper', 'id', max_times_find=self.max_times_find)
        if _div_wrapper == False:
            return False

        # Case1: error
        _error = self.__find_recursive(
            _div_wrapper, 'error', 'class', max_times_find=1)
        if _error != False:
            return False

        # Case2: No altmetric
        # if not self.__altmetric_exists(_div_wrapper):
            # return False

        return _div_wrapper
    
    def __get_cid_aas_from_div_wrapper(self, div_wrapper):
        _citation_id, _aas = "nan", "nan"

        _div_donut = self.__find_recursive(div_wrapper, 'donut', 'class', max_times_find=3)
        if _div_donut == False:
            # Absence of div.donut means AAS not assigned.
            return _citation_id, _aas
        _a_donut = self.__find_recursive(_div_donut, 'a', 'tag', max_times_find=3)
        if _a_donut == False:
            return _citation_id, _aas

        # Search for cid
        for _query in urlparse(_a_donut.get_attribute('href')).query.split('&'):
            if _query.startswith("citation_id="):
                _citation_id = _query[12:]
        
        _img_donut = self.__find_recursive(_div_donut, 'img', 'tag', max_times_find=3)
        if _img_donut == False:
            print("[-]img donut: FALSE")
            return _citation_id, _aas
        
        # Search for score
        for _query in urlparse(_img_donut.get_attribute('src')).query.split('&'):
            if _query.startswith("score="):
                _aas = int(_query[6:])
        
        if _aas == False:
            _aas = 0
        
        return _citation_id, _aas
    
    def __find_recursive(self, WebElement, name, by='class', multiple=False, max_times_find=1):
        _method = self.__get_find_method(WebElement, multiple, by)
        _times_find = 0

        while True:
            _times_find += 1
            try:
                print('\tFind by %s: %s(%d th try)' % (by, name, _times_find))

                _elements = _method(name)
            except:  # NoSuchElementException
                print('\t%s %s not found.' % (by, name))
                if _times_find < max_times_find:
                    print('\tRetrying...')
                    sleep(self.sec_sleep)
                    pass
                else:
                    print('\tExceeded max_times_find.')
                    return False
            else:
                print('\t%s %s found.' % (by, name))
                return _elements
    
    def __get_find_method(self, WebElement, multiple, by):
        _dict_find_methods = {
            True: {
                'class': WebElement.find_elements_by_class_name,
                'tag': WebElement.find_elements_by_tag_name
            },
            False: {
                'id': WebElement.find_element_by_id,
                'class': WebElement.find_element_by_class_name,
                'tag': WebElement.find_element_by_tag_name
            }
        }
        return _dict_find_methods[multiple][by]
    
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
                    or (self.overwrite == "Err" and not ((self.set_redirection and self.data["Redirection"][_i] in self.tup_domains_exception) or (self.set_pdf and self.data["Redirection_pdf"][_i] in self.tup_domains_exception))):
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
                if self.set_aas:
                    # Open
                    # self.driver.get(_url_redirected[0])
                    self.__driver_get(_url_redirected[0])

            else:
                if self.set_redirection:
                    # Build up url
                    _url = "https://www.doi.org/" + self.data["DOI"][_i]
                    # Get redirection
                    if self.data["Source title"][_i] in self.dict_domain_by_source_title_by_driver.keys():
                        if self.use_driver:
                            self.__write_redirection_by_driver(_i, _url)
                        else:
                            print("\t[-]Driver required but not available.")
                            self.num_pass += 1
                    else:
                        self.__write_redirection_by_open(_i, _url)
                    # self.__write_redirection_by_driver(
                    #     _i, _url) if self.data["Source title"][_i] in self.dict_domain_by_source_title_by_driver.keys() else self.__write_redirection_by_open(_i, _url)

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

    def __write_redirection_by_driver(self, i, url):
        # print("\t[+]Opening Driver.")
        # _driver = webdriver.Chrome(self.fp_driver)
        print("\t[+]Opening url:")
        print("\t\t%s" % url)
        # self.driver.get(url)
        self.__driver_get(url)
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
        # self.__sleep_process()

        return self

    def __get_next_i_from_queue(self, current_time):
        _i = None
        _max_interval = 0.0
        _target_domain = None
        _domains_to_be_removed = list()
        for _domain in self.dict_queue_by_domains:
            _interval = current_time - self.dict_queue_by_domains[_domain]["last_time"]
            if _interval > self.process_interval:
                if len(self.dict_queue_by_domains[_domain]["queue"]) == 0:
                    _domains_to_be_removed.append(_domain)
                elif _interval > _max_interval and len(self.dict_queue_by_domains[_domain]["queue"]) > 0:
                    _max_interval = _interval
                    _target_domain = _domain
        
        # Remove domains
        for _domain in _domains_to_be_removed:
            self.dict_queue_by_domains.pop(_domain)
        
        if _target_domain != None:
            _i = self.dict_queue_by_domains[_target_domain]["queue"].pop(0)
            # Replace last_time
            self.dict_queue_by_domains[_target_domain]["last_time"] = current_time
        
        print("\t".join(["Domains in queue:"] + list(map(lambda _key: "%s: %d" % (_key, len(self.dict_queue_by_domains[_key]["queue"])), self.dict_queue_by_domains))))
        return _i
    
    def __sleep_process(self):
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
            if _redirected_abs in self.tup_fields_unprocessed:
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
    
    def __get_flag_sleep(self, value):
        return False if value in self.tup_fields_unprocessed else True

    def __write_redirection(self, i, redirected_abs):
        print("\t[+]Redirection: %s" % redirected_abs)
        self.data["Redirection"][i] = redirected_abs

    def __write_pdf(self, i, redirected_pdf):
        print("\t[+]Redirection_pdf: %s" % redirected_pdf)
        self.data["Redirection_pdf"][i] = redirected_pdf
    
    def __write_altmetric_id(self, i, altmetric_id):
        print("\t[+]Altmetric ID: %s" % altmetric_id)
        self.data["Altmetric ID"][i] = altmetric_id
        return self.__get_flag_sleep(altmetric_id)
    
    def __write_aas(self, i, aas):
        print("\t[+]AAS: %s" % aas)
        self.data["AAS"][i] = aas
        return self.__get_flag_sleep(aas)

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
            print("[+]Checkpoint: Saving.")
            self.__save()

        return self

    def __save(self):
        # data
        self.data.astype(str).to_csv(self.fpath_scopus_csv, index=False)

        # redirection domains
        with open(self.fp_dict_redirection_domains, "w") as f:
            json.dump(self.dict_redirection_domains, f)
    
    def __install_bookmarklet(self, first_name=None, last_name=None, email=None):
        print("[+]Installing bookmarklet.")
        # self.driver.get('https://www.altmetric.com/products/free-tools/bookmarklet/')
        self.__driver_get('https://www.altmetric.com/products/free-tools/bookmarklet/')
        sleep(15)
        self.driver.switch_to_frame(
            self.driver.find_element_by_tag_name('iframe'))
        if first_name == None:
            first_name = self.__get_random_str(3, 'char')
            print('Randomize first name:', first_name)
        if last_name == None:
            last_name = self.__get_random_str(2, 'char')
            print('Randomize last name:', last_name)
        if email == None:
            email = self.__get_random_str(10, 'num') + '@g.ecc.u-tokyo.ac.jp'
            print('Randomize email:', email)
        job = 'Student'
        organization = 'The Univ. of Tokyo'

        _script_first_name = "document.getElementsByClassName('first_name')[0].children[1].setAttribute('value', '%s');" % first_name
        _script_last_name = "document.getElementsByClassName('last_name')[0].children[1].setAttribute('value', '%s');" % last_name
        _script_email = "document.getElementsByClassName('email')[0].children[1].setAttribute('value', '%s');" % email
        _script_job = "document.getElementsByClassName('job_title')[0].children[1].setAttribute('value', '%s');" % job
        _script_organization = "document.getElementsByClassName('company')[0].children[1].setAttribute('value', '%s');" % organization
        _script_org_type = "document.getElementsByClassName('Organization_Type')[0].children[1].lastElementChild.setAttribute('selected', 'selected');document.getElementsByClassName('Organization_Type')[0].children[1].firstElementChild.removeAttribute('selected');"

        self.driver.execute_script(_script_first_name)
        self.driver.execute_script(_script_last_name)
        self.driver.execute_script(_script_email)
        self.driver.execute_script(_script_job)
        self.driver.execute_script(_script_organization)
        self.driver.execute_script(_script_org_type)

        _input_submit = self.__find_recursive(
            self.driver, 'submit', 'class', max_times_find=self.max_times_find).find_element_by_tag_name('input')
        print(_input_submit)
        _input_submit.click()
        sleep(5)

        _a_install_bookmarklet = self.__find_recursive(
            self.driver, 'install-bookmarklet', 'id', max_times_find=self.max_times_find)
        print('Clicking: #install-bookmarket')
        _a_install_bookmarklet.click()
        sleep(1)

        # _href = self.driver.execute_script("document.getElementById('install-bookmarklet').getAttribute('href')")
        # _href = _a_install_bookmarklet.get_attribute('href')
        self.driver.switch_to_default_content()
        print('Executing script:', self.script_altmetricit)
        self.driver.execute_script(self.script_altmetricit)
        sleep(5)

        return self
    
    def __get_random_str(self, length, content_type):
        _chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
        if content_type == 'char':
            _chars = _chars[:-10]
        elif content_type == 'num':
            _chars = _chars[-10:]
        _num_chars = len(_chars)
        _rand_str = ''
        cur_len = 0
        while True:
            cur_len += 1
            if cur_len > length:
                break
            _rand_str += _chars[randint(0, _num_chars - 1)]
        return _rand_str
    
    def __driver_get(self, url):
        _trial = 0
        while _trial < self.page_load_trial:
            try:
                _trial += 1
                self.driver.get(url)
            except TimeoutException:
                continue
            else:
                return True

        raise TimeoutException("Trial failed.")


if __name__ == "__main__":
    # fpath = "scopus/scopus_math+comp_top5perc_1401.csv"
    # scopus_preprocessor = ScopusPreprocessor(fpath, overwrite=True, shuffle=True)
    # scopus_preprocessor.preprocess_scopus_csv()

    parser = argparse.ArgumentParser()
    parser.add_argument('--fpath', default=None)
    parser.add_argument('--overwrite', action="store_true", default="Err")
    parser.add_argument('--redirection', action="store_true", default=False)
    parser.add_argument('--pdf', action="store_true", default=False)
    parser.add_argument('--aas', action="store_true", default=False)
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
                                                 set_aas=args.aas,
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
                                                     set_aas=args.aas,
                                                     savepoint_interval=args.savepoint_interval,
                                                     process_interval=args.process_interval,
                                                     postprocess_redirections=args.postprocess_redirections)
            scopus_preprocessor.preprocess_scopus_csv()
