# -*- encoding: utf-8 -*-
import urllib2
import urllib
import database as db
from script import liberty_parse as lp
import time

def fix_0A(a):
    if '0A' in a['url']:
        print a['url']
        a['url'] = a['url'].replace('0A', '0')
        return True
    return False

def fetch_text(a):
    if a['cached']:
        return False
    time.sleep(0.2)
    txt = lp.fetch_text(urllib.unquote(a['url']))
    if txt:
        print a['title'], a['url']
        a['cached'] = txt
        return True
    return False


source = u'自由時報'
articles = db.list_articles_by_source(source, addition_cols=['cached'])
fixed = 0
for a in articles:
    if any((fix_0A(a), fetch_text(a))):
        #print 'fixed', a
        db.ensure_article_exists(a, overwrite=True)
        fixed += 1
print 'total: %s, fixed: %s' % (len(articles), fixed)
