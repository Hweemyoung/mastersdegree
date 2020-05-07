from selenium import webdriver
from datetime import datetime
from time import sleep

import os.path as osp
import json
import re


class AltmetricIt:
    dict_drivers = {
        'chrome': webdriver.Chrome
    }
    list_tabs_altmetric = ['', 'news', 'blogs', 'twitter',
                           'wikipedia', 'google', 'reddit', 'video']
    script_altmetricit = 'javascript:((function(){var a;a=function(){var a,b,c,d,e;b=document,e=b.createElement("script"),a=b.body,d=b.location;try{if(!a)throw 0;c="d1bxh8uas1mnw7.cloudfront.net";if(typeof runInject!="function")return e.setAttribute("src",""+d.protocol+"//"+c+"/assets/content.js?cb="+Date.now()),e.setAttribute("type","text/javascript"),e.setAttribute("onload","runInject()"),a.appendChild(e)}catch(f){return console.log(f),alert("Please wait until the page has loaded.")}},a(),void 0})).call(this);'
    regex_citation_id = re.compile(r'citation_id=\d{6,10}')

    def __init__(self,
                 driver='chrome',
                 p_driver='./chromedriver',
                 max_times_find=2,
                 sec_sleep=1.0):
        self.driver = self.dict_drivers[driver](p_driver)
        self.max_times_find = max_times_find
        self.sec_sleep = sec_sleep

    def get_nums_twitter(self, dict_tweets):
        _num_tweets = len(dict_tweets['twitter'])
        _num_followers = 0
        for _article in dict_tweets['twitter']:
            _num_followers += _article['followers']
        return (_num_tweets, _num_followers)

    def save_results(self, results):
        # {'citation_id': str, 'tab': str, 'twitter': [{...}, ...]}
        with open(osp.join('altmetric', results['tab'], results['citation_id'] + '.txt'), 'w') as f:
            json.dump(results, f)

    def get_tweets_from_id(self, citation_id):
        # Iterate over page
        _url_twitter = self.get_url_tab_altmetric(citation_id, 'twitter')
        _page = 0
        _dict_tweets = dict()
        _dict_tweets['citation_id'] = citation_id
        _dict_tweets['tab'] = 'twitter'
        _dict_tweets['twitter'] = list()
        while True:
            _page += 1
            print('\tProcessing page: %d' % _page)
            _url_page = _url_twitter + '/page:%d' % _page
            self.driver_get(_url_page)
            # limited-access-warning
            try:
                self.driver.find_element_by_class_name(
                    'limited-access-warning')
            except:
                # NoSuchElementException
                pass
            else:
                print('\t.limited-access-warning found.')
                return

            if self.driver.current_url != _url_page:
                # Invalid pagination
                print('\tPage %d not exist.' % _page)
                break
            # Crawl on the page
            _dict_tweets['twitter'] += self.crawl_tweets_from_current_page()

        return _dict_tweets

    def crawl_tweets_from_current_page(self):
        _list_tweets = list()
        _section_post_list = self.driver.find_element_by_class_name(
            'post-list')
        _articles = _section_post_list.find_elements_by_tag_name('article')
        for _article in _articles:
            _author = _article.find_element_by_class_name(
                'author').find_element_by_class_name('handle').text
            _followers = _article.find_element_by_class_name(
                'follower_count').find_element_by_tag_name('span').text
            _content_summary = _article.find_element_by_class_name('summary').text
            _datetime = datetime.strptime(_article.find_element_by_tag_name('time').get_attribute(
                'datetime'), '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
            _list_tweets.append({
                'author': _author,
                'followers': _followers,
                'content_summary': _content_summary,
                'datetime': _datetime
            })
            # {'author': str','followers': str', 'content_summary': str, 'datetime': str'}

        return _list_tweets

    def get_tab_of_altmetric(self, citation_id, tab='twitter'):
        _url_tab = self.get_url_tab_altmetric(citation_id, tab)
        self.driver_get(_url_tab)

    def get_url_tab_altmetric(self, citation_id, tab):
        if tab not in self.list_tabs_altmetric:
            raise ValueError('Tab name not understood: %s' % tab)
        return 'https://www.altmetric.com/details/%s/%s' % (citation_id, tab)

    def get_altmetric_citation_id(self, div_wrapper):
        # Find: #altmetric-wrapper div.article-details a
        _href_details = div_wrapper.find_element_by_class_name(
            'article-details').find_element_by_tag_name('a').get_attribute('href')
        return self.regex_citation_id.findall(_href_details)[0].split('=')[1]

    def get_div_wrapper_from_url(self, url):
        print('url:', url)
        self.driver_get(url)
        self.driver_execute_script(self.script_altmetricit)
        _times_find = 0
        while True:
            _times_find += 1
            try:
                print('\tFind: #altmetric-wrapper(%d th try)' % _times_find)
                _div_wrapper = self.driver.find_element_by_id(
                    'altmetric-wrapper')
            except:  # NoSuchElementException
                print('\t#altmetric-wrapper not found.')
                if _times_find < self.max_times_find:
                    print('Retrying...')
                    sleep(self.sec_sleep)
                    pass
                else:
                    print('Exceeded max_times_find. Go on to next job.')
                    return
            else:
                print('\t#altmetric-wrapper found.')
                break

        # Case1: error
        try:
            print('\tFind: .error')
            _div_wrapper.find_element_by_class_name('error')
        except:  # NoSuchElementException
            print('\t.error not found.')
            pass
        else:
            print('\t.error found. Go on to next job.')
            return

        # Case2: No altmetric
        try:
            print('\tFind: .article-details')
            _div_wrapper.find_element_by_class_name('article-details')
        except:  # NoSuchElementException
            print('\t.article-details found.')
            return _div_wrapper
        else:
            print('\t.article-details not found. Go on to next job')
            return

    def driver_get(self, url):
        # url must be understood by altmetricit
        self.driver.get(url)

    def driver_execute_script(self, script):
        self.driver.execute_script(script)


if __name__ == '__main__':
    altmetric_it = AltmetricIt()
    altmetric_it.get_div_wrapper_from_url('https://www.naver.com/')
