# -*- encoding: utf-8 -*-
import urllib2
import database as db
from script import liberty_parse as lp
import time

def fix_0A(a):
    if '0A' in a['url']:
        print a['url']
        a['url'] = a['url'].replace('0A', '0')
        fetch_text(a)
        return True
    return False

def fetch_text(a):
    time.sleep(0.2)
    txt = lp.fetch_text(a['url'])
    if txt:
        print a['title'], a['url']
        a['cached'] = txt
        return True
    return False

source = u'自由時報'
articles = db.list_articles_by_source(source)
for a in articles:
    if fix_0A(a):
        #print 'fixed', a
        db.ensure_article_exists(a, overwrite=True)
