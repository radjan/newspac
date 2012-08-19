from xml.dom import minidom
import urllib2
from datetime import datetime

REPLACE = [('0L0S', 'http://www.'),
           ('0N', '.com'),
           ('0B', '.'),
           ('0C', '/'),
           ('0E', '-'),
           ('20A12', '2012'),]
START = '0L0S'
END = '/'

process_date = lambda x: x[5:-4]
DATE_FORMAT =  '%d %b %Y %H:%M:%S'

def convertUrl(oriurl):
    #http://libertytimes.feedsportal.com/c/33098/f/535583/s/206656e2/l/0L0Slibertytimes0N0Btw0C20A120Cnew0Cjun0C160Ctoday0Et30Bhtm/story01.htm 
    start_idx = oriurl.find(START)
    end_idx = oriurl.find(END, start_idx)
    u = oriurl[start_idx:end_idx]
    for ori, new in REPLACE:
        u = u.replace(ori, new)
    return u

def get_articles(feed_url, last=None):
    last = datetime.strptime(last, DATE_FORMAT) if last else datetime(1970, 1, 1)
    max_last = last
    articles = []
    f = urllib2.urlopen(feed_url)
    dom = minidom.parse(f)
    items = dom.getElementsByTagName('item')
    for item in items:
        link = getTextByTagName(item, 'link')
        title = getTextByTagName(item, 'title')
        pubDate = getTextByTagName(item, 'pubDate')
        link = convertUrl(link)
        pubDate = _str_to_ts(pubDate)
        if last and pubDate <= last:
            continue
        elif pubDate > max_last:
            max_last = pubDate
        articles.append(dict(url=link,
                             title=title,
                             url_date=pubDate,))
    return articles, max_last.strftime(DATE_FORMAT)

def _str_to_ts(pubdate_str):
    return datetime.strptime(process_date(pubdate_str), DATE_FORMAT)

def getTextByTagName(node, tagName):
    return getText(node.getElementsByTagName(tagName)[0])

def getText(node):
    text = ''
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            text += child.data
    return text

if __name__ == '__main__':
    import pprint
    #print convertUrl('http://libertytimes.feedsportal.com/c/33098/f/535583/s/206656e2/l/0L0Slibertytimes0N0Btw0C20A120Cnew0Cjun0C160Ctoday0Et30Bhtm/story01.htm')
    pprint.pprint(get_articles('http://www.libertytimes.com.tw/rss/fo.xml'))

