from db_uploader import DBUploader
from preprocessor import Preprocessor
from datetime import datetime

import urllib.request
import re

from bs4 import BeautifulSoup


class DBPapersUploader(DBUploader):
    regex_abs = re.compile(r'https?://arxiv.org/abs/\d{3,5}.\d{3,5}')
    regex_pdf = re.compile(r'https?://arxiv.org/pdf/\d{3,5}.\d{3,5}.pdf')
    regex_http = re.compile(r'^http://')
    regex_https = re.compile(r'^https://')

    num_existed = 0
    num_merged = 0

    def get_items(self, args):
        # args must include: idx_videos, url from videos
        # args.url could be either abs or pdf
        cols = ['title', 'urls', 'idx_videos']
        vals = list()
        vals.append(self.get_title_from_arxiv(args.url))
        vals.append(self.get_urls(args.url))
        vals.append(args.idx_video)
        items = dict()
        for col, val in zip(cols, vals):
            items[col] = val
        return items

    def url_http_to_https(self, url):
        # Convert only if url matches pdf
        if bool(self.regex_https.match(url)):
            # Pattern: https
            pass
        elif not bool(self.regex_http.match(url)):
            raise SyntaxError(
                'URL pattern not understood as http(s).')
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

    def get_title_from_arxiv(self, url):
        url = self.url_pdf_to_abs(url)
        html = urllib.request.urlopen(url)
        soup = BeautifulSoup(html, 'html.parser')
        html.close()
        heading = soup.find('h1', {'class': ['mathjax', 'title']})
        # print(heading)
        title = heading.findAll(text=True)[1]
        print('\ttitle:', title)
        return str(title)

    def get_urls(self, url):
        url_abs = self.url_http_to_https(self.url_pdf_to_abs(url))
        url_pdf = self.url_http_to_https(self.url_abs_to_pdf(url))
        urls = '%s, %s' % (url_abs, url_pdf)
        print('\turls:', urls)
        return urls

    def paper_exists(self, args):
        # Determines by url
        sql = "SELECT `idx`, `idx_videos` FROM papers WHERE match(urls) against('\"%s\"' in boolean mode);" % args.url
        # Determines by title?
        # sql = "SELECT `idx` FROM papers WHERE match(urls) against('\"%s\"' in boolean mode);" % args.title
        print('\tsql:', sql)
        self.mycursor.execute(sql)
        result = self.mycursor.fetchall()
        exists = len(result) != 0

        if len(result) > 0:
            self.num_existed += 1
            print('\tPaper already exists:', args.url)

            if len(result) > 1:
                print('Multiple papers sharing same URL:', args.url)
                args.rows = result
                result = self.merge_rows(args)

            args.idx_paper = result[0][0]
            self.idx_video_exists(args)
        elif len(result) == 0:
            print('\tPaper not exist:', args.url)

        return exists

    def merge_rows(self, args):
        print('\tMerging rows:', args.rows)
        target_idx_videos = list()
        deleted_idx = list()
        # Acquirer
        target_idx_videos.append(args.rows[0][1])

        for row in args.rows[1:]:
            deleted_idx.append(str(row[0]))
            target_idx_videos.append(row[1])

        target_idx_videos = ', '.join(target_idx_videos)
        deleted_idx = ', '.join(deleted_idx)

        sql = "UPDATE papers SET idx_videos='%s' WHERE idx=%s;" % (
            target_idx_videos, args.rows[0][0])
        print('\tsql:', sql)
        self.mycursor.execute(sql)
        self.conn.commit()

        sql = "DELETE FROM papers WHERE idx in (%s);" % deleted_idx
        print('\tsql:', sql)
        self.mycursor.execute(sql)
        self.conn.commit()

        sql = "SELECT `idx`, `idx_videos` FROM papers WHERE match(urls) against('\"%s\"' in boolean mode);" % args.url
        print('\tsql:', sql)
        self.mycursor.execute(sql)
        result = self.mycursor.fetchall()
        if len(result) != 1:
            raise Exception('Error occured while merging: %s merged into %d.' % (
                args.url, len(result)))

        self.num_merged += 1

        return result

    def idx_video_exists(self, args):
        # Determines by url
        sql = "SELECT 1 FROM papers WHERE (match(idx_videos) against('\"%s,\"' in boolean mode) OR match(idx_videos) against('\" %s\"' in boolean mode) OR idx_videos='%s') AND idx='%s';" % (
            args.idx_video, args.idx_video, args.idx_video, args.idx_paper)
        print('\tsql:', sql)
        self.mycursor.execute(sql)
        result = self.mycursor.fetchall()
        exists = len(result) != 0
        if exists:
            print('\tidx_video already exists:', args.idx_video)
        else:
            print('\tidx_video not exist:', args.idx_video)
            self.update_idx_videos(args)
        return exists

    def update_idx_videos(self, args):
        sql = "SELECT `idx_videos` FROM papers WHERE `idx`=%s;" % args.idx_paper
        self.mycursor.execute(sql)
        result = self.mycursor.fetchall()
        old_idx_videos = result[0][0] if len(result) else ''
        print('\tUpdating idx_videos to:',
              '%s, %s' % (old_idx_videos, args.idx_video))
        sql = "UPDATE papers SET idx_videos='%s' WHERE idx='%s';" % (
            '%s, %s' % (old_idx_videos, args.idx_video), args.idx_paper)
        self.mycursor.execute(sql)
        self.conn.commit()
