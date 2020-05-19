from db_handler import DBHandler
from preprocessor import Preprocessor
from datetime import datetime
from random import shuffle

import urllib.request
import re

from bs4 import BeautifulSoup


class DBPapersUploader(DBHandler):
    regex_abs = re.compile(r'https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
    regex_pdf = re.compile(r'https?://arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf')
    regex_http = re.compile(r'^http://')
    regex_https = re.compile(r'^https://')

    regex_date = re.compile(r'\d{1,2} \w{3} \d{4}')  # 3 Oct 2019

    num_crawled = 0
    num_inserted = 0
    num_existed = 0
    list_merged = list()

    db_handler = DBHandler()

    def upload_papers_from_videos(self, args):
        sql = "SELECT `idx`, `description` FROM videos WHERE description LIKE '%arxiv.org/abs/%' OR description LIKE '%arxiv.org/pdf/%';"
        # sql = "SELECT `idx`, `description` FROM videos WHERE idx=23;"
        self.db_handler.mycursor.execute(sql)
        results = self.db_handler.mycursor.fetchall()
        num_queried = len(results)
        print('# of queried videos:', num_queried)

        # Shuffle
        print('Before shuffle:', results[0])
        shuffle(results)
        print('After shuffle:', results[0])

        for i, row in enumerate(results):
            print('Processing:', i+1, 'out of', num_queried, 'videos')
            args.idx_video = row[0]
            regex_urls = re.compile(
                r'https?://arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf|https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
            list_urls = regex_urls.findall(row[1])
            num_urls = len(list_urls)
            print('# of found urls:', num_urls)
            self.num_crawled += num_urls

            for j, url in enumerate(list_urls):
                print('\n\tProcessing:', j+1, 'out of', num_urls, 'urls:', url)
                args.url = self.url_http_to_https(
                    self.url_pdf_to_abs(url))
                # Check if paper exists
                if not self.paper_exists(args):
                    items = self.__get_items(args)
                    print(items)
                    self.insert('papers', items)
                    self.num_inserted += 1

        print('\nDone')
        print('# of queried videos:', num_queried)
        print('# of crawled papers:', self.num_crawled)
        print('# of inserted papers:', self.num_inserted)
        print('# of existed papers:', self.num_existed)
        print('# of merge:', len(self.list_merged))
        print('Merged urls:', self.list_merged)

    def __update_papers_from_arxiv_list(self, args):
        _url = self.__get_urls(args, mode="arxiv_list")
        _html = urllib.request.urlopen(_url)
        _soup = BeautifulSoup(_html, 'html.parser')
        _html.close()

        _list_paths = self.__get_list_paths_from_arxiv_list(_soup)
        for i, _path in enumerate(_list_paths):
            _url = "https://arxiv.org" + _path
            # Get items from url

    def __get_list_paths_from_arxiv_list(self, soup):
        _div_dlpage = soup.find('div', {'id': 'dlpage'})
        _list_dts = _div_dlpage.find_all('dt')
        _list_paths = list(map(lambda _dt: _dt.find('span', {'class': 'list-identifier'}).find('a', {'title': 'Abstract'})['href'], _list_dts)) # ['/abs/1902.33284', ...]
        return _list_paths

    def __get_items(self, args):
        # args must include: idx_videos, url from videos
        # args["url"] could be either abs or pdf
        items = dict()
        items['urls'] = self.__get_urls(args, mode="arxiv_paper")
        items['idx_videos'] = args["idx_video"]
        items['queriedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # title, publishedAt, ...
        items.update(self.get_fields_from_arxiv(args["url"]))
        return items

    def get_fields_from_arxiv(self, url):
        # url could be either abs or pdf
        url = self.url_pdf_to_abs(url)
        html = urllib.request.urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')
        html.close()

        fields = dict()
        # Get title
        fields['title'] = self.get_title_from_arxiv_html(soup)  # str
        # Get authors
        fields['authors'] = self.get_authors_from_arxiv_html(soup)  # str
        # Get abstract
        fields['abstract'] = self.get_abstract_from_arxiv_html(soup)  # str
        # Get publishedAt
        fields['publishedAt'] = self.get_publishedAt_from_arxiv_html(
            soup)  # str
        # Get subjects
        fields.update(self.get_subjects_from_arxiv(soup))  # dict

        return fields

    def get_subjects_from_arxiv(self, soup):
        subjects = soup.find('div', {'class': 'subheader'})
        subjects = subjects.find('h1').find(text=True)
        subjects = str(subjects).split(' > ')
        cols = ['subject_1', 'subject_2', 'subject_3']
        return dict(zip(cols, subjects))

    def get_abstract_from_arxiv_html(self, soup):
        abstract = soup.find('blockquote', {'class': 'abstract'})
        abstract = abstract.find_all(text=True)
        # Filter texts
        abstract = [text for text in abstract if text not in (
            '\n', 'Abstract:')]
        # Remove \n
        abstract = map(lambda text: text.replace('\n', ' '), abstract)
        return '\n'.join(abstract)

    def get_authors_from_arxiv_html(self, soup):
        authors = soup.find('div', {'class': 'authors'})
        authors = authors.find_all(text=True)
        # Filter texts
        authors = [author for author in authors if author not in (
            'Authors:', ', ')]
        return ', '.join(authors)

    def get_title_from_arxiv_html(self, soup):
        # Get title
        heading = soup.find('h1', {'class': ['mathjax', 'title']})
        title = heading.findAll(text=True)[1]
        print('\ttitle:', title)
        return str(title)

    def get_publishedAt_from_arxiv_html(self, soup):
        # Get publishedAt
        div_dateline = soup.find('div', {'class': 'dateline'})
        published_date = self.regex_date.findall(str(div_dateline))[0]
        # 2019-10-03
        return datetime.strptime(published_date, '%d %b %Y').strftime('%Y-%m-%d')

    def __get_urls(self, args, mode="arxiv_paper"):
        if mode == "arxiv_paper":
            _urls = self.__get_arxiv_paper_urls(args["url"])
        elif mode == "arxiv_list":
            _urls = self.__get_arxiv_list_urls(args)
        return _urls

    def __get_arxiv_list_urls(self, args):
        _urls = tuple("https://arxiv.org/list/%s/%s%s?skip=0&show=5000" % (
            args["field"], args["YY"], args["MM"]))
        return _urls

    def __get_arxiv_paper_urls(self, url):
        url_abs = self.url_http_to_https(self.url_pdf_to_abs(url))
        url_pdf = self.url_http_to_https(self.url_abs_to_pdf(url))
        urls = '%s, %s' % (url_abs, url_pdf)
        print('\turls:', urls)
        return urls

    def paper_exists(self, args):
        # Determines by url
        sql = "SELECT `idx`, `idx_videos` FROM papers WHERE match(urls) against('\"%s\"' in boolean mode);" % args["url"]
        # Determines by title?
        # sql = "SELECT `idx` FROM papers WHERE match(urls) against('\"%s\"' in boolean mode);" % args["title"]
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        exists = len(result) != 0

        if len(result) > 0:
            self.num_existed += 1
            print('\tPaper already exists:', args["url"])

            if len(result) > 1:
                print('Multiple papers sharing same URL:', args["url"])
                args["rows"] = result
                result = self.merge_rows(args)

            args["idx_paper"] = result[0][0]
            self.idx_video_exists(args)
        elif len(result) == 0:
            print('\tPaper not exist:', args["url"])

        return exists

    def merge_rows(self, args):
        print('\tMerging rows:', args["rows"])
        target_idx_videos = list()
        deleted_idx = list()
        # Acquirer
        target_idx_videos.append(args["rows"][0][1])

        for row in args["rows"][1:]:
            deleted_idx.append(str(row[0]))
            target_idx_videos.append(row[1])

        target_idx_videos = ', '.join(target_idx_videos)
        deleted_idx = ', '.join(deleted_idx)

        sql = "UPDATE papers SET idx_videos='%s' WHERE idx=%s;" % (
            target_idx_videos, args["rows"][0][0])
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        self.db_handler.conn.commit()

        sql = "DELETE FROM papers WHERE idx in (%s);" % deleted_idx
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        self.db_handler.conn.commit()

        sql = "SELECT `idx`, `idx_videos` FROM papers WHERE match(urls) against('\"%s\"' in boolean mode);" % args["url"]
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        if len(result) != 1:
            raise Exception('Error occured while merging: %s merged into %d.' % (
                args["url"], len(result)))

        self.list_merged.append(args["url"])

        return result

    def idx_video_exists(self, args):
        # Determines by url
        sql = "SELECT 1 FROM papers WHERE (match(idx_videos) against('\"%s,\"' in boolean mode) OR match(idx_videos) against('\" %s\"' in boolean mode) OR idx_videos='%s') AND idx='%s';" % (
            args["idx_video"], args["idx_video"], args["idx_video"], args["idx_paper"])
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        exists = len(result) != 0
        if exists:
            print('\tidx_video already exists:', args["idx_video"])
        else:
            print('\tidx_video not exist:', args["idx_video"])
            self.update_idx_videos(args)
        return exists

    def update_idx_videos(self, args):
        sql = "SELECT `idx_videos` FROM papers WHERE `idx`=%s;" % args["idx_paper"]
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        old_idx_videos = result[0][0] if len(result) else ''
        print('\tUpdating idx_videos to:',
              '%s, %s' % (old_idx_videos, args["idx_video"]))
        sql = "UPDATE papers SET idx_videos='%s' WHERE idx='%s';" % (
            '%s, %s' % (old_idx_videos, args["idx_video"]), args["idx_paper"])
        self.db_handler.mycursor.execute(sql)
        self.db_handler.conn.commit()

    def url_http_to_https(self, url):
        # Convert only if url matches pdf
        if bool(self.regex_https.match(url)):
            # Pattern: https
            pass
        elif not bool(self.regex_http.match(url)):
            raise SyntaxError(
                'URL pattern not understood http nor https.')
        else:
            # Pattern: http
            url = 'https' + url[4:]
        return url

    def url_pdf_to_abs(self, url):
        # Convert only if url matches pdf
        if bool(self.regex_abs.match(url)):
            # Pattern: ABS
            pass
        elif not bool(self.regex_pdf.match(url)):
            raise SyntaxError(
                'URL pattern not understood as arXiv PDF.')
        else:
            # Pattern: PDF
            url = url[:-4].replace('pdf', 'abs')
        return url

    def url_abs_to_pdf(self, url):
        # Convert only if url matches abs
        if bool(self.regex_pdf.match(url)):
            # Pattern: ABS
            pass
        elif not bool(self.regex_abs.match(url)):
            raise SyntaxError(
                'URL pattern not understood as arXiv ABS.')
        else:
            url = url.replace('abs', 'pdf') + '.pdf'
        return url

    def get_missing_idx(self):
        sql = "SELECT a.idx+1 AS start, MIN(b.idx) - 1 AS end FROM papers AS a, papers AS b WHERE a.idx < b.idx GROUP BY a.idx HAVING start < MIN(b.idx);"
        self.db_handler.mycursor.execute(sql)
        results = self.db_handler.mycursor.fetchall()  # [(26, 26), (68, 72), ...]
        return results
