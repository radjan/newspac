from bs4 import BeautifulSoup
import urllib2
import re
import rss_base

class Handler(rss_base.RssBaseHandler):
    def fetch_text(self, url):
        try:
            u = urllib2.urlopen(url)
            url = u.geturl()
            bs = BeautifulSoup(u)
            canonical_url = self.get_canonical_url(bs)
            url = canonical_url if canonical_url else url
            if 'iservice' in url:
                return url, bs.find(attrs={'id': re.compile('newsc'),
                                           'role': re.compile('article')}).get_text()
            else:
                return url, bs.find(attrs={'id': re.compile('newsContent')}).find_all('span')[1].get_text()
        except Exception, e:
            #raise
            return url, None
