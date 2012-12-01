# -*- encoding: utf-8 -*-
import simplejson as json
import database as db
db.THREAD_LOCAL = True
from importlib import import_module

def _feed_dict(feed_url, source, handler, catalog=None):
    return dict(feed_url=feed_url,
                source=source,
                handler=handler,
                catalog=catalog,
                last=None)

default_feeds = []
default_feeds.append(_feed_dict('http://www.libertytimes.com.tw/rss/fo.xml', u'自由時報', 'libertytimes', u'焦點'))
default_feeds.append(_feed_dict('http://www.libertytimes.com.tw/rss/p.xml', u'自由時報', 'libertytimes', u'政治'))
default_feeds.append(_feed_dict('http://www.libertytimes.com.tw/rss/e.xml', u'自由時報', 'libertytimes', u'財經'))
default_feeds.append(_feed_dict('http://rss.chinatimes.com/rss/focusing-u.rss', u'中時電子報', 'chinatimes', u'首頁焦點'))
default_feeds.append(_feed_dict('http://rss.chinatimes.com/rss/focus-u.rss', u'中時電子報', 'chinatimes', u'焦點'))
default_feeds.append(_feed_dict('http://rss.chinatimes.com/rss/Politic-u.rss', u'中時電子報', 'chinatimes', u'政治'))
default_feeds.append(_feed_dict('http://rss.chinatimes.com/rss/finance-u.rss', u'中時電子報', 'chinatimes', u'財經'))

def _load_state():
    with open('feed_state', 'r') as f:
        state = json.loads(f.readline())
    return state

def _save_state(states):
    state_str = json.dumps(states)
    with open('feed_state', 'w') as f:
        f.write(state_str)

def main():
    state = _load_state()
    for feed in default_feeds:
        if feed['feed_url'] not in state:
            state[feed['feed_url']] = feed

    for url, meta in state.items():
        print 'processing %s' % url
        handler = import_module(meta['handler']).Handler()
        new_articles, new_last = handler.get_articles(url, meta['last'])
        bad_count = 0
        for a in new_articles:
            a['source'] = meta['source']
            aid = db.ensure_article_exists(a, overwrite=True)
            if not a['cached']:
                bad_count += 1
            #print a
        print '  get %s articles, bad_count: %s' % (len(new_articles), bad_count)
        print new_last
        meta['last'] = new_last

    _save_state(state)

if __name__ == '__main__':
    main() 
