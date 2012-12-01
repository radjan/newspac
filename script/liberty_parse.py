from bs4 import BeautifulSoup
import urllib2
import re

def fetch_text(url):
    try:
        u = urllib2.urlopen(url)
        url = u.geturl()
        bs = BeautifulSoup(u)
        if 'iservice' in url:
            return url, bs.find(attrs={'id': re.compile('newsc'),
                                  'role': re.compile('article')}).get_text()
        else:
            return url, bs.find(attrs={'id': re.compile('newsContent')}).find_all('span')[1].get_text()
    except Exception, e:
        #raise
        return url, None
