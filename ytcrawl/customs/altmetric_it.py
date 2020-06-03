from selenium import webdriver
from datetime import datetime
from time import sleep
from os import listdir
import os.path as osp
import json
import re
from random import randint
from urllib.parse import urlparse

from db_handler import DBHandler


class AltmetricIt:
    db_handler = DBHandler()

    dict_drivers = {
        'chrome': webdriver.Chrome
    }
    list_tabs_altmetric = ['', 'news', 'blogs', 'twitter',
                           'wikipedia', 'google', 'reddit', 'video']
    dict_tabs_args = dict()

    script_altmetricit = 'javascript:((function(){var a;a=function(){var a,b,c,d,e;b=document,e=b.createElement("script"),a=b.body,d=b.location;try{if(!a)throw 0;c="d1bxh8uas1mnw7.cloudfront.net";if(typeof runInject!="function")return e.setAttribute("src",""+d.protocol+"//"+c+"/assets/content.js?cb="+Date.now()),e.setAttribute("type","text/javascript"),e.setAttribute("onload","runInject()"),a.appendChild(e)}catch(f){return console.log(f),alert("Please wait until the page has loaded.")}},a(),void 0})).call(this);'

    regex_citation_id = re.compile(r'citation_id=\d{6,10}')
    regex_tweet_id = re.compile(r'tweet_id=\d{16,22}')
    regex_abs = re.compile(r'https?://arxiv.org/abs/\d{3,5}.\d{3,5}')

    msg_error = ''
    dict_failed = dict()

    def __init__(self, args):
        #  driver='chrome', p_driver='./chromedriver', new_bookmarklet=True, max_times_find=5, sec_sleep=1.0, ...
        self.driver = self.dict_drivers[args['driver']](args['p_driver'])
        self.max_times_find = args['max_times_find']
        self.sec_sleep = args['sec_sleep']
        self.table = args['table']
        self.overwrite = args['overwrite']  # Not used...
        # self.__init_find_methods()
        self.__set_dict_tabs_args(args)
        if args['new_bookmarklet']:
            self.__install_bookmarklet()

    def __set_dict_tabs_args(self, args):
        self.dict_tabs_args['news'] = args['news']
        self.dict_tabs_args['blogs'] = args['blogs']
        self.dict_tabs_args['twitter'] = args['twitter']
        self.dict_tabs_args['wikipedia'] = args['wikipedia']
        self.dict_tabs_args['google'] = args['google']
        self.dict_tabs_args['reddit'] = args['reddit']
        self.dict_tabs_args['video'] = args['video']

    def __init_find_methods(self):
        self.dict_find_methods = {
            True: {
                'class': self.driver.find_elements_by_class_name,
                'tag': self.driver.find_elements_by_tag_name
            },
            False: {
                'id': self.driver.find_element_by_id,
                'class': self.driver.find_element_by_class_name,
                'tag': self.driver.find_element_by_tag_name
            }
        }

    def __get_random_str(self, length, content_type=None):
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

    def __install_bookmarklet(self, first_name=None, last_name=None, email=None):
        self.__driver_get(
            'https://www.altmetric.com/products/free-tools/bookmarklet/')
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

    def update_results(self, list_citation_ids=None, overwrite='incomplete'):
        if self.dict_tabs_args['twitter']:
            _tab = 'twitter'
            print('Updating results of: %s' % _tab)
            # Get .txt files
            _list_fnames = [_fname for _fname in listdir(
                './altmetricit/%s' % _tab) if _fname.endswith('.txt')] if list_citation_ids == None else list(map(lambda _citation_id: _citation_id+'.txt', list_citation_ids))
            _num_files = len(_list_fnames)
            print('# of result files:', _num_files)

            # self.dict_failed['twitter'] = list()
            _num_failed = 0

            for i, _fname in enumerate(_list_fnames):  # 65248654.txt
                print('%d out of %d result files' % (i+1, _num_files))
                with open('./altmetricit/%s/%s' % (_tab, _fname)) as fp:
                    _dict_result = json.load(fp)
                _success = self.__update_twitter_from_citation_id(
                    _dict_result['citation_id'], overwrite=overwrite)
                if not _success:
                    _num_failed += 1
            print('Update completed: Twitter\t# of result files: %d\t# of failed jobs: %d' % (
                _num_files, _num_failed))

    def crawl_altmetric_from_papers(self, overwrite='incomplete'):
        self.db_handler.sql_handler.select(self.table, ('idx', 'urls', 'altmetric_id'))
        # self.db_handler.sql_handler.select(self.table, ('idx', 'urls', 'altmetric_id')).order_by(dict_columns_orders={'idx': 'desc'})
        _records = self.db_handler.execute().fetchall()
        # _records = _records[:2]
        _num_papers = len(_records)
        print('# of paper urls:', _num_papers)

        for i, _row in enumerate(_records):
            print('Processing: %d out of %d papers' % (i+1, _num_papers))
            _str_urls = _row[1]
            _url_abs = self.regex_abs.findall(_str_urls)[0]

            # Twitter
            if self.dict_tabs_args['twitter']:
                print('Crawling: Twitter')
                self.dict_failed['twitter'] = list()
                _success = self.__update_twitter_from_url(
                    self.table, _row[0], _url_abs, overwrite=overwrite)
                if not _success:
                    print('--Job failed: %s' % self.msg_error)
                    self.dict_failed['twitter'].append({
                        'idx': _row[0],
                        'url': _url_abs,
                        'msg_error': self.msg_error
                    })
                else:
                    print('--Job successful.')
                print('\n')

        print('Crawling completed: Twitter\t# of papers: %d\t# of failed jobs: %d' % (
            _num_papers, len(self.dict_failed['twitter'])))
        _fp = './altmetricit/log_fail_%s.txt' % datetime.now().strftime('%Y%m%d_%H%M%S')
        with open(_fp, 'w+') as f:
            json.dump(self.dict_failed, f)
            print('Log dumped: %s' % _fp)

    def __update_twitter_from_url(self, table, idx_paper, url, overwrite='incomplete'):
        # Check if citation_id already exists on the table
        self.db_handler.sql_handler.select(
            table, 'altmetric_id').where('idx', idx_paper)
        _result = self.db_handler.execute().fetchall()
        _citation_id = _result[0][0]
        if _citation_id == None:
            # Get div.wrapper
            _div_wrapper = self.__get_div_wrapper_from_url(url)
            if _div_wrapper == False:
                return False

            # Get citation id
            _citation_id = self.__get_altmetric_citation_id(_div_wrapper)
            if _citation_id == False:  # No altmetric given to paper
                print('\tNo altmetric score given.')
                return False

            # Update table set altmetric_id
            self.db_handler.sql_handler.update(table, dict_columns_values={
                                               'altmetric_id': _citation_id}).where('idx', idx_paper)
            self.db_handler.execute()
            print('\tCitation_id set on DB.')

        return self.__update_twitter_from_citation_id(_citation_id, overwrite=overwrite)

    # def update_papers_set_altmetric_id(self, args, tup_idx_urls):
    #     # Fix required
    #     _str_urls = tup_idx_urls[1]
    #     _url_abs = self.regex_abs.findall(_str_urls)[0]
    #     _citation_id = self.__get_altmetric_id(_url_abs)
    #     if _citation_id == False:
    #         return
    #     self.db_handler.sql_handler.reset()
    #     self.db_handler.sql_handler.update(self.table, dict_columns_values={
    #         'altmetric_id': _citation_id}).where('idx', int(field[0]))
    #     # sql = self.db_handler.sql_handler.get_sql()
    #     # self.db_handler.mycursor.execute(sql)
    #     # self.db_handler.conn.commit()
    #     self.db_handler.execute()

    #     self.db_handler.sql_handler.select(self.table, ['idx', 'urls'])
    #     # sql = self.db_handler.sql_handler.get_sql()
    #     # self.db_handler.mycursor.execute(sql)
    #     # list_urls = self.db_handler.mycursor.fetchall()
    #     list_urls = self.db_handler.execute().fetchall()
    #     # list_urls = list_urls[:2]
    #     num_papers = len(list_urls)
    #     print('# of paper urls:', num_papers)

    #     self.dict_failed['twitter'] = list()

    #     for i, field in enumerate(list_urls):
    #         print('Processing: %d out of %d papers' % (i+1, num_papers))
    #         _str_urls = field[1]
    #         _url_abs = self.regex_abs.findall(_str_urls)[0]
    #         _citation_id = self.__get_altmetric_id(_url_abs)
    #         if _citation_id == False:
    #             continue
    #         self.db_handler.sql_handler.reset()
    #         self.db_handler.sql_handler.update(self.table, dict_columns_values={
    #             'altmetric_id': _citation_id}).where('idx', int(field[0]))
    #         # sql = self.db_handler.sql_handler.get_sql()
    #         # self.db_handler.mycursor.execute(sql)
    #         # self.db_handler.conn.commit()
    #         self.db_handler.execute()

    #     self.driver.close()

    def __get_altmetric_id(self, url):
        # Get div.wrapper
        _div_wrapper = self.__get_div_wrapper_from_url(url)
        if _div_wrapper == False:
            return False

        # Get citation id
        _citation_id = self.__get_altmetric_citation_id(_div_wrapper)
        if _citation_id == False:  # No altmetric given to paper
            return False

        return _citation_id

    def __update_twitter_from_citation_id(self, citation_id, overwrite='incomplete'):
        # If file already exists
        if not self.__determine_go_or_pass(citation_id, overwrite=overwrite):
            return True

        # Crawl on twitter
        _dict_tweets = self.__get_dict_tweets_from_id(citation_id)

        # Save results
        self.__save_results(_dict_tweets)

        # self.__load_results('twitter', _citation_id)
        if _dict_tweets['completed'] == '0':
            return False

        return True

    def __determine_go_or_pass(self, citation_id, overwrite):
        try:
            print('\tChecking file exists: ./altmetricit/twitter/%s.txt' %
                  citation_id)
            f = open('./altmetricit/twitter/%s.txt' % citation_id, 'r')
        except IOError:  # No such file or directory
            print('\tNo such file or directory.')
            return True
        else:
            print('\tFile found. Overwrite policy:', overwrite)
            if overwrite == True:
                f.close()
                return True
            elif overwrite == 'incomplete':
                _dict_tweets = json.load(f)
                f.close()
                if _dict_tweets['completed'] == '1':  # Completed already.
                    print('\tCrawling completed already.')
                    return False
                return True
            elif overwrite == False:  # Never overwrite
                f.close()
                return False

    # def get_nums_twitter(self, dict_tweets):
        # _num_tweets = len(dict_tweets['twitter'])
        # _num_followers = 0
        # for _article in dict_tweets['twitter']:
            # _num_followers += _article['followers']
        # return (_num_tweets, _num_followers)

    def __save_results(self, results):
        # {'citation_id': str, 'tab': str, 'twitter': [{...}, ...]}
        print(results)
        with open('./altmetricit/%s/%s.txt' % (results['tab'], results['citation_id']), 'w+') as f:
            # with open(osp.join('altmetric', results['tab'], results['citation_id'] + '.txt'), 'w+') as f:
            json.dump(results, f)

    def __load_results(self, tab, citation_id):
        with open('./altmetricit/%s/%s.txt' % (tab, citation_id), 'r') as f:
            return json.load(f)

    def __get_dict_tweets_from_id(self, citation_id):
        # Access authorized page
        self.__driver_get(
            'https://www.altmetric.com/details.php?citation_id=%s&src=bookmarklet' % citation_id)

        # Iterate over page
        _url_twitter = self.__get_url_tab_altmetric(citation_id, 'twitter')
        _page = 0
        _dict_tweets = dict()
        _dict_tweets['citation_id'] = citation_id
        _dict_tweets['tab'] = 'twitter'
        _dict_tweets['twitter'] = dict()
        _dict_tweets['completed'] = '0'
        _dict_tweets['queriedAt'] = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S')
        while True:
            _page += 1
            print('\tProcessing page: %d' % _page)
            _url_page = _url_twitter + '/page:%d' % _page
            self.__driver_get(_url_page)
            # limited-access-warning
            try:
                self.driver.find_element_by_class_name(
                    'limited-access-warning')
            except:  # NoSuchElementException
                pass
            else:
                print('\t.limited-access-warning found.')
                self.msg_error = 'Limited access warning.'
                return _dict_tweets

            if self.driver.current_url != _url_page:
                # Invalid pagination
                print('\tPage %d not exist.' % _page)
                break

            # Crawl on the page
            _dict_new_tweets = self.__crawl_tweets_from_current_page()
            if _dict_new_tweets == False:
                print('\t.post-list not found.')
                self.msg_error = 'Failed to find .post-list.'
                return _dict_tweets

            _dict_tweets['twitter'].update(_dict_new_tweets)

        _dict_tweets['completed'] = '1'
        return _dict_tweets

    def __crawl_tweets_from_current_page(self):
        _dict_tweet = dict()
        _section_post_list = self.__find_recursive(
            self.driver, 'post-list', 'class', max_times_find=self.max_times_find)
        if _section_post_list == False:
            return False
        _articles = _section_post_list.find_elements_by_tag_name('article')
        for _article in _articles:
            _author = _article.find_element_by_class_name(
                'author').find_element_by_class_name('handle').text
            _followers = _article.find_element_by_class_name(
                'follower_count').find_element_by_tag_name('span').get_property('innerText')
            _content_summary = _article.find_element_by_class_name(
                'summary').text
            _datetime = datetime.strptime(_article.find_element_by_tag_name('time').get_attribute(
                'datetime'), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
            _tweet_id = self.regex_tweet_id.findall(
                _article.find_element_by_class_name('retweet').get_attribute('href'))[0].split('=')[1]
            _dict_tweet[_tweet_id] = {
                'author': _author,
                'followers': _followers,
                'content_summary': _content_summary,
                'datetime': _datetime
            }
            # {'str': {'author': str','followers': str', 'content_summary': str, 'datetime': str'}}

        return _dict_tweet

    def __get_url_tab_altmetric(self, citation_id, tab):
        if tab not in self.list_tabs_altmetric:
            raise ValueError('Tab name not understood: %s' % tab)
        return 'https://www.altmetric.com/details/%s/%s' % (citation_id, tab)

    def __get_altmetric_citation_id(self, div_wrapper):
        # if not self.__altmetric_exists(div_wrapper):
        # return False

        # Find: #altmetric-wrapper div.article-details a
        _href_details = div_wrapper.find_element_by_class_name(
            'article-details').find_element_by_tag_name('a').get_attribute('href')
        _list_sentences = self.regex_citation_id.findall(_href_details)
        return self.regex_citation_id.findall(_href_details)[0].split('=')[1] if _list_sentences else False

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

    def __get_div_wrapper_from_url(self, url):
        _url_parse = urlparse(url)  # https://arxiv.org/abs/1810.04805
        url = _url_parse[0] + '://export.' + _url_parse[1] + \
            _url_parse[2]  # https://export.arxiv.org/abs/1810.04805
        print('\turl:', url)
        self.__driver_get(url)
        self.__driver_execute_script(self.script_altmetricit)

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

    def __altmetric_exists(self, div_wrapper):
        # Case2: No altmetric
        # _article_details = self.__find_recursive(
        # div_wrapper, 'article-details', 'class', max_times_find=self.max_times_find)
        # return _article_details != False

        return True  # .article_details always exists

    def __driver_get(self, url):
        # url must be understood by altmetricit
        self.driver.get(url)
        return self.driver.execute_script('return document.location.protocol != "chrome-error:"')

    def __driver_execute_script(self, script):
        self.driver.execute_script(script)


# if __name__ == '__main__':
#     altmetric_it = AltmetricIt()
#     altmetric_it.update_papers_set_altmetric_id()
