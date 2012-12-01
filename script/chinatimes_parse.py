from bs4 import BeautifulSoup
import urllib2
import re

def fetch_text(url):
    try:
        u = urllib2.urlopen(url)
        url = u.geturl()
        bs = BeautifulSoup(u)
        return url, bs.find(attrs={'id': re.compile('ctkeywordcontent')}).get_text()
    except Exception, e:
        #raise
        return url, None
