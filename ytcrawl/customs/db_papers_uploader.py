from db_handler import DBHandler
from preprocessor import Preprocessor
from datetime import datetime
from random import shuffle

import urllib.request
import re

from bs4 import BeautifulSoup


class DBPapersUploader:
    regex_abs = re.compile(r'https?://(export.)?arxiv.org/abs/\d{3,5}.\d{3,5}')
    regex_pdf = re.compile(r'https?://(export.)?arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf')
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
                if not self.__paper_exists(args):
                    items = self.__get_items(args)
                    print(items)
                    self.db_handler.insert('papers', items)
                    self.num_inserted += 1

        print('\nDone')
        print('# of queried videos:', num_queried)
        print('# of crawled papers:', self.num_crawled)
        print('# of inserted papers:', self.num_inserted)
        print('# of existed papers:', self.num_existed)
        print('# of merge:', len(self.list_merged))
        print('Merged urls:', self.list_merged)

    def update_papers_from_arxiv_list(self, args, overwrite=False):
        # Required: args["table","subject", "YY", "MM"]
        print('Update papers from arXiv list:\tSubject: %s\tYY: %s\tMM: %s' %
              (args['subject'], args['YY'], args['MM']))
        _url = self.__get_urls(args, mode="arxiv_list", export=True)
        print('url:', _url)
        _html = urllib.request.urlopen(_url)
        _soup = BeautifulSoup(_html, 'html.parser')
        _html.close()

        _list_paths = self.__get_list_paths_from_arxiv_list(_soup)
        _num_paths = len(_list_paths)
        _num_inserted = 0
        print('# of papers: %d' % _num_paths)

        for i, _path in enumerate(_list_paths):
            # Additional requirements: args['url]
            print('Processing %d out of %d papers...' % (i+1, _num_paths))
            args['path'] = _path
            args['url'] = self.__get_arxiv_domain(export=True) + _path

            # Get _dict_fields
            if not self.__paper_exists(args):
                print('\tPaper not found. Crawling...')
                # Get fields from args
                _dict_fields = self.__get_fields(args)
                _num_inserted += 1
            else:
                print('\tPaper already exists. Overwrite policy:', overwrite)
                if overwrite:
                    _dict_fields = self.__get_fields(args)
                    _num_inserted += 1
                else:
                    _dict_fields = None

            if _dict_fields == None:
                continue
            self.db_handler.sql_handler.insert(
                args['table'], dict_columns_values=_dict_fields)
            self.db_handler.execute()

        print('\nDone')
        print('# of queried papers:', _num_paths)
        print('# of inserted papers:', _num_inserted)
        print('# of passed papers:', _num_paths - _num_inserted)
    
    def __get_arxiv_domain(self, export=True):
        return "https://export.arxiv.org" if export else "https://arxiv.org"

    def __get_fields(self, args):
        print('\tGet fields from url: %s' % args['url'])
        _dict_fields = dict()
        _dict_fields['urls'] = self.__get_urls(args, mode="arxiv_paper", export=False)
        _dict_fields['idx_videos'] = self.__get_idx_videos(args)
        _dict_fields['queriedAt'] = datetime.now().strftime('%Y-%m-%d %X')
        _dict_fields.update(self.__get_fields_from_arxiv(args['url']))
        return _dict_fields

    def __get_idx_videos(self, args):
        return None if 'idx_videos' not in args.keys() else args['idx_videos']

    def __get_list_paths_from_arxiv_list(self, soup):
        _div_dlpage = soup.find('div', {'id': 'dlpage'})
        _list_dts = _div_dlpage.find_all('dt')
        _list_paths = list(map(lambda _dt: _dt.find('span', {'class': 'list-identifier'}).find(
            'a', {'title': 'Abstract'})['href'], _list_dts))  # ['/abs/1902.33284', ...]
        return _list_paths

    def __get_items(self, args):
        # args must include: idx_videos, url from videos
        # args["url"] could be either abs or pdf
        items = dict()
        items['urls'] = self.__get_urls(args, mode="arxiv_paper")
        items['idx_videos'] = args["idx_video"]
        items['queriedAt'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # title, publishedAt, ...
        items.update(self.__get_fields_from_arxiv(args["url"]))
        return items

    def __get_fields_from_arxiv(self, url):
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
        # authors = authors.find_all(text=True)
        # Filter texts
        # authors = [author for author in authors if author not in ('Authors:', ', ')]
        authors = tuple(map(lambda a: a.findAll(text=True)[0], authors.findAll('a'))) # export
        return ', '.join(authors)

    def get_title_from_arxiv_html(self, soup):
        # Get title
        heading = soup.find('h1', {'class': ['mathjax', 'title']})
        # title = heading.findAll(text=True)[1]
        title = heading.findAll(text=True)[1].replace('\n', '') # export
        # print('\ttitle:', title)
        return title

    def get_publishedAt_from_arxiv_html(self, soup):
        # Get publishedAt
        div_dateline = soup.find('div', {'class': 'dateline'})
        published_date = self.regex_date.findall(str(div_dateline))[0]
        # 2019-10-03
        return datetime.strptime(published_date, '%d %b %Y').strftime('%Y-%m-%d')

    def __get_urls(self, args, mode="arxiv_paper", export=True):
        if mode == "arxiv_paper":
            _urls = self.__get_arxiv_paper_urls(args["path"], export=export)
        elif mode == "arxiv_list":
            _urls = self.__get_arxiv_list_urls(
                args["subject"], args["YY"], args["MM"], export=export)
        return _urls

    def __get_arxiv_list_urls(self, field, YY, MM, export=True):
        _path = "/list/%s/%s%s?skip=0&show=5000" % (
            field, YY, MM)
        return self.__get_arxiv_domain(export) + _path

    def __get_arxiv_paper_urls(self, path, export=False):
        url = self.__get_arxiv_domain(export=export) + path
        url_abs = self.url_http_to_https(self.url_pdf_to_abs(url))
        url_pdf = self.url_http_to_https(self.url_abs_to_pdf(url))
        urls = '%s, %s' % (url_abs, url_pdf)
        # print('\turls:', urls)
        return urls

    def __paper_exists(self, args):
        # Determines by url
        sql = "SELECT `idx`, `idx_videos` FROM %s WHERE match(urls) against('\"%s\"' in boolean mode);" %(args['table'], self.__get_arxiv_domain(export=False) + args['path'])
        # sql = "SELECT `idx` FROM %s WHERE match(urls) against('\"%s\"' in boolean mode);" % (args['table'], args["title"])
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        exists = len(result) != 0

        if len(result) > 0:
            self.num_existed += 1
            print('\tPaper already exists:', self.__get_arxiv_domain(export=False) + args['path'])

            if len(result) > 1:
                print('Multiple papers sharing same URL:', args["url"])
                raise ValueError('\nPapers Collision')
                args["rows"] = result
                result = self.merge_rows(args)

            args["idx_paper"] = result[0][0]
            if "idx_video" in args:
                self.idx_video_exists(args)

        else:  # len(result) == 0
            print('\tPaper not exist:', self.__get_arxiv_domain(export=False) + args['path'])

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

        sql = "UPDATE %s SET idx_videos='%s' WHERE idx=%s;" % (
            args['table'],target_idx_videos, args["rows"][0][0])
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        self.db_handler.conn.commit()

        sql = "DELETE FROM %s WHERE idx in (%s);" % (args['table'], deleted_idx)
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        self.db_handler.conn.commit()

        sql = "SELECT `idx`, `idx_videos` FROM %s WHERE match(urls) against('\"%s\"' in boolean mode);" % (args['table'], args[
            "url"])
        print('\tsql:', sql)
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        if len(result) != 1:
            raise Exception('Error occured while merging: %s merged into %d.' % (
                args["url"], len(result)))

        self.list_merged.append(args["url"])

        return result

    def idx_video_exists(self, args):
        if "idx_video" not in args:
            return False
        # Determines by url
        sql = "SELECT 1 FROM %s WHERE (match(idx_videos) against('\"%s,\"' in boolean mode) OR match(idx_videos) against('\" %s\"' in boolean mode) OR idx_videos='%s') AND idx='%s';" % (
            args['table'], args["idx_video"], args["idx_video"], args["idx_video"], args["idx_paper"])
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
        sql = "SELECT `idx_videos` FROM %s WHERE `idx`=%s;" % (args['table'], args["idx_paper"])
        self.db_handler.mycursor.execute(sql)
        result = self.db_handler.mycursor.fetchall()
        old_idx_videos = result[0][0] if len(result) else ''
        print('\tUpdating idx_videos to:',
              '%s, %s' % (old_idx_videos, args["idx_video"]))
        sql = "UPDATE %s SET idx_videos='%s' WHERE idx='%s';" % (args['table'],
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
        sql = "SELECT a.idx+1 AS start, MIN(b.idx) - 1 AS end FROM %s AS a, %s AS b WHERE a.idx < b.idx GROUP BY a.idx HAVING start < MIN(b.idx);"%(args['table'],args['table'])
        self.db_handler.mycursor.execute(sql)
        # [(26, 26), (68, 72), ...]
        results = self.db_handler.mycursor.fetchall()
        return results


if __name__ == "__main__":
    db_papers_uploader = DBPapersUploader()
    # Required: args["table","subject", "YY", "MM", "url"]
    args = {
        'table': 'temp_papers',
        'subject': 'cs.LG',
        'YY': '19'
    }
    # for MM in ['01', '02', '03']:
    for MM in ['01']:
        args['MM'] = MM
        print(args)
        db_papers_uploader.update_papers_from_arxiv_list(args)
