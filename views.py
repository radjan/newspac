import urllib
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse

import database as db
import common
log = common.get_logger()

def index(request):
    topics = db.homepage_topics()
    topics = _add_level(topics)
    return render_to_response('index.html',
                              dict(topics=topics))

def _add_level(datalist):
    def value_fn(item):
        return item['amount']
    def set_level(item, lv):
        item['level'] = lv
    cand_list = [value_fn(item) for item in datalist]
    cand_list = sorted(cand_list)
    log.debug(cand_list)
    idxs = _get_indexes(cand_list)
    log.debug(idxs)
    for item in datalist:
        is_set = False
        for i in range(len(idxs)):
            if value_fn(item) <= idxs[i]:
                set_level(item, i + 1)
                is_set = True
                break
        if not is_set:
            set_level(item, len(idxs) + 1)
    return datalist

def _get_indexes(clist):
    l = len(clist)
    seg_10 = int(l * 0.1)
    seg_35 = int(l * 0.35)
    return [clist[seg_10], clist[seg_35], clist[-seg_35], clist[-seg_10]]

def topic(request):
    topics_str = _get(request, 'topic')
    if not topics_str:
        return HttpResponseRedirect('/')

    limit = _get(request, 'limit')
    if limit is None:
        limit = 100
    elif limit == 'all':
        limit = 0
    else:
        try:
            limit = int(limit)
        except Exception:
            limit = 100

    def _process_row(a):
        a['created_date'] = a['created'][:10] #.timepstr('%Y-%M-%D')
        a['url'] = urllib.unquote(a['url'])
        a['source_url'] = urllib.unquote(a['source_url'])
        return a
    topics = topics_str.split(common.TOPIC_SEPARATOR)
    if len(topics) == 1:
        articles = db.list_articles_by_topic(topics[0], limit)
    else:
        articles = db.list_articles_by_topics(topics, limit)
    articles = [_process_row(a) for a in articles]
    limit = limit if len(articles) == limit else 0

    related_topics = db.get_related_topics(topics, limit=10)
    for item in related_topics:
        item['q'] = topics_str + common.TOPIC_SEPARATOR + item['title']

    return render_to_response('topic.html',
                              dict(topics=topics,
                                   topic=topics_str,
                                   highlight_pattern='|'.join(topics) if len(topics) > 1 else topics[0],
                                   articles=articles,
                                   limit=limit,
                                   related_topics=related_topics))

def article(request):
    aid = _get(request, 'id')
    if not aid:
        return HttpResponseRedirect('/')
    aid = int(aid)
    article = db.get_article(aid)
    if not article:
        return HttpResponseRedirect('/')
    article['source'] = db.get_source(article['source'])
    article['topics'] = db.get_topics_by_article(aid)
    article['url'] = urllib.unquote(article['url'])
    article['source']['url'] = urllib.unquote(article['source']['url'])
    return render_to_response('article.html', article)

def _get(r, key):
    return r.REQUEST[key] if key in r.REQUEST else None

