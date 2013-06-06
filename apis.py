#! /bin.env python
# -*- coding: utf-8 -*-

import datetime
import urllib

import database as db
import views

from django.http import HttpResponse
from django.utils import simplejson as json

CONTENT_TYPE_JSON = 'application/json; charset=utf-8'
MAX_LIMIT = 1000
ONE_DAY = datetime.timedelta(days=1)
DATE_FORMAT = '%Y-%m-%d'

def json_response(res):
    return HttpResponse(json.dumps(res, ensure_ascii=False, encoding='utf-8'),
                        content_type=CONTENT_TYPE_JSON)

@views.benchmark
def topics(request):
    return json_response(db.list_topics())

@views.benchmark
def sources(request):
    return json_response(db.list_sources())

def _parse_params(request):
    start = views._get(request, 'start')
    end = views._get(request, 'end')
    limit = views._get(request, 'limit')
    if start:
        start = datetime.datetime.strptime(start, DATE_FORMAT)
    if end:
        end = datetime.datetime.strptime(end, DATE_FORMAT) + ONE_DAY
    if limit:
        limit = int(limit)
        limit = limit if limit < MAX_LIMIT else MAX_LIMIT
    else:
        limit = MAX_LIMIT
    return start, end, limit

@views.benchmark
def topic(request, topic=''):
    start, end, limit = _parse_params(request)
    ret = db.list_articles_by_topic(topic, start=start, end=end, limit=limit)
    return json_response(ret)

@views.benchmark
def source(request, source=''):
    start, end, limit = _parse_params(request)
    ret = db.list_articles_by_source(source, start=start, end=end, limit=limit)
    return json_response(ret)

@views.benchmark
def article(request, aid=''):
    if not aid:
        #XXX 404
        return HttpResponseRedirect('/')
    aid = int(aid)
    article = db.get_article(aid)
    if not article:
        #XXX 404
        return HttpResponseRedirect('/')
    article['source'] = db.get_source(article['source'])
    article['topics'] = db.get_topics_by_article(aid)
    article['url'] = urllib.unquote(article['url'])
    article['source']['url'] = urllib.unquote(article['source']['url'])
    #if article['cached'] and len(article['cached']) > 100:
    #    article['cached'] = article['cached'][:100] + '...'
    return json_response(article)
