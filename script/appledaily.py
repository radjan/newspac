from bs4 import BeautifulSoup
import urllib2
import re
from datetime import datetime
import rss_base
# Sat, 01 Dec 2012 07:00:00 +0800
process_date = lambda x: x[5:-6]
DATE_FORMAT =  '%d %b %Y %H:%M:%S'

class Handler(rss_base.RssBaseHandler):
    def fetch_text(self, url):
        try:
            u = urllib2.urlopen(url)
            url = u.geturl()

            # <option value="balabala/value"selected>
            # XXX This kind of data confuses beautiful soup
            full_text = u.read()
            full_text = full_text.replace("\"selected", "\" selected")

            bs = BeautifulSoup(full_text)
            canonical_url = self.get_canonical_url(bs)
            url = canonical_url if canonical_url else url
            return url, bs.find(attrs={'class': re.compile('articulum')}).get_text()
        except Exception, e:
            #raise
            return url, None

    def _str_to_ts(self, pubdate_str):
        ts = datetime.strptime(process_date(pubdate_str), DATE_FORMAT)
        ts = ts.replace(tzinfo=rss_base.UTC8())
        return ts.astimezone(rss_base.UTC())

